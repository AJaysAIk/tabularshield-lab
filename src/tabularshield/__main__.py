import argparse
from pathlib import Path

from .data import ROOT


def main():
    parser = argparse.ArgumentParser(description="TabularShield public-data research lab")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--output", type=Path, default=ROOT / "reports")
    evaluate.add_argument("--seeds", type=int, default=30)
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path, default=ROOT / "reports")
    sub.add_parser("validate")
    args = parser.parse_args()
    if args.command == "evaluate":
        from .experiment import run

        print(run(args.output, args.seeds))
    elif args.command == "report":
        from .report import build_report

        build_report(args.output)
    else:
        from .data import load_dataset

        for name in ["wholesale", "abalone", "geonames_gb"]:
            source = load_dataset(name)
            print(name, len(source.frame), source.digest)


if __name__ == "__main__":
    main()
