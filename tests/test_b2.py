"""B2 real behavior tests. Live checks only use CitibikeDW_B_Test."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'scripts' / 'warehouse.py'


class DeploymentSafetyTests(unittest.TestCase):
    def runner(self):
        try:
            spec = importlib.util.spec_from_file_location('b2_warehouse', ENTRY)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except FileNotFoundError:
            self.fail('The protected B2 deployment runner is not implemented yet.')

    def test_system_and_unrelated_databases_are_refused(self):
        # Removing the allowlist must fail this test before any connection.
        module = self.runner()
        for name in ['master', 'AdventureWorksDW2025', 'CitibikeDW_B_Test]; DROP DATABASE x;--', '']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.validate_database(name)

    def test_business_database_needs_explicit_switch(self):
        # Defaulting to the business target must fail this test.
        module = self.runner()
        with self.assertRaises(ValueError):
            module.validate_database('CitibikeDW')
        self.assertEqual(module.validate_database('CitibikeDW', True), 'CitibikeDW')
        self.assertEqual(module.validate_database('CitibikeDW_B_Test'), 'CitibikeDW_B_Test')

    def test_cli_refuses_unsafe_target_before_trying_connection(self):
        # A connection error instead of unsafe_database shows a guard bypass.
        result = subprocess.run([sys.executable, '-X', 'utf8', str(ENTRY), '--server', 'invalid.invalid',
                                 '--database', 'master', 'inspect'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail('Runner has not produced the required structured safety refusal.')
        self.assertEqual(report['kind'], 'unsafe_database')

    def test_changed_ddl_artifact_is_refused(self):
        # Editing a DDL file without a matching reviewed manifest must stop deploy.
        module = self.runner()
        with tempfile.TemporaryDirectory(prefix='citibike-b2-artifact-') as directory:
            folder = Path(directory).resolve()
            self.assertTrue(folder.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            artifact = folder / 'change.sql'
            artifact.write_text('', encoding='utf-8')
            spec = {'ddl_sha256': {'change.sql': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}}
            try:
                validator = module.verify_artifact_hashes
            except AttributeError:
                self.fail('DDL artifact tampering is not checked yet.')
            validator(spec, folder)
            artifact.write_text('-- unreviewed edit', encoding='utf-8')
            with self.assertRaises(module.WarehouseError) as failure:
                validator(spec, folder)
            self.assertEqual(failure.exception.kind, 'artifact_drift')


class LiveSchemaTests(unittest.TestCase):
    def test_same_create_or_alter_body_remains_equivalent(self):
        # SQL Server rewrites the CREATE/ALTER header, not the module body.
        self.command('verify')
        module = DeploymentSafetyTests().runner()
        module.Sqlcmd('localhost').execute((ROOT / 'sql/ddl/050_integrity.sql').read_text(encoding='utf-8'), 'CitibikeDW_B_Test')
        self.assertTrue(self.command('verify')['ok'])

    def test_disabled_foreign_key_is_detected_and_not_silently_repaired(self):
        # Verification must inspect enabled/trusted state, not just object names.
        self.command('verify')
        module = DeploymentSafetyTests().runner()
        client = module.Sqlcmd('localhost')
        restored = False
        try:
            client.execute('ALTER TABLE dwd.fact_trip NOCHECK CONSTRAINT FK_dwd_fact_trip_18;', 'CitibikeDW_B_Test')
            result = subprocess.run([sys.executable, '-X', 'utf8', str(ENTRY), 'verify'],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('foreign_keys', json.loads(result.stdout)['drift'])
            result = subprocess.run([sys.executable, '-X', 'utf8', str(ENTRY), 'deploy'],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['kind'], 'schema_drift')
            self.assertTrue(client.query("SELECT is_disabled FROM sys.foreign_keys WHERE name='FK_dwd_fact_trip_18'", 'CitibikeDW_B_Test')[0]['is_disabled'])
        finally:
            client.execute('ALTER TABLE dwd.fact_trip WITH CHECK CHECK CONSTRAINT FK_dwd_fact_trip_18;', 'CitibikeDW_B_Test')
            restored = True
        self.assertTrue(restored)
        self.assertTrue(self.command('verify')['ok'])

    def test_empty_catalog_query_is_an_empty_list(self):
        # SQL Server 2019 RTM can produce NULL from this empty scalar JSON query.
        module = DeploymentSafetyTests().runner()
        try:
            actual = module.Sqlcmd('localhost').query("SELECT name FROM sys.databases WHERE 1=0")
        except module.WarehouseError as error:
            self.fail('Empty catalog results must be [], not a transport error: ' + str(error))
        self.assertEqual(actual, [])

    def command(self, action):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(ENTRY), action], capture_output=True,
                                text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_catalog_matches_full_model_and_all_constraints_are_trusted(self):
        # Missing columns, a disabled FK, or a changed index must be detected.
        report = self.command('verify')
        self.assertTrue(report['ok'])
        self.assertEqual(report['tables'], 14)
        self.assertEqual(report['columns'], 132)
        self.assertEqual(report['foreign_keys'], 31)
        self.assertEqual(report['drift'], [])

    def test_sql_boundaries_and_negative_constraints(self):
        # Weakening any covered CHECK/FK/UQ/trigger makes a negative case succeed.
        report = self.command('boundaries')
        self.assertGreaterEqual(report['cases'], 25)
        self.assertEqual(report['failed'], [])

    def test_redeploy_preserves_existing_run_row(self):
        # A drop/truncate/rebuild on default redeploy loses this committed marker.
        self.command('verify')
        loader = DeploymentSafetyTests().runner()
        client = loader.Sqlcmd('localhost')
        run_id = str(uuid.uuid4())
        created = False
        try:
            client.execute("""INSERT meta.load_run
              (run_id,data_scope,input_set_sha256,model_version,metric_rule_version,
               processing_policy_version,code_revision,status,is_current,started_at_utc)
              VALUES ('%s',N'JC_official_snapshot',REPLICATE('f',64),'1.0','A-1.0',
                      'B1-1.0',N'SYNTHETIC-B2-SAFE-RERUN','CREATED',0,SYSUTCDATETIME());""" % run_id,
                           'CitibikeDW_B_Test')
            created = True
            report = self.command('deploy')
            self.assertEqual(report['result'], 'already_matches_no_changes')
            rows = client.query("SELECT COUNT_BIG(*) AS n FROM meta.load_run WHERE run_id='%s'" % run_id,
                                'CitibikeDW_B_Test')
            self.assertEqual(rows[0]['n'], 1)
        finally:
            if created:
                client.execute("DELETE meta.load_run WHERE run_id='%s' AND code_revision=N'SYNTHETIC-B2-SAFE-RERUN';" % run_id,
                               'CitibikeDW_B_Test')


if __name__ == '__main__':
    unittest.main()
