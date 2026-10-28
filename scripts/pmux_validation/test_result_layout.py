"""Output paths must be directly usable by native validation tools."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent / 'runner'))


class ResultLayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = importlib.import_module('result_layout')

    def test_output_root_is_checked_without_creating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'not-created' / 'results'
            self.assertEqual(self.layout.validate_output_root(candidate), candidate.resolve())
            self.assertFalse(candidate.exists())

    def test_unsafe_output_roots_are_rejected_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            for segment in ('中文', 'with space', 'shell&name', 'dollar$name'):
                candidate = Path(tmp) / segment
                with self.subTest(segment=segment), self.assertRaises(ValueError):
                    self.layout.validate_output_root(candidate)
                self.assertFalse(candidate.exists())

    def test_labels_are_ascii_and_cannot_escape_the_round(self):
        for label in ('v8_same_run', 'V8-fixed-01', '_trial'):
            self.assertEqual(self.layout.validate_label(label), label)
        for label in ('', '中文', 'with space', '../escape', 'x.y', 'x&y'):
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.layout.validate_label(label)

    def test_contained_path_keeps_final_evidence_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.layout.contained_path(root, 'test1', 'work')
            self.assertEqual(path, (root / 'test1' / 'work').resolve())
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):
                self.layout.contained_path(root, '..', 'escape')

    def test_make_round_freezes_ascii_assets_without_a_bridge_sibling(self):
        import validate
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cfg = {'repo': str(repo), 'target_commit': 'a' * 40,
                   'suite_manifest': 'suite-official/manifest.json',
                   'ascii_bridge': str(repo / '_eval_ascii_obsolete')}
            with mock.patch.object(validate, 'git', return_value=''):
                root = validate.make_round(cfg, b'// frozen source\n',
                                           'v8_same_run', 'builtin', collect_tools_env=False)
            context = json.loads((root / 'validation_context.json').read_text())
            self.assertNotIn('ascii_bridge', context)
            self.assertEqual(context['result_layout_version'], 'ascii-v1')
            self.assertTrue(root.name.endswith('_aaaaaaa_r01'))
            self.assertEqual([p.name for p in (repo / 'results').iterdir()], ['official_eval'])
            self.assertEqual((root / '02_assets/tree/src/pmux_opt.cc').read_bytes(),
                             b'// frozen source\n')
            self.assertTrue((root / '03_runner/result_layout.py').is_file())
            self.assertTrue(all(str(p).isascii() for p in root.rglob('*')))

    def test_make_round_rejects_bad_label_before_any_output(self):
        import validate
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with self.assertRaises(ValueError):
                validate.make_round({'repo': str(repo)}, b'', '中文', 'builtin',
                                    collect_tools_env=False)
            self.assertFalse((repo / 'results').exists())


if __name__ == '__main__':
    unittest.main()
