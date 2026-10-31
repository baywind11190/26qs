import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import validate as V
import result_layout as L


class NativeSelfcheckCache(unittest.TestCase):
    def test_native_gate_is_required_and_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / L.SELFCHECK / 'assets'
            assets.mkdir(parents=True)
            (assets / 'checks.json').write_text(json.dumps({'checks': [{'name': 'positive'}]}))
            summary = root / 'summary.json'
            fp = {'eqy_workspace_version': 'managed-short-v1', 'strategy_version': 'eqy-zero-init-r1'}
            entry = {'ok': True, 'fingerprint': fp, 'evidence_root': str(root)}
            cache = {'entries': {'formal_selfcheck': entry}}
            with patch('eqy_workspace.verify_archive', return_value={'ok': True}):
                for names, expected in [(['positive', 'native_premises_unsat_gate'], True),
                                        (['positive'], False),
                                        (['positive', 'native_premises_unsat_gate', 'unknown'], False)]:
                    summary.write_text(json.dumps({'selfcheck_ok': True, 'cases': [
                        {'name': name, 'ok': True} for name in names]}))
                    entry['formal_evidence'] = {'path': str(summary), 'sha256': V.digest(summary)}
                    self.assertEqual(V.cache_entry_valid(cache, 'formal_selfcheck', fp), expected)


if __name__ == '__main__':
    unittest.main()
