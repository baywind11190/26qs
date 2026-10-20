"""Focused V7 contracts: PowerShell wall time remains separate from V6 CPU."""
import sys
import tempfile
import unittest
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "runner"))
try:
    import measure_v7 as v7
except ImportError:
    v7 = None


class V7Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(v7, "V7 wall-time measurement interface is missing")

    def test_fixed_scheme_and_schedule(self):
        self.assertEqual(v7.SCHEME, "pmux-perf-single-powershell-wall-exitpeak-v7")
        rows = list(v7.schedule())
        self.assertEqual(len(rows), 16)
        self.assertEqual([row["purpose"] for row in rows], ["wall_time"] * 8 + ["memory"] * 8)
        self.assertEqual(len({(r["purpose"], r["case"], r["side"]) for r in rows}), 16)

    def test_wall_thresholds_use_integer_ticks(self):
        self.assertEqual(v7.compare(10_000, 10_500)["wall_5pct"], "PASS")
        self.assertEqual(v7.compare(10_000, 10_501)["wall_5pct"], "FAIL")
        self.assertEqual(v7.compare(10_000, 11_500)["wall_15pct"], "PASS")
        mid = v7.compare(10_000, 10_501)
        self.assertEqual(mid["official_midband_score"], "NOT_DETERMINED")
        self.assertEqual(v7.compare(0, 1)["wall_5pct"], "INVALID")
        self.assertEqual(v7.compare(10_000, 11_501)["wall_15pct"], "FAIL")

    def test_method_identity_and_ticks_milliseconds_consistency(self):
        with tempfile.TemporaryDirectory() as temp:
            stdout_path = Path(temp) / "stdout.bin"
            stderr_path = Path(temp) / "stderr.bin"
            stdout_path.write_bytes(b"stdout")
            stderr_path.write_bytes(b"stderr")
            row = {
            "performance_scheme": v7.SCHEME,
            "case": "test1",
            "purpose": "wall_time",
            "wall_time_method": v7.METHOD,
            "time_span_ticks": 12_345_000,
            "total_milliseconds": 1234.5,
            "rc": 0,
            "timed_out": False,
            "process_exit_observed": True,
            "stdout_capture_complete": True,
            "stderr_capture_complete": True,
            "measure_command_module": "Microsoft.PowerShell.Utility",
            "measure_command_source": "Microsoft.PowerShell.Utility",
            "powershell_major": 5,
            "powershell_minor": 1,
            "powershell_version": "5.1.26100.5074",
            "powershell_path": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
            "powershell_sha256": "d" * 64,
            "powershell_identity_match": True,
            "measure_script_sha256": "e" * 64,
            "native_pid": 77,
            "actual_command": ["yosys.exe", "-s", "flow.ys"],
            "working_directory": temp,
            "environment_sha256": "b" * 64,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "flow_match": True,
            "stat_exists": True,
            "resource_match": True,
            "required_outputs": {"mapped.il": True},
            "measurement_error": None,
            }
            self.assertEqual(v7.wall_errors(row), [])
            row["wall_time_method"] = "python-perf-counter"
            self.assertTrue(v7.wall_errors(row))

    def test_cpu_fields_are_never_wall_time_score_fields(self):
        result = v7.compare(100_000, 105_000)
        self.assertIn("wall_overhead_pct", result)
        self.assertNotIn("cpu_overhead_pct", result)
        self.assertNotIn("cpu_verdict", result)

    def test_shared_validator_recognizes_only_the_fixed_v7_policy(self):
        sys.path.insert(0, str(Path(__file__).parent))
        import validate
        cfg = {"performance_scheme": v7.SCHEME, "wall_policy": v7.POLICY}
        try:
            validate.validate_performance_policy(cfg)
        except ValueError as exc:
            self.fail("V7 policy is rejected: {}".format(exc))
        cfg["wall_policy"] = dict(v7.POLICY, wall_runs_per_side=2)
        with self.assertRaises(ValueError):
            validate.validate_performance_policy(cfg)

    def test_reference_cache_key_only_accepts_missing_unpatched_marker(self):
        sys.path.insert(0, str(Path(__file__).parent / "runner"))
        import prepare_builtin
        wanted = {"algorithm_source_sha256": "abc", "runtime_patch": None,
                  "base_commit": "commit"}
        if not hasattr(prepare_builtin, "reference_key_matches"):
            self.fail("unpatched V6 reference cache matching is not implemented")
        self.assertTrue(prepare_builtin.reference_key_matches(
            {"algorithm_source_sha256": "abc", "base_commit": "commit"}, wanted))
        self.assertFalse(prepare_builtin.reference_key_matches(
            {"algorithm_source_sha256": "abc", "base_commit": "different"}, wanted))
        self.assertFalse(prepare_builtin.reference_key_matches(
            {"algorithm_source_sha256": "abc", "base_commit": "commit",
             "runtime_patch": {"method": "v6"}}, wanted))

    def test_v7_report_uses_wall_category_and_does_not_claim_cpu_or_delivery(self):
        import copy
        import report
        from test_validation import BuiltinModeTests
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            BuiltinModeTests()._write_builtin_round(root)

            def load(rel):
                return json.loads((root / rel).read_text(encoding="utf-8"))

            def save(rel, data):
                (root / rel).write_text(json.dumps(data), encoding="utf-8")

            ctx = load("validation_context.json")
            ctx.update(flow_version="official4-p6-windows", performance_scheme=v7.SCHEME,
                       wall_policy=v7.POLICY, performance_pairs=1, suite_verified=True)
            save("validation_context.json", ctx)
            pub = load("05_公开四例_public/round01/summary.json")
            rates = []
            for case in pub["cases"]:
                case.update(resource_checks_ok=True, io_nonincrease=True,
                            other_resources_nonincrease=True,
                            baseline_lut_count=100, optimized_lut_count=80,
                            baseline_inverter_count=0, optimized_inverter_count=0,
                            baseline_logic_units=100, optimized_logic_units=80,
                            logic_reduction_pct=20.0,
                            baseline_comb=100, optimized_comb=80,
                            baseline_abc9_ok=True, optimized_abc9_ok=True,
                            baseline_formal_netlist_stage="post_abc",
                            optimized_formal_netlist_stage="post_abc",
                            baseline_split_full_resources_match=True,
                            optimized_split_full_resources_match=True)
                for side, logic in (("baseline", 100), ("optimized", 80)):
                    case[side + "_resources"] = {
                        "logic_units": logic, "dff_count": 10,
                        "io_ports": 2, "io_bits": 2,
                        "io_cell_types": {"cycloneiv_io": 2}, "other_cell_types": {}}
                rates.append(20.0)
            pub["public_mean_logic_reduction_pct"] = sum(rates) / 4
            save("05_公开四例_public/round01/summary.json", pub)
            chains = load("10_验证工具自检_selfcheck/chains/run01/chains_summary.json")
            for row in chains:
                row["formal_netlist_stage"] = "post_abc"
            save("10_验证工具自检_selfcheck/chains/run01/chains_summary.json", chains)

            output_dir = root / "09_时间内存开销_performance/round01"
            summaries = []
            for case in v7.CASES:
                summary = {"case": case, "performance_scheme": v7.SCHEME,
                           "wall_policy": v7.POLICY, "execution_complete": True,
                           "memory_metric": "yosys_peak_working_set_bytes",
                           "wall_runs": [], "memory_runs": []}
                for side, ticks in (("baseline", 10_000_000), ("optimized", 10_500_000)):
                    folder = output_dir / case / "wall_time" / side
                    folder.mkdir(parents=True)
                    stdout = folder / "stdout.bin"
                    stderr = folder / "stderr.bin"
                    stdout.write_bytes(b"ok")
                    stderr.write_bytes(b"")
                    (folder / "mapped.il").write_text("mapped", encoding="utf-8")
                    (folder / "stat.json").write_text("{}", encoding="utf-8")
                    summary["wall_runs"].append({
                        "side": side, "case": case, "purpose": "wall_time",
                        "performance_scheme": v7.SCHEME,
                        "wall_time_method": v7.METHOD, "time_span_ticks": ticks,
                        "total_milliseconds": ticks / 10_000, "rc": 0, "timed_out": False,
                        "process_exit_observed": True, "stdout_capture_complete": True,
                        "stderr_capture_complete": True,
                        "measure_command_module": "Microsoft.PowerShell.Utility",
                        "measure_command_source": "Microsoft.PowerShell.Utility",
                        "powershell_major": 5, "powershell_minor": 1,
                        "powershell_version": "5.1.26100.5074",
                        "powershell_path": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                        "powershell_sha256": "d" * 64,
                        "powershell_identity_match": True,
                        "measure_script_sha256": "e" * 64,
                        "native_pid": 44,
                        "actual_command": ["/" + side + "/yosys.exe", "-s", "flow.ys"],
                        "working_directory": str(folder), "stdout_path": str(stdout),
                        "stderr_path": str(stderr), "environment_sha256": "b" * 64,
                        "flow_sha256": "c" * 64, "measurement_error": None,
                        "flow_match": True, "stat_exists": True, "resource_match": True,
                        "required_outputs": {"mapped.il": True, "stat.json": True}})
                for side in ("baseline", "optimized"):
                    summary["memory_runs"].append({
                        "side": side, "case": case, "purpose": "memory",
                        "performance_scheme": v7.SCHEME,
                        "rc": 0, "timed_out": False, "metrics_valid": True,
                        "measurement_error": None, "main_pid": 55,
                        "root_debugged": True, "memory_capture_complete": True,
                        "memory_exit_event_observed": True, "memory_exit_event_pid": 55,
                        "memory_method_version": "windows-root-exit-event-v1",
                        "flow_sha256": "c" * 64,
                        "flow_match": True, "stat_exists": True, "resource_match": True,
                        "required_outputs": {"mapped.il": True, "stat.json": True},
                        "yosys_peak_working_set_bytes": 1000,
                        "stat_exists": True, "resource_match": True, "flow_match": True})
                summaries.append(summary)
            save("09_时间内存开销_performance/round01/performance_summary.json", summaries)

            report.build_builtin_report(root)
            manifest = load("11_汇总与证据_summary/manifest.json")
            self.assertEqual(manifest["category_status"].get("wall_time"), "PASS")
            self.assertNotIn("cpu", manifest["category_status"])
            self.assertEqual(manifest["delivery_verdict"], "NOT_RUN")
            self.assertEqual(manifest["project_readiness"], "NOT_READY")
            self.assertEqual(manifest["official_acceptance"], "NOT_CLAIMED")
            self.assertTrue(all("cpu_overhead_pct" not in row for row in manifest["performance"]))
            text = (root / "00_本轮验证结论.md").read_text(encoding="utf-8")
            self.assertIn("PowerShell Measure-Command 墙钟时间", text)
            self.assertIn("5%～15%之间的官方评分规则尚未明确", text)
            self.assertIn("墙钟按每例 `testN→baseline→optimized`", text)
            self.assertIn("用例顺序为 test1 至 test4", text)
            self.assertIn("与报告同轮生成或更新", text)
            self.assertNotIn("生成于运行收尾", text)
            self.assertNotIn("pair 奇 baseline", text)

    def test_exactly_sixteen_independent_wall_and_memory_runs(self):
        stat = {"design": {"num_cells_by_type": {"cycloneiv_lcell_comb": 2},
                           "num_ports": 2, "num_port_bits": 2}}
        calls = []
        fake_ps = Path(sys.executable).resolve()
        fake_ps_hash = hashlib.sha256(fake_ps.read_bytes()).hexdigest()

        def wall_execute(command, *, cwd, log_path, stdout_path, stderr_path,
                         result_path, timeout_s, powershell_path, env):
            cwd = Path(cwd)
            calls.append(("wall_time", command[0]))
            (cwd / "mapped.il").write_text("mapped\n", encoding="utf-8")
            (cwd / "stat.json").write_text(json.dumps(stat), encoding="utf-8")
            Path(stdout_path).write_bytes(b"yosys output")
            Path(stderr_path).write_bytes(b"")
            return {
                "wall_time_method": v7.METHOD, "performance_scheme": v7.SCHEME,
                "time_span_ticks": 10_000 if "base" in command[0] else 10_500,
                "total_milliseconds": 1 if "base" in command[0] else 1.05,
                "rc": 0, "timed_out": False, "process_exit_observed": True,
                "stdout_capture_complete": True, "stderr_capture_complete": True,
                "measure_command_module": "Microsoft.PowerShell.Utility",
                "measure_command_source": "Microsoft.PowerShell.Utility",
                "powershell_major": 5, "powershell_minor": 1,
                "powershell_version": "5.1.26100.5074",
                "powershell_path": str(fake_ps),
                "powershell_sha256": fake_ps_hash,
                "powershell_identity_match": True,
                "measure_script_sha256": "e" * 64,
                "native_pid": 77,
                "actual_command": command, "working_directory": str(cwd),
                "environment_sha256": hashlib.sha256(json.dumps(
                    sorted((str(k), str(v)) for k, v in env.items()),
                    ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "flow_sha256": hashlib.sha256(b"same flow\n").hexdigest(),
                "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
                "measurement_error": None,
            }

        def memory_execute(command, *, cwd, log_path, timeout_s):
            cwd = Path(cwd)
            calls.append(("memory", command[0]))
            (cwd / "mapped.il").write_text("mapped\n", encoding="utf-8")
            (cwd / "stat.json").write_text(json.dumps(stat), encoding="utf-8")
            return {
                "rc": 0, "timed_out": False, "metrics_valid": True,
                "measurement_error": None, "main_pid": 88, "root_debugged": True,
                "memory_capture_complete": True, "memory_exit_event_observed": True,
                "memory_exit_event_pid": 88, "memory_method_version": "windows-root-exit-event-v1",
                "yosys_peak_working_set_bytes": 1000,
            }

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for case in v7.CASES:
                for side in ("baseline", "optimized"):
                    folder = root / f"05_公开四例_public/round01/{case}/{side}"
                    folder.mkdir(parents=True)
                    (folder / "stat.json").write_text(json.dumps(stat), encoding="utf-8")
            context = {"performance_scheme": v7.SCHEME, "wall_policy": v7.POLICY,
                       "mode": "builtin", "wall_time_tool": {
                           "path": str(fake_ps), "sha256": fake_ps_hash}}
            rc = v7.run(context, root, {"baseline": Path("baseline/yosys.exe"),
                                        "optimized": Path("optimized/yosys.exe")},
                        {case: "same flow\n" for case in v7.CASES},
                        wall_execute=wall_execute, memory_execute=memory_execute)
            status = json.loads((root / "09_时间内存开销_performance/round01/execution_status.json").read_text(encoding="utf-8"))
            self.assertEqual(rc, 0, status["error"])
            self.assertEqual(len(calls), 16)
            self.assertEqual([purpose for purpose, _ in calls], ["wall_time"] * 8 + ["memory"] * 8)
            rows = json.loads((root / "09_时间内存开销_performance/round01/performance_summary.json").read_text(encoding="utf-8"))
            for summary in rows:
                result = v7.judge_case(summary)
                self.assertTrue(result["pass"])
                self.assertEqual(result["wall_5pct"], "PASS")
                self.assertNotIn("cpu_overhead_pct", result)


if __name__ == "__main__":
    unittest.main()
