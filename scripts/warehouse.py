"""Protected SQL Server 2019 schema operations; no ETL or destructive reset."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'citibike-warehouse'
VERSION = 'B2-1.1'
TEST_DATABASE = 'CitibikeDW_B_Test'
TARGET_DATABASE = 'CitibikeDW'
SETTINGS = """SET NOCOUNT ON; SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON; SET ANSI_WARNINGS ON; SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON; SET NUMERIC_ROUNDABORT OFF;
"""


class WarehouseError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def validate_database(name, allow_target=False):
    if name not in (TEST_DATABASE, TARGET_DATABASE):
        raise ValueError('Only the two explicitly named project databases are allowed.')
    if name == TARGET_DATABASE and not allow_target:
        raise ValueError('The business database requires --allow-target.')
    return name


class Sqlcmd:
    def __init__(self, server, executable=None):
        self.server = server
        self.executable = executable or os.environ.get('SQLCMD_PATH', 'sqlcmd')

    def execute(self, sql, database='master'):
        fd, filename = tempfile.mkstemp(prefix='citibike-b2-', suffix='.sql')
        os.close(fd)
        path = Path(filename)
        try:
            path.write_text(SETTINGS + sql, encoding='utf-8', newline='\n')
            result = subprocess.run([self.executable, '-S', self.server, '-d', database,
                                     '-E', '-b', '-V', '16', '-l', '5', '-t', '120',
                                     '-f', '65001', '-y', '0', '-w', '65535', '-i', str(path)],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace')
            output = result.stdout + result.stderr
            if result.returncode:
                raise WarehouseError('sql_error', output.strip())
            return output
        finally:
            path.unlink(missing_ok=True)  # Only this process-created SQL file.

    def query(self, select_sql, database='master'):
        marker = '__JSON_' + uuid.uuid4().hex + '__'
        output = self.execute("DECLARE @j nvarchar(max)=(" + select_sql +
                              " FOR JSON PATH,INCLUDE_NULL_VALUES); SELECT N'" + marker +
                              "'+COALESCE(@j,N'[]')+N'" + marker + "';", database)
        match = re.search(re.escape(marker) + '(.*?)' + re.escape(marker), output, re.S)
        if not match:
            raise WarehouseError('sql_output', 'The expected JSON result was not returned.')
        return json.loads(''.join(match.group(1).splitlines()))


def inspect_database(client, database):
    server = client.query("SELECT CONVERT(varchar(32),SERVERPROPERTY('ProductVersion')) AS version,"
                          "CONVERT(varchar(64),SERVERPROPERTY('Edition')) AS edition,"
                          "IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin")[0]
    db = client.query("SELECT name,compatibility_level,state_desc FROM sys.databases WHERE name=N'" + database + "'")
    result = {'server': server, 'database': database, 'exists': bool(db)}
    if db:
        result['database_info'] = db[0]
        result['properties'] = client.query("SELECT name,CONVERT(nvarchar(256),value) AS value FROM sys.extended_properties WHERE class=0", database)
        result['user_objects'] = client.query("SELECT COUNT(*) AS n FROM sys.objects WHERE is_ms_shipped=0 AND type IN('U','V','P','TR','FN','IF','TF')", database)[0]['n']
    return result


def verify_artifact_hashes(spec, root):
    root = root.resolve()
    for relative, expected in spec['ddl_sha256'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise WarehouseError('artifact_drift', 'A reviewed DDL artifact is missing or outside the project.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise WarehouseError('artifact_drift', 'DDL changed without an updated manifest: ' + relative)


def manifest():
    path = ROOT / 'docs/design/physical-model.json'
    if not path.exists():
        raise WarehouseError('missing_artifact', 'The physical manifest is not implemented.')
    spec = json.loads(path.read_text(encoding='utf-8'))
    payload = {k: v for k, v in spec.items() if k != 'manifest_sha256'}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                       separators=(',', ':')).encode('utf-8')).hexdigest()
    if digest != spec['manifest_sha256']:
        raise WarehouseError('artifact_drift', 'The physical manifest fingerprint does not match its contents.')
    verify_artifact_hashes(spec, ROOT)
    return spec


def verify(client, database):
    info = inspect_database(client, database)
    if not info['exists']:
        raise WarehouseError('schema_missing', 'The project database does not exist.')
    properties = {x['name']: x['value'] for x in info['properties']}
    if properties.get('CitibikeWarehouseProject') != PROJECT:
        raise WarehouseError('unmanaged_database', 'Refusing an existing database without the project ownership marker.')
    expected = manifest()
    catalog_sql = (ROOT / 'sql/validation/010_catalog.sql').read_text(encoding='utf-8')
    output = client.execute(catalog_sql, database)
    match = re.search('__CATALOG_BEGIN__(.*?)__CATALOG_END__', output, re.S)
    if not match:
        raise WarehouseError('sql_output', 'Catalog JSON was not returned.')
    actual = json.loads(''.join(match.group(1).splitlines()))
    drift = []
    for key in ('columns', 'keys', 'foreign_keys', 'checks', 'indexes', 'modules'):
        def canonical(rows):
            if key == 'modules':
                rows = [dict(row, definition=re.sub(
                    r'^(CREATE\s+(?:OR\s+ALTER\s+)?|ALTER\s+)(PROCEDURE|TRIGGER)\b',
                    lambda match: 'CREATE ' + match.group(2).upper(),
                    row['definition'].strip(), flags=re.I)) for row in rows]
            return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))
        if canonical(actual[key]) != canonical(expected['catalog'][key]):
            drift.append(key)
    if actual['schemas'] != expected['schemas']:
        drift.append('schemas')
    if info['database_info']['compatibility_level'] != 150:
        drift.append('compatibility_level')
    if not info['server']['version'].startswith('15.'):
        drift.append('engine_version_not_2019')
    if properties.get('CitibikeWarehouseSchema') != VERSION:
        drift.append('schema_version')
    if properties.get('CitibikeWarehouseManifest') != expected['manifest_sha256']:
        drift.append('manifest_fingerprint')
    return {'ok': not drift, 'database': database, 'tables': len(expected['tables']),
            'columns': len(actual['columns']), 'foreign_keys': len(actual['foreign_keys']),
            'drift': drift, 'catalog': actual}


def deploy(client, database):
    info = inspect_database(client, database)
    if not info['server']['version'].startswith('15.'):
        raise WarehouseError('engine_version', 'This deployment requires SQL Server 2019 (15.x).')
    spec = manifest()
    ddl_files = [ROOT / p for p in spec['deployment_files']]
    if info['exists']:
        props = {x['name']: x['value'] for x in info['properties']}
        if props.get('CitibikeWarehouseProject') != PROJECT:
            raise WarehouseError('unmanaged_database', 'Refusing to adopt or overwrite an existing unmarked database.')
        if info['user_objects']:
            report = verify(client, database)
            if not report['ok']:
                raise WarehouseError('schema_drift', 'Schema differs; no automatic repair: ' + ','.join(report['drift']))
            return {'result': 'already_matches_no_changes', 'database': database, 'ok': True}
    else:
        client.execute("CREATE DATABASE [" + database + "] COLLATE Latin1_General_100_BIN2;\nGO\n"
                       "ALTER DATABASE [" + database + "] SET COMPATIBILITY_LEVEL=150;\nGO\n"
                       "EXEC [" + database + "].sys.sp_addextendedproperty @name=N'CitibikeWarehouseProject', @value=N'" + PROJECT + "';")
    body = "SET XACT_ABORT ON; BEGIN TRANSACTION;\nGO\n"
    body += '\nGO\n'.join(path.read_text(encoding='utf-8') for path in ddl_files)
    body += "\nGO\nEXEC sys.sp_addextendedproperty @name=N'CitibikeWarehouseSchema',@value=N'" + VERSION + "';\n"
    body += "EXEC sys.sp_addextendedproperty @name=N'CitibikeWarehouseManifest',@value=N'" + spec['manifest_sha256'] + "'; COMMIT TRANSACTION;"
    client.execute(body, database)
    result = verify(client, database)
    if not result['ok']:
        raise WarehouseError('schema_drift', 'Post-deployment verification differs: ' + ','.join(result['drift']))
    return {'result': 'created_and_verified', 'database': database, 'ok': True}


def boundaries(client, database):
    if database != TEST_DATABASE:
        raise WarehouseError('unsafe_database', 'Synthetic boundary fixtures only run in the test database.')
    report = verify(client, database)
    if not report['ok']:
        raise WarehouseError('schema_drift', 'Verify the structure before boundary fixtures.')
    output = client.execute((ROOT / 'tests/sql/boundary_cases.sql').read_text(encoding='utf-8'), database)
    match = re.search('__B2_CASES_BEGIN__(.*?)__B2_CASES_END__', output, re.S)
    if not match:
        raise WarehouseError('sql_output', 'Boundary results were not returned.')
    cases = json.loads(''.join(match.group(1).splitlines()))
    return {'database': database, 'cases': len(cases), 'failed': [c for c in cases if not c['passed']], 'results': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default=os.environ.get('CITIBIKE_SQL_SERVER', 'localhost'))
    parser.add_argument('--database', default=os.environ.get('CITIBIKE_SQL_DATABASE', TEST_DATABASE))
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('action', choices=['inspect', 'deploy', 'verify', 'boundaries'])
    args = parser.parse_args()
    try:
        try:
            database = validate_database(args.database, args.allow_target)
        except ValueError as error:
            raise WarehouseError('unsafe_database', str(error)) from error
        client = Sqlcmd(args.server)
        if args.action == 'inspect':
            report = inspect_database(client, database)
        elif args.action == 'deploy':
            report = deploy(client, database)
        elif args.action == 'verify':
            report = verify(client, database)
        else:
            report = boundaries(client, database)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report.get('ok') is False or report.get('failed') else 0
    except (WarehouseError, OSError) as error:
        print(json.dumps({'ok': False, 'kind': getattr(error, 'kind', 'environment_error'),
                          'message': str(error)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
