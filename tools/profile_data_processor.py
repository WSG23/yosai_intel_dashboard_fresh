"""Profile DataProcessor.process with cProfile."""

import argparse
import cProfile
import pstats
from pathlib import Path
import sys

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
        default="profile.prof",
        help="Profile output path",
    )
    args = parser.parse_args()

    from file_processing.data_processor import DataProcessor

    processor = DataProcessor()
    profiler = cProfile.Profile()
    profiler.enable()
    processor.process(args.file_path)
    profiler.disable()
    profiler.dump_stats(args.output)
    stats = pstats.Stats(args.output)
    stats.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(20)


if __name__ == "__main__":
    main()
