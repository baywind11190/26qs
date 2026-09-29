#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内置四例调用与流程证据检查（builtin flowcheck）。

对四例输入、两侧内置二进制运行**逐字节相同**的外部综合脚本
（read_verilog + synth_intel + check -assert + write_rtlil + stat），并检查：

- 两侧综合 rc=0、check -assert 通过（CHECK 段 "Found and reported 0 problems."）；
- 原版日志不含任何 PMUX_OPT 执行痕迹（其二进制不含该 pass）；
- 优化版日志中 `Executing PMUX_OPT` 恰好一次，且位于 fsm;opt 的 OPT 之后、
  WREDUCE 之前（按 Executing 序列相邻性核对，不能只看字符串出现）；
- 不加载插件：命令行无 -m 参数、日志无插件加载痕迹；
- 两侧脚本逐字节相同（记录脚本 SHA-256）。

输出：04_流程一致性_flowcheck/builtin_run01/（脚本、日志、builtin_flowcheck.json）
退出码：0 全部通过；1 存在不符合项。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
import builtin_common as B


def norm_name(desc: str) -> str:
    """Executing 描述归一化为 pass 名（取首个 token）。"""
    name = B.executing_name(desc)
    return name.split()[0] if name else name


check_pmux_position = B.check_pmux_position


def run_side(side, binary, script, sdir, timeout=900):
    (sdir / "flow.ys").write_text(script)
    rc = C.run_binary(binary, script, sdir / "run.log", cwd=sdir, timeout=timeout)
    log_text = (sdir / "run.log").read_text(errors="replace")
    entries = [(num, norm_name(desc))
               for num, desc in B.extract_executing_entries(log_text)]
    names = [name for _, name in entries]
    info = {
        "rc": rc,
        "binary": str(binary),
        "binary_sha256": C.sha256_file(binary),
        "script_sha256": C.sha256_file(sdir / "flow.ys"),
        "check_assert_ok": C.check_assert_ok(sdir / "run.log"),
        "plugin_loading_suspected": ("Loading plugin" in log_text
                                     or "plugin -i" in log_text),
        "pmux_exec_count": names.count("PMUX_OPT"),
        "abc9_ok": B.abc9_mapping_ok(log_text),
    }
    if side == "optimized":
        info["pmux_position"] = check_pmux_position(entries)
    return info


def main():
    out = C.ROUND_DIR / "04_流程一致性_flowcheck" / "builtin_run01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)
    builtin = C.CONTEXT.get("builtin") or {}
    binaries = {
        "baseline": Path(builtin.get("baseline", {}).get("path", "")),
        "optimized": Path(builtin.get("optimized", {}).get("path", "")),
    }
    for side, binary in binaries.items():
        if not binary.is_file():
            print("STOP：{} 内置二进制缺失：{}".format(side, binary))
            return 1
    summary = {
        "check": "builtin_synth_intel_invocation",
        "round": C.ROUND_DIR.name,
        "command": "run_builtin_flowcheck.py",
        "binaries": {side: {"path": str(p), "sha256": C.sha256_file(p)}
                     for side, p in binaries.items()},
        "cases": [],
    }
    all_ok = True
    for i in range(1, 5):
        top = "test{}".format(i)
        rtl = C.TREE / "pmux_case" / "competition_case" / top / "{}.v".format(top)
        cdir = out / top
        script = C.gen_builtin_synth_ys(rtl, top)
        script_sha = __import__("hashlib").sha256(script.encode()).hexdigest()
        case = {"case": top, "script_sha256": script_sha, "sides": {}}
        for side, binary in binaries.items():
            sdir = cdir / side
            sdir.mkdir(parents=True)
            info = run_side(side, binary, script, sdir)
            case["sides"][side] = info
            if not info["abc9_ok"]:
                all_ok = False
                case["fail"] = case.get("fail", []) + [side + " ABC9 mapping required"]
            if info["rc"] != 0:
                all_ok = False
                case["fail"] = case.get("fail", []) + ["{} rc={}".format(side, info["rc"])]
            if not info["check_assert_ok"]:
                all_ok = False
                case["fail"] = case.get("fail", []) + ["{} check_assert".format(side)]
            if info["plugin_loading_suspected"]:
                all_ok = False
                case["fail"] = case.get("fail", []) + ["{} plugin_suspected".format(side)]
            if side == "baseline" and info["pmux_exec_count"] != 0:
                all_ok = False
                case["fail"] = case.get("fail", []) + ["baseline 含 PMUX_OPT 执行"]
            if side == "optimized":
                pos = info["pmux_position"]
                if not (pos["count"] == 1 and pos["after_opt"] and pos["before_wreduce"]):
                    all_ok = False
                    case["fail"] = case.get("fail", []) + [
                        "optimized PMUX_OPT 位置/次数不符: {}".format(pos)]
        summary["cases"].append(case)
        print("{}: script={} baseline(rc={},pmux={}) optimized(rc={},pmux={},{})".format(
            top, script_sha[:12],
            case["sides"]["baseline"]["rc"], case["sides"]["baseline"]["pmux_exec_count"],
            case["sides"]["optimized"]["rc"], case["sides"]["optimized"]["pmux_exec_count"],
            case["sides"]["optimized"].get("pmux_position", {}).get("after"),
        ), flush=True)
    summary["all_ok"] = all_ok
    (out / "builtin_flowcheck.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("builtin_flowcheck all_ok={}".format(all_ok))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
