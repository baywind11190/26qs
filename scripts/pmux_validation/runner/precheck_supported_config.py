#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""映射网表“支持配置”预检（official4-p2）。

按执行说明修正的边界：
- 目录模式匹配不到任何输入文件 → 失败（退出 2）；
- --expect 模式逐一要求预期文件齐备（缺一即失败，不静默跳过）；
- 寄存器控制端口缺失（clrn/ena 等无 connect）→ 阻断，不把缺失控制端口当合法信号；
- 未知单元类型/参数/端口取值 → 阻断（不静默建模）；
- 纯组合用例（无 dffeas，如 test2）合法；$ 前缀内建单元使用 Yosys 自带语义。

用法：
  precheck_supported_config.py --dir STAGE --expect test1:baseline test1:optimized ... \
      --top-from-name --model form_cells_cycloneiv.v
退出码：0 全部通过；2 阻断（stdout 列出原因；调用方必须停止，不得继续运行证明）。
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formal_status import check_mapped_model


def top_of(il_path: Path) -> str:
    for line in il_path.read_text(errors="replace").splitlines():
        if line.startswith("module ") and not line.startswith("module $"):
            return line.split()[1].lstrip("\\")
    raise ValueError("未找到顶层模块定义")


def gather(dirpath: Path, expect):
    issues = []
    if expect:
        files, missing = [], []
        for spec in expect:
            case, _, side = spec.partition(":")
            f = dirpath / "{}_mapped.il".format("{}_{}".format(case, side))
            (files if f.is_file() else missing).append(f)
        issues += ["缺少预期输入: {}".format(f.name) for f in missing]
        return files, issues
    files = sorted(p for p in dirpath.glob("*.il"))
    if not files:
        issues.append("目录中未匹配到任何输入文件(*.il): {}".format(dirpath))
    return files, issues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True, help="输入目录（.il 文件所在）")
    ap.add_argument("--expect", nargs="*", default=None,
                    help="预期文件清单（case:side；逐项要求 <case>_<side>_mapped.il 存在）")
    ap.add_argument("--top-from-name", action="store_true",
                    help="以文件名中的 case 作为顶层模块名（<case>_<side>_mapped.il）")
    ap.add_argument("--model", default=None,
                    help="同时要求存在的模型文件（可给绝对路径或目录内相对名）")
    args = ap.parse_args(argv)
    d = Path(args.dir)
    if not d.is_dir():
        print("[阻断] 输入目录不存在: {}".format(d))
        return 2
    files, issues = gather(d, args.expect)
    if args.model:
        cand = Path(args.model)
        if not cand.is_file():
            cand = d / args.model
        if not cand.is_file():
            issues.append("缺少模型文件: {}".format(args.model))
    for f in files:
        try:
            top = f.name.split("_", 1)[0] if args.top_from_name else top_of(f)
            check_mapped_model(f, top)
        except ValueError as exc:
            issues.append("{}: {}".format(f.name, exc))
    if issues:
        print("[阻断] 支持配置预检未通过（{} 项）：".format(len(issues)))
        for i in issues:
            print("  - " + i)
        return 2
    print("[通过] 支持配置预检：{} 个输入文件全部在受支持集内{}".format(
        len(files), "；模型文件 {} 存在".format(args.model) if args.model else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
