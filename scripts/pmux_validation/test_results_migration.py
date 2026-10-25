"""Evidence-preserving migration behavior, exercised on small isolated trees."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import migrate_results_layout as M

OLD_ROUND = '2026-10-23_1232_Windows同次墙钟与峰值内存_v8_17f9361_第01轮'
BRIDGE = '_eval_ascii_094ada9a41454b0ba3f987f84e615345'


class MigrationTests(unittest.TestCase):
    def fixture(self, root):
        round_root = root / 'results' / '官方口径评测' / OLD_ROUND
        source = round_root / '10_验证工具自检_selfcheck/chains/run01/test1/work/proof.log'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'FAIL: original evidence\r\n')
        (round_root / 'empty_failure_stage').mkdir()
        report = round_root / '00_本轮验证结论.md'
        report.write_bytes('工程FAIL\n'.encode())
        bridge = root / 'results' / BRIDGE / 'chains/test1.v'
        bridge.parent.mkdir(parents=True)
        bridge.write_bytes(b'module test1; endmodule\n')
        (root / 'results/_eval_ascii_0200a46df60a407caa4ca8f9cbe5f629').mkdir()
        return source

    def test_migrate_preserves_files_directories_and_old_path_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self.fixture(root)
            data = original.read_bytes()
            manifest = M.build_manifest(root, tracked={str(original.relative_to(root)).replace('\\', '/')})
            self.assertTrue(any(f['git_tracked'] for f in manifest['files']))
            self.assertEqual(M.verify_manifest(manifest)['missing_files'], 3)
            M.apply_manifest(manifest)
            result = M.verify_manifest(manifest)
            self.assertTrue(result['ok'], result)
            old_rel = original.relative_to(root).as_posix()
            new = M.resolve_path(manifest, str(original).replace('\\', '/').upper())
            self.assertEqual(new.read_bytes(), data)
            self.assertEqual(M.resolve_path(manifest, '10_验证工具自检_selfcheck/chains/run01/test1/work/proof.log',
                                            base='results/官方口径评测/' + OLD_ROUND), new)
            self.assertEqual(M.resolve_path(manifest, old_rel), new)
            new_round = root / 'results/official_eval/2026-10-23_1232_v8_same_run_17f9361_r01'
            self.assertTrue((new_round / 'empty_failure_stage').is_dir())
            self.assertFalse(any(p.name.startswith('_eval_') for p in (root / 'results').iterdir()))
            self.assertTrue(all(str(p.relative_to(root / 'results')).isascii()
                                for p in (root / 'results').rglob('*')))
            shared_file = M.resolve_path(manifest, 'results/' + BRIDGE + '/chains/test1.v')
            self.assertEqual(shared_file, new_round / 'legacy_workspace/chains/test1.v')

    def test_conflict_stops_before_moving_any_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self.fixture(root)
            manifest = M.build_manifest(root, tracked=set())
            destination = M.resolve_path(manifest, str(original))
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b'conflict')
            with self.assertRaises((ValueError, FileExistsError)):
                M.apply_manifest(manifest)
            self.assertTrue(original.exists())
            self.assertEqual(destination.read_bytes(), b'conflict')

    def test_interrupted_migration_resumes_and_rollback_is_reversible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self.fixture(root)
            manifest = M.build_manifest(root, tracked=set())
            def interrupt(index, record):
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                M.apply_manifest(manifest, on_progress=interrupt)
            M.apply_manifest(manifest)
            self.assertTrue(M.verify_manifest(manifest)['ok'])
            M.rollback_manifest(manifest)
            self.assertTrue(original.exists())
            self.assertTrue((root / 'results/_eval_ascii_0200a46df60a407caa4ca8f9cbe5f629').is_dir())

    def test_changed_source_blocks_and_mapping_cannot_escape_results(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self.fixture(root)
            manifest = M.build_manifest(root, tracked=set())
            original.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                M.apply_manifest(manifest)
            with self.assertRaises(ValueError):
                M.resolve_path(manifest, '../../escape')
            manifest['files'][0]['new_path'] = '../outside'
            with self.assertRaises(ValueError):
                M.apply_manifest(manifest)

    def test_zip_bytes_unchanged_and_shared_bridge_has_one_named_location(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            zip_file = root / 'results/官方口径评测/2026-10-23_无调试墙钟与JobCPU诊断_17f9361_test2-test3_第02轮.zip'
            zip_file.parent.mkdir(parents=True)
            zip_file.write_bytes(b'ZIP payload is not rewritten')
            shared = root / 'results/_eval_ascii_ad2d9c12a5fb4d76b6f29d3f682309e4/chains/test1.v'
            shared.parent.mkdir(parents=True)
            shared.write_bytes(b'shared evidence')
            manifest = M.build_manifest(root, tracked=set())
            M.apply_manifest(manifest)
            self.assertEqual(M.resolve_path(manifest, str(zip_file)).read_bytes(), b'ZIP payload is not rewritten')
            self.assertIn('_shared_evidence/2026-10-22_1823_v7_17f9361',
                          M.resolve_path(manifest, str(shared)).as_posix())

    def test_original_hash_list_is_checked_via_old_paths_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self.fixture(root)
            index = root / 'results/官方口径评测' / OLD_ROUND / '11_汇总与证据_summary/ALL_SHA256.txt'
            index.parent.mkdir()
            expected = hashlib.sha256(original.read_bytes()).hexdigest()
            reference = '10_验证工具自检_selfcheck/chains/run01/test1/work/proof.log'
            index.write_text(expected + '  ' + reference + '\n' + '0' * 64 + '  00_本轮验证结论.md\n',
                             encoding='utf-8')
            raw = index.read_bytes()
            manifest = M.build_manifest(root, tracked=set())
            before = M.verify_legacy_hashes(manifest)
            self.assertEqual(before['matched'], 1)
            self.assertEqual(len(before['issues']), 1)
            M.apply_manifest(manifest)
            self.assertEqual(M.verify_legacy_hashes(manifest), before)
            self.assertEqual(M.resolve_path(manifest, str(index)).read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
