# EQY workspace implementation report

Owned changes:
- `D:/codex/0000_26qs/scripts/pmux_validation/runner/eqy_workspace.py` (new common manager).
- `D:/codex/0000_26qs/scripts/pmux_validation/runner/eqy_recheck_support.py` (minimal delegates: sha, safe_root, check_work, inventory, archive_tree; legacy case codes/public API remain).
- `D:/codex/0000_26qs/scripts/pmux_validation/test_eqy_workspace.py` (new real-file tests).

Implementation follows interface.md. Additional public helper `path_identity` normalizes Windows slash/case/dot spellings. General manifest order derives case/check codes; identity binds target/source/tools. Inputs preserve raw bytes and bind source path, SHA-256 and size. Post-setup guards actual generated partitions, strategy references and both literal/absolute path budgets. Archive preserves empty directories and bytes, refuses overwrites, records portable round-relative archive paths, preserves source/partial output; resolver verifies the complete archive without external workspace.

TDD evidence (fixed `.tools/msys64/mingw64/bin/python3.exe -X utf8 -B`):
1. `-m unittest discover -s scripts/pmux_validation -p test_eqy_workspace.py`: initial RED, 5 expected failures `common workspace manager missing` before creating implementation.
2. Initial GREEN: 5 tests, 0.421s.
3. Added absolute strategy-reference escape regression: RED 7 tests, 1 failure (`ValueError not raised`), then parsing fix GREEN 7 tests, 0.572s.
4. Final focused manager run: 9 tests, 0.666s, OK with 1 SKIP (Windows host denied creating symlink, WinError 1314). Other linked-path checks remain implemented; no claim of actual symlink test execution.
5. Legacy `-p test_eqy_recheck.py`: 12 tests, 4.022s, OK.
6. Full `-m unittest discover -s scripts/pmux_validation`: 164 tests, 37.353s, FAILED (2 failures, 1 error), while other agents were actively implementing. Failures: `ManagedV8IntegrationTests.test_build_failure_finalizes_workspace_before_failure_report`, `ManagedV8IntegrationTests.test_managed_report_requires_archive_gate_even_with_no_proof_rows`; error: `InPlaceEqyEvidenceTests.test_successful_proof_keeps_transforms_and_probes_in_final_work` (run_selfcheck fixture lacks CONTEXT). Reported promptly to parent and runtime implementer; parent must rerun final suite after integration.

No Git mutation, no package/config edits, no actual EQY, synthesis, official validation, algorithm or official RTL edits. Original dirty state preserved. This task does not assert official/local validation PASS.
