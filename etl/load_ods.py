# -*- coding: utf-8 -*-
"""阶段 1：ODS 导入（源 ZIP → meta.source_member / load_run / run_source / ods.trip_raw）。

规则依据 docs/design/source-to-target.md 与 docs/contracts/b-to-c-model-contract.md：
- 原始层不去重、不裁季度；13 列全部保留原文，空字段保留空字符串；
- CSV 记录号从表头 1 开始计数，多行字段仍算一条记录；
- 字段数不符属于运行错误：记录诊断、run 置 FAILED，不硬灌；
- 输入指纹只含真正的骑行 CSV（Mac 附属文件跳过），算法已对照 catalog.json 验证。

用法：
  python -X utf8 etl/load_ods.py --dry-run     # 只清点校验，不写库
  python -X utf8 etl/load_ods.py               # 正式导入，完成后打印 run_id
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone

from common import (ROOT, EtlError, Sqlcmd, batch_insert, sql_int, sql_nstr,
                    sql_str, validate_database)

MANIFEST_PATH = ROOT / 'inputs/public-source-snapshot.json'
RAW_DIR = ROOT / 'data/raw/citibike_jc/snapshot_20261113'

EXPECTED_HEADER = ['ride_id', 'rideable_type', 'started_at', 'ended_at',
                   'start_station_name', 'start_station_id', 'end_station_name',
                   'end_station_id', 'start_lat', 'start_lng', 'end_lat', 'end_lng',
                   'member_casual']

# 版本与范围：取值被 CK_meta_load_run_scope / CK_meta_load_run_versions 约束锁定，
# 必须完全一致（见 sql/ddl/020_tables.sql）；设计版本与加工代码版本分开登记。
DATA_SCOPE = 'JC_official_snapshot'
MODEL_VERSION = '1.0'              # 逻辑模型版本
METRIC_RULE_VERSION = 'A-1.0'      # 需求说明（指标口径）版本
PROCESSING_POLICY_VERSION = 'B1-1.0'  # 加工规则版本


def utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')


def iso_to_sql(iso_text):
    """ISO 8601（带 +00:00）→ datetime2 字面量文本。"""
    dt = datetime.fromisoformat(iso_text)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def code_revision():
    """当前 git 提交号；有未提交改动时加 -dirty。取不到时返回 unknown。"""
    try:
        rev = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return rev + ('-dirty' if dirty else '')
    except Exception:
        return 'unknown'


def input_set_sha256(trip_members):
    """输入指纹：[zip_sha256, member_path, csv_sha256] 三元组数组，
    按 ZIP 哈希（ASCII）与成员路径（UTF-8 字节）排序，UTF-8 无 BOM 紧凑 JSON。"""
    entries = sorted(([z, p, c] for z, p, c in trip_members),
                     key=lambda e: (e[0].encode('ascii'), e[1].encode('utf-8')))
    text = json.dumps(entries, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def scan_archives():
    """清点五个 ZIP：核对哈希与成员清单，解析 CSV 表头和行数。不写数据库。"""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    members = []          # 每个真正骑行 CSV 一项
    for archive in manifest['archives']:
        zip_path = RAW_DIR / Path(archive['path_from_repo']).name
        zip_sha = sha256_file(zip_path)
        if zip_sha != archive['sha256']:
            raise EtlError('input_mismatch', f"ZIP 哈希不符：{zip_path.name}")
        if zip_path.stat().st_size != archive['bytes']:
            raise EtlError('input_mismatch', f"ZIP 大小不符：{zip_path.name}")

        with zipfile.ZipFile(zip_path) as zf:
            inventory_ok = True
            trip_csvs = []
            for info in zf.infolist():
                declared = next((m for m in archive['all_members']
                                 if m['member_path'] == info.filename), None)
                if declared is None:
                    inventory_ok = False
                    continue
                data = zf.read(info)
                if hashlib.sha256(data).hexdigest() != declared['sha256']:
                    inventory_ok = False
                if declared['member_kind'] == 'trip_csv':
                    trip_csvs.append((info.filename, data, declared))
            if len(trip_csvs) != archive['csv_data_member_count']:
                raise EtlError('input_mismatch',
                               f"{zip_path.name} 的骑行 CSV 数量与清单不符")

            for member_path, data, declared in trip_csvs:
                text = io.TextIOWrapper(io.BytesIO(data), encoding='utf-8-sig', newline='')
                reader = csv.reader(text)
                header = next(reader)
                if header != EXPECTED_HEADER:
                    raise EtlError('header_mismatch',
                                   f"{member_path} 表头与 13 列约定不符：{header}")
                # csv_header 约束要求 JSON 数组（CK_meta_source_member_csv_header）
                csv_header = json.dumps(header, ensure_ascii=False, separators=(',', ':'))
                # 记录号从表头 1 开始：首条数据记录为 2。这里先只数行。
                record_count = sum(1 for _ in reader)
                if record_count != declared['csv_data_record_count']:
                    raise EtlError('count_mismatch',
                                   f"{member_path} 行数 {record_count} 与清单 "
                                   f"{declared['csv_data_record_count']} 不符")
                members.append({
                    'zip_sha256': archive['sha256'],
                    'zip_url': archive['url'],
                    'zip_bytes': archive['bytes'],
                    'zip_month_label': archive['month'],
                    'zip_csv_member_count': archive['csv_data_member_count'],
                    'archive_inventory_verified': 1 if inventory_ok else 0,
                    'member_path': member_path,
                    'csv_sha256': declared['sha256'],
                    'csv_header': csv_header,
                    'csv_data_record_count': record_count,
                    'acquired_at_utc': iso_to_sql(archive['acquired_at_utc']),
                    '_zip_path': zip_path,
                })
    return members


def ensure_source_member(client, database, member):
    """档案登记簿：按 (zip_sha256, member_path) 唯一约束查找，没有才登记。"""
    found = client.query(
        "SELECT source_member_id FROM meta.source_member WHERE zip_sha256="
        + sql_str(member['zip_sha256']) + " AND member_path="
        + sql_nstr(member['member_path']), database)
    if found:
        return found[0]['source_member_id']
    client.execute(
        "INSERT INTO meta.source_member (zip_sha256,zip_url,zip_bytes,zip_month_label,"
        "zip_csv_member_count,archive_inventory_verified,member_path,csv_sha256,"
        "csv_header,csv_data_record_count,acquired_at_utc) VALUES ("
        + sql_str(member['zip_sha256']) + ','
        + sql_nstr(member['zip_url']) + ','
        + sql_int(member['zip_bytes']) + ','
        + sql_str(member['zip_month_label']) + ','
        + sql_int(member['zip_csv_member_count']) + ','
        + sql_int(member['archive_inventory_verified']) + ','
        + sql_nstr(member['member_path']) + ','
        + sql_str(member['csv_sha256']) + ','
        + sql_nstr(member['csv_header']) + ','
        + sql_int(member['csv_data_record_count']) + ','
        + "'" + member['acquired_at_utc'] + "');", database)
    return client.query(
        "SELECT source_member_id FROM meta.source_member WHERE zip_sha256="
        + sql_str(member['zip_sha256']) + " AND member_path="
        + sql_nstr(member['member_path']), database)[0]['source_member_id']


def open_run(client, database, run_id, fingerprint):
    client.execute(
        "INSERT INTO meta.load_run (run_id,data_scope,input_set_sha256,model_version,"
        "metric_rule_version,processing_policy_version,code_revision,status,is_current,"
        "started_at_utc,finished_at_utc) VALUES ("
        + "'" + str(run_id) + "',"
        + sql_nstr(DATA_SCOPE) + ','
        + sql_str(fingerprint) + ','
        + sql_str(MODEL_VERSION) + ','
        + sql_str(METRIC_RULE_VERSION) + ','
        + sql_str(PROCESSING_POLICY_VERSION) + ','
        + sql_nstr(code_revision()) + ','
        + "'RUNNING',0,'" + utc_now() + "',NULL);", database)


def fail_run(client, database, run_id, message):
    """运行错误：run 置 FAILED 并记录诊断时间。失败运行不删除、不发布。"""
    client.execute(
        "UPDATE meta.load_run SET status='FAILED', finished_at_utc='" + utc_now()
        + "' WHERE run_id='" + str(run_id) + "';", database)
    print(json.dumps({'ok': False, 'run_id': str(run_id),
                      'diagnostic': str(message)[:1500]}, ensure_ascii=False),
          file=sys.stderr)


def load_member_rows(client, database, run_id, member, source_member_id):
    """逐行读取一个 CSV，分批写入 ods.trip_raw。字段数不符 → 运行错误。"""
    with zipfile.ZipFile(member['_zip_path']) as zf:
        data = zf.read(member['member_path'])
    text = io.TextIOWrapper(io.BytesIO(data), encoding='utf-8-sig', newline='')
    reader = csv.reader(text)
    next(reader)  # 表头 = 记录 1
    rows, record_no, loaded = [], 1, 0
    columns = ['source_member_id', 'csv_record_number', 'field_count', 'raw_values',
               'ride_id_raw', 'rideable_type_raw', 'started_at_raw', 'ended_at_raw',
               'start_station_name_raw', 'start_station_id_raw', 'end_station_name_raw',
               'end_station_id_raw', 'start_lat_raw', 'start_lng_raw',
               'end_lat_raw', 'end_lng_raw', 'member_casual_raw']
    for record in reader:
        record_no += 1  # 多行字段仍是一条 CSV 记录，由 csv 模块正确合并
        if len(record) != 13:
            raise EtlError('field_count',
                           f"{member['member_path']} 记录 {record_no} 字段数 "
                           f"{len(record)}，不符 13 列约定")
        raw_values = json.dumps(record, ensure_ascii=False, separators=(',', ':'))
        rows.append([sql_int(source_member_id), sql_int(record_no), sql_int(13),
                     sql_nstr(raw_values)] + [sql_nstr(v) for v in record])
        if len(rows) >= 500:
            loaded += batch_insert(client, database, 'ods.trip_raw', columns, rows)
            rows = []
    if rows:
        loaded += batch_insert(client, database, 'ods.trip_raw', columns, rows)
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='只清点校验，不写数据库')
    args = parser.parse_args()

    try:
        members = scan_archives()
        fingerprint = input_set_sha256(
            [(m['zip_sha256'], m['member_path'], m['csv_sha256']) for m in members])
        total = sum(m['csv_data_record_count'] for m in members)
        report = {'members': [{k: v for k, v in m.items() if not k.startswith('_')}
                              for m in members],
                  'total_records': total, 'input_set_sha256': fingerprint}
        if args.dry_run:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        database = validate_database(args.database, args.allow_target)
        client = Sqlcmd(args.server)
        run_id = uuid.uuid4()
        open_run(client, database, run_id, fingerprint)
        try:
            for member in members:
                member_id = ensure_source_member(client, database, member)
                # ODS 原文按成员共享存储（无 run_id），重跑时已完整导入的成员直接复用，
                # 保证同一输入重复执行不累加；部分导入视为异常，需人工处理。
                existing = client.query(
                    "SELECT COUNT_BIG(*) AS n FROM ods.trip_raw WHERE source_member_id="
                    + sql_int(member_id), database)[0]['n']
                if existing == member['csv_data_record_count']:
                    read = existing
                elif existing == 0:
                    read = load_member_rows(client, database, run_id, member, member_id)
                else:
                    raise EtlError('partial_load',
                                   f"{member['member_path']} 已存在 {existing} 行，"
                                   f"既不是 0 也不是完整的 {member['csv_data_record_count']} 行，"
                                   "需人工核查后再继续")
                client.execute(
                    "INSERT INTO meta.run_source (run_id,source_member_id,"
                    "read_record_count,read_status) VALUES ("
                    + "'" + str(run_id) + "'," + sql_int(member_id) + ','
                    + sql_int(read) + ",'COMPLETE');", database)
            actual = client.query(
                "SELECT COUNT_BIG(*) AS n FROM ods.trip_raw tr JOIN meta.run_source rs "
                "ON rs.source_member_id = tr.source_member_id WHERE rs.run_id='"
                + str(run_id) + "'", database)[0]['n']
            if actual != total:
                raise EtlError('count_mismatch',
                               f"ODS 行数 {actual} 与清单合计 {total} 不符")
        except EtlError:
            fail_run(client, database, run_id, sys.exc_info()[1])
            raise
        print(json.dumps({'ok': True, 'run_id': str(run_id), 'ods_rows': total,
                          'input_set_sha256': fingerprint,
                          'note': 'ODS 导入完成；run 保持 RUNNING，待后续阶段对账后再 VALIDATED'},
                         ensure_ascii=False, indent=2))
        return 0
    except EtlError as error:
        print(json.dumps({'ok': False, 'kind': error.kind, 'message': str(error)},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
