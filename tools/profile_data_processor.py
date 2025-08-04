"""Profile :class:`DataProcessor.process` using cProfile or pyinstrument."""

from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile DataProcessor.process on a file",
    )
    parser.add_argument("file_path", help="Path to input file")
    parser.add_argument(
        "--output",
        "-o",
        help="Profile output path",
    )
    parser.add_argument(
        "--tool",
        choices=["cprofile", "pyinstrument"],
        default="cprofile",
        help="Profiler to use",
    )
    args = parser.parse_args()

    from yosai_intel_dashboard.src.file_processing.data_processor import DataProcessor

    processor = DataProcessor()
    if args.tool == "pyinstrument":
        try:
            from pyinstrument import Profiler
        except Exception as exc:  # pragma: no cover - missing dep
            raise SystemExit("pyinstrument not installed") from exc

        profiler = Profiler()
        profiler.start()
        processor.process(args.file_path)
        profiler.stop()
        output = args.output or "profile.html"
        Path(output).write_text(profiler.output_html(), encoding="utf-8")
        # ``unicode`` parameter was for Python 2 compatibility; Unicode is the
        # default in modern Python versions.
        print(profiler.output_text(color=True))
    else:
        profiler = cProfile.Profile()
        profiler.enable()
        processor.process(args.file_path)
        profiler.disable()
        output = args.output or "profile.prof"
        profiler.dump_stats(output)
        stats = pstats.Stats(output)
        stats.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(20)


if __name__ == "__main__":
    main()
