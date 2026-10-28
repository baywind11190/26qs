# V8 managed short EQY integration ledger
User plan: 2026-10-27, full nine-case formal run once after tests and fixture smoke.
Ruling: work in the user-requested existing dirty repositories, no branch/worktree/commit/reset. Preserve historical bytes and existing changes.
Tasks: generic workspace; runner/selfcheck wiring; orchestrator/report/cache; tests/smoke; one formal run; independent audit/docs.
Shared API contract recorded in interface.md.
Task workspace complete: 8 passed + 1 symlink privilege skip; runtime 9 passed; orchestrator/cache/report 5 passed. Final full suite: 170 run, 169 passed, 1 skipped, 37.673s. Package 64 entries. Independent task+whole integration review complete; REJECT SAT gate fixed.
Real fixture smoke: formal selfcheck rc0, synthetic same-interface merge via production test3 template rc0, archive verified; no official synthesis.
One official launch: results/official_eval/2026-10-27_1045_v8_eqy_short_17f9361_r01. 18 valid samples, 18 functional chains PASS; final archive/report running. Time gate fails balanced+8.5068%,pipeline+16.3205%,crossbar+7.1074%; preserve all, no rerun.
