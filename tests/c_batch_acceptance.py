"""批量写入往返检查，仅使用连接内临时表。"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from etl.common import Sqlcmd, batch_insert, sql_nstr

class BatchRoundtrip(unittest.TestCase):
    def test_unicode_quotes_null_and_large_integer_are_lossless(self):
        class Client:
            def execute(self, sql, database):
                output=Sqlcmd('localhost').execute("CREATE TABLE #batch (n decimal(38,0),txt nvarchar(max));"+sql+
                    "SELECT N'__BATCH__'+(SELECT CONVERT(varchar(40),n) AS n,txt FROM #batch ORDER BY n FOR JSON PATH,INCLUDE_NULL_VALUES)+N'__BATCH__';",database)
                self.rows=json.loads(''.join(output.split('__BATCH__')[1].splitlines()))
        client=Client()
        batch_insert(client,'CitibikeDW_B_Test','#batch',['n','txt'],[
            ['9007199254740993',sql_nstr("站点 O'Neil\n🚲")],['2','NULL'],['3',sql_nstr('NULL')],['4',sql_nstr('')]])
        self.assertEqual(client.rows,[{'n':'2','txt':None},{'n':'3','txt':'NULL'},{'n':'4','txt':''},{'n':'9007199254740993','txt':"站点 O'Neil\n🚲"}])

if __name__=='__main__': unittest.main(verbosity=2)
