#!/usr/bin/env python3
"""Install the stable PMUX pass into an unmodified Yosys 0.69 source tree.

The equivalent unified diff is yosys_0_69_stable_pmux.patch. This installer
also accepts Windows checkouts whose C++ sources use CRLF line endings.
"""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/pmux_opt.cc"


def insert_in_stage(source: str, stage: str, before: str, commands: tuple[str, ...]) -> str:
    marker = f'if (check_label("{stage}")) {{'
    if source.count(marker) != 1:
        raise ValueError(f"Expected exactly one {stage} stage")
    start = source.index(marker)
    next_stage = source.find('if (check_label("', start + len(marker))
    end = len(source) if next_stage < 0 else next_stage
    block = source[start:end]
    lines = block.splitlines(keepends=True)
    targets = [i for i, line in enumerate(lines) if line.strip() == before]
    if not targets or (stage != "map_luts" and len(targets) != 1):
        raise ValueError(f"Expected {before} in {stage} stage")
    # map_luts cleans immediately after ABC9 and again after autoname.
    # The LUT pass belongs after the second clean, as in the reference patch.
    position = targets[-1]
    indent = lines[position][:len(lines[position]) - len(lines[position].lstrip())]
    newline = "\r\n" if "\r\n" in lines[position] else "\n"
    if stage == "map_luts":
        position += 1
    lines[position:position] = [f'{indent}run("{command}");{newline}' for command in commands]
    return source[:start] + "".join(lines) + source[end:]


def prepare_synth(path: Path) -> bytes:
    original = path.read_bytes()
    source = original.decode("utf-8")
    markers = ('run("pmux_opt -arith");', 'run("pmux_opt");', 'run("pmux_opt -lut");')
    counts = [source.count(marker) for marker in markers]
    if counts == [1, 1, 1]:
        return original
    if counts != [0, 0, 0]:
        raise ValueError(f"Partial or repeated PMUX integration in {path}: {counts}")
    source = insert_in_stage(source, "coarse", 'run("wreduce");', ("pmux_opt -arith", "pmux_opt"))
    source = insert_in_stage(source, "map_luts", 'run("clean");', ("pmux_opt -lut",))
    return source.encode("utf-8")


def prepare_cmake(path: Path) -> bytes:
    original = path.read_bytes()
    content = original.decode("utf-8")
    count = content.count("yosys_pass(pmux_opt")
    if count == 1:
        return original
    if count != 0:
        raise ValueError(f"Repeated PMUX CMake registration in {path}")
    newline = "\r\n" if b"\r\n" in original else "\n"
    if content and not content.endswith(("\n", "\r")):
        content += newline
    content += newline + f"yosys_pass(pmux_opt{newline}\tpmux_opt.cc{newline}){newline}"
    return content.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yosys-root", type=Path, required=True)
    parser.add_argument("--replace-existing", action="store_true",
                        help="Replace an existing passes/opt/pmux_opt.cc")
    args = parser.parse_args()
    root = args.yosys_root.resolve()
    synth = root / "techlibs/intel/synth_intel.cc"
    cmake = root / "passes/opt/CMakeLists.txt"
    target = root / "passes/opt/pmux_opt.cc"

    # Validate every target before writing any file.
    source_bytes = SOURCE.read_bytes()
    synth_bytes = prepare_synth(synth)
    cmake_bytes = prepare_cmake(cmake)
    if target.exists() and target.read_bytes() != source_bytes and not args.replace_existing:
        parser.error(f"{target} differs; use --replace-existing to overwrite it")

    if synth.read_bytes() != synth_bytes:
        synth.write_bytes(synth_bytes)
    if cmake.read_bytes() != cmake_bytes:
        cmake.write_bytes(cmake_bytes)
    if not target.exists() or target.read_bytes() != source_bytes:
        target.write_bytes(source_bytes)
    print(f"Stable PMUX integration ready in {root}")


if __name__ == "__main__":
    main()
