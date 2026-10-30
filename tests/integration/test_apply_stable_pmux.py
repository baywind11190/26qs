#!/usr/bin/env python3
"""Exercise the delivery integrator on LF and CRLF Yosys checkouts."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / 'integration/apply_stable_pmux.py'
SYNTH = '''if (check_label("coarse")) {
            run("opt");
            run("wreduce");
}
if (check_label("map_luts")) {
            run("abc9");
            run("clean");
            run("autoname");
            run("clean");
}
if (check_label("map_cells")) {
}
'''
CMAKE = 'yosys_pass(peepopt\n\tpeepopt.cc\n)\n'


class IntegratorTests(unittest.TestCase):
    def make_source(self, root, newline):
        synth = root / 'techlibs/intel/synth_intel.cc'
        cmake = root / 'passes/opt/CMakeLists.txt'
        synth.parent.mkdir(parents=True)
        cmake.parent.mkdir(parents=True)
        synth.write_bytes(SYNTH.replace('\n', newline).encode())
        cmake.write_bytes(CMAKE.replace('\n', newline).encode())
        return synth, cmake

    def invoke(self, root, *extra):
        return subprocess.run([sys.executable, str(INSTALLER), '--yosys-root', str(root), *extra],
                              capture_output=True, text=True)

    def test_clean_checkout_lf_and_crlf(self):
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=repr(newline)), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                synth, cmake = self.make_source(root, newline)
                result = self.invoke(root)
                self.assertEqual(result.returncode, 0, result.stderr)
                text = synth.read_bytes()
                self.assertEqual(text.count(b'pmux_opt -arith'), 1)
                self.assertEqual(text.count(b'run("pmux_opt")'), 1)
                self.assertEqual(text.count(b'pmux_opt -lut'), 0)
                original_flow = text.decode().replace(
                    '            run("pmux_opt -arith");' + newline, '').replace(
                    '            run("pmux_opt");' + newline, '')
                self.assertEqual(original_flow, SYNTH.replace('\n', newline))
                self.assertEqual(cmake.read_bytes().count(b'yosys_pass(pmux_opt'), 1)
                self.assertEqual((root / 'passes/opt/pmux_opt.cc').read_bytes(),
                                 (ROOT / 'src/pmux_opt.cc').read_bytes())
                if newline == '\r\n':
                    self.assertNotIn(b'\n', text.replace(b'\r\n', b''))
                else:
                    self.assertNotIn(b'\r\n', text)
                again = self.invoke(root)
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertEqual(synth.read_bytes(), text)

    def test_migrate_old_complete_integration_preserves_original_flow(self):
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=repr(newline)), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                synth, cmake = self.make_source(root, newline)
                old = SYNTH.replace('            run("wreduce");',
                    '            run("pmux_opt -arith");\n            run("pmux_opt");\n            run("wreduce");')
                old = old.replace('            run("autoname");\n            run("clean");',
                    '            run("autoname");\n            run("clean");\n            run("pmux_opt -lut");')
                synth.write_bytes(old.replace('\n', newline).encode())
                result = self.invoke(root)
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = synth.read_bytes().decode()
                self.assertNotIn('pmux_opt -lut', actual)
                stripped = actual.replace('            run("pmux_opt -arith");' + newline, '').replace(
                    '            run("pmux_opt");' + newline, '')
                self.assertEqual(stripped, SYNTH.replace('\n', newline))
                before = synth.read_bytes()
                self.assertEqual(self.invoke(root).returncode, 0)
                self.assertEqual(synth.read_bytes(), before)

    def test_partial_integration_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            synth, cmake = self.make_source(root, '\n')
            synth.write_text(SYNTH.replace('            run("wreduce");',
                             '            run("pmux_opt");\n            run("wreduce");'))
            before = synth.read_bytes(), cmake.read_bytes()
            result = self.invoke(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((synth.read_bytes(), cmake.read_bytes()), before)
            self.assertFalse((root / 'passes/opt/pmux_opt.cc').exists())

    def test_existing_pass_requires_explicit_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_source(root, '\n')
            existing = root / 'passes/opt/pmux_opt.cc'
            existing.write_text('old pass')
            rejected = self.invoke(root)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(existing.read_text(), 'old pass')
            accepted = self.invoke(root, '--replace-existing')
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(existing.read_bytes(), (ROOT / 'src/pmux_opt.cc').read_bytes())


if __name__ == '__main__':
    unittest.main()
