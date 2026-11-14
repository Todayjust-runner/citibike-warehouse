# -*- coding: utf-8 -*-
"""ETL 共用工具：sqlcmd 客户端与 T-SQL 转义/批量插入。

风格对齐 scripts/warehouse.py：通过本机 sqlcmd + Windows 集成认证执行，
临时 SQL 文件用 UTF-8（-f 65001）传递，避免中文和特殊字符乱码。
"""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = 'CitibikeDW_B_Test'
TARGET_DATABASE = 'CitibikeDW'

SETTINGS = """SET NOCOUNT ON; SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON; SET ANSI_WARNINGS ON; SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON; SET NUMERIC_ROUNDABORT OFF;
"""


class EtlError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def validate_database(name, allow_target=False):
    """只允许两个项目库；业务库必须显式 --allow-target。规则与 warehouse.py 一致。"""
    if name not in (TEST_DATABASE, TARGET_DATABASE):
        raise EtlError('unsafe_database', 'Only the two explicitly named project databases are allowed.')
    if name == TARGET_DATABASE and not allow_target:
        raise EtlError('unsafe_database', 'The business database requires --allow-target.')
    return name


class Sqlcmd:
    """最小 sqlcmd 封装：execute 执行脚本，query 取回 JSON 结果。"""

    def __init__(self, server, executable=None):
        self.server = server
        self.executable = executable or os.environ.get('SQLCMD_PATH', 'sqlcmd')

    def execute(self, sql, database='master'):
        fd, filename = tempfile.mkstemp(prefix='citibike-etl-', suffix='.sql')
        os.close(fd)
        path = Path(filename)
        try:
            path.write_text(SETTINGS + sql, encoding='utf-8', newline='\n')
            result = subprocess.run([self.executable, '-S', self.server, '-d', database,
                                     '-E', '-b', '-V', '16', '-l', '5', '-t', '600',
                                     '-f', '65001', '-y', '0', '-w', '65535', '-i', str(path)],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace')
            output = result.stdout + result.stderr
            if result.returncode:
                raise EtlError('sql_error', output.strip())
            return output
        finally:
            path.unlink(missing_ok=True)

    def query(self, select_sql, database='master'):
        marker = '__JSON_' + uuid.uuid4().hex + '__'
        output = self.execute("DECLARE @j nvarchar(max)=(" + select_sql +
                              " FOR JSON PATH,INCLUDE_NULL_VALUES); SELECT N'" + marker +
                              "'+COALESCE(@j,N'[]')+N'" + marker + "';", database)
        match = re.search(re.escape(marker) + '(.*?)' + re.escape(marker), output, re.S)
        if not match:
            raise EtlError('sql_output', 'The expected JSON result was not returned.')
        return json.loads(''.join(match.group(1).splitlines()))


def sql_nstr(value):
    """Python 字符串 → T-SQL nvarchar 字面量；None → NULL。空字符串保留为空字符串。"""
    if value is None:
        return 'NULL'
    return "N'" + str(value).replace("'", "''") + "'"


def sql_str(value):
    """Python 字符串 → T-SQL varchar 字面量；None → NULL。"""
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def sql_int(value):
    return 'NULL' if value is None else str(int(value))


def batch_insert(client, database, table, columns, rows, chunk=500):
    """分批多行 INSERT。VALUES 单语句上限 1000 行，这里取 500 留余量。"""
    total = 0
    cols = ', '.join(columns)
    for start in range(0, len(rows), chunk):
        part = rows[start:start + chunk]
        values = ',\n'.join('(' + ', '.join(row) + ')' for row in part)
        client.execute("INSERT INTO " + table + " (" + cols + ") VALUES\n" + values + ";", database)
        total += len(part)
    return total
