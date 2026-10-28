# Runtime integration implementation report

Owned files changed:
- D:/codex/0000_26qs/scripts/pmux_validation/runner/run_eqy_chains.py (preserved pre-existing dirty implementation; added managed official context branch only).
- D:/codex/0000_26qs/scripts/pmux_validation/runner/run_selfcheck.py.
- D:/codex/0000_26qs/scripts/pmux_validation/test_eqy_v8_runtime.py (new).

Changes:
- Managed official builtin flow stages model, source RTL and post_abc input bytes through eqy_workspace.stage_input. All manifest cases run two bound main chains; no legacy TARGET_CASES restriction. Managed plugin mode explicitly rejected because the shared job API supports two side jobs only; parent confirmed builtin-only official entry.
- Jobs use job_dir(ctx,'chains',case=...,side=...) or job_dir(ctx,'sc',check=...). Pre-tool config/input/work paths checked, post-setup actual generated partitions audited with expected=None, and actual result keys must equal audited partition set.
- Normal chain/selfcheck summaries and hash manifests remain at original round paths. Legacy functional_recheck six-chain adapter and contextless fixture behavior retained.
- test3 merged template, assertions, depth16, triggering conditions, original partition attempts, depth5, noDF transform, concurrency and timeouts unchanged. Merged probe classification now exit/error-aware; merged tool relative script/input paths checked against actual short cwd.
- Selfcheck uses exit/error-aware probes; expected rejection requires a real clean FAIL and cannot hide another partition tool failure. Clean noDF probes required. Proof ERROR/nonzero exit cannot remain a counterexample FAIL.

TDD evidence (fixed .tools/msys64/mingw64/bin/python3.exe -X utf8 -B):
1. Initial `-m unittest discover -s scripts/pmux_validation -p test_eqy_v8_runtime.py`: RED, 2 tests / 4 failures. Failed because rc1/124/error FAIL counted as REJECT and failed probe SAT text counted valid. After classifier/judge fix: GREEN 2 tests.
2. Added merged failed-exit SAT marker regression: RED 4 tests / 1 failure (`PASS == PASS`). After classify_probe_result integration: GREEN 4 tests.
3. Added pre-tool overbudget selfcheck regression: RED 6 tests / 1 failure (ValueError not raised). Added preflight check_paths: GREEN 6 tests.
4. Added negative-check cross-partition failure regression: RED 7 tests / 1 failure (True accepted). Added all-proof clean process gate: GREEN 7 tests.
5. Additional tool-free integration/characterization coverage: actual manager nine-case 18 distinct short jobs and 18 post_abc staged netlists; byte-preserving selfcheck staging and original summary locations; missing result completeness check. Latest runtime command: GREEN 8 tests, 2.150s.

Other verification:
- `-m unittest discover -s scripts/pmux_validation -p test_eqy_recheck.py`: GREEN 12 tests, 4.472s. Includes unchanged legacy six-job fixture.
- `-m unittest discover -s scripts/pmux_validation -p test_validation.py`: GREEN 64 tests, 10.301s. Workspace-agent whole-suite discovery had exposed missing C.CONTEXT on a legacy fixture; this is corrected with getattr(C,'CONTEXT',{}).
- Parent owns final whole-suite execution after all shared files stabilize; no additional concurrent full suite run by this agent.

No official EQY, proof, synthesis, algorithm/RTL edits, Git mutation, package/config changes or historical writes performed. All external tools in runtime tests are replaced at the subprocess boundary with controlled logs/work files; real workspace identity/staging/auditing is used for 18-chain integration.

## Reviewer follow-up: negative selfcheck premise validity

Changed only owned run_selfcheck.py and test_eqy_v8_runtime.py. judge(REJECT) now additionally requires every noDF verdict to be PREMISES_SAT; existing clean exit/error and VALID probe state gates remain. A genuine clean FAIL in one partition cannot mask UNSAT or OTHER premises in another.

RED: runtime suite 9 tests, 2 failures (PREMISES_UNSAT and OTHER both incorrectly accepted).
GREEN: same fixed runtime command `-m unittest discover -s scripts/pmux_validation -p test_eqy_v8_runtime.py`, 9 tests, 2.310s, OK. Positive all-SAT counterexample case remains accepted. No real tools executed.
