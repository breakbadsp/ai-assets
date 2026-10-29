#!/usr/bin/env python3
"""Copy the three adapted PStack skills into a project's .agents/skills."""

import argparse
from pathlib import Path
import shutil
import sys


SKILLS = ("typescript-best-practices", "architect", "visual-parity")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parents[1] / "skills"
    target_root = args.project.resolve() / ".agents" / "skills"
    differences = []
    for name in SKILLS:
        source = source_root / name
        target = target_root / name
        if not (source / "SKILL.md").is_file():
            parser.error(f"Missing source skill: {source}")
        source_files = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
        target_files = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        for relative in sorted(source_files):
            expected = (source / relative).read_bytes()
            destination = target / relative
            if destination.is_file() and destination.read_bytes() == expected:
                continue
            if args.check:
                differences.append(str(destination))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / relative, destination)
        differences.extend(str(target / p) for p in sorted(target_files - source_files))
    if differences:
        print("Skill copies differ (extra files are never deleted):", file=sys.stderr)
        print("\n".join(differences), file=sys.stderr)
        return 1
    print("PStack skill copies match." if args.check else "PStack skills synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
