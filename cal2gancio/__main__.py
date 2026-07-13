"""Entry point: python3 -m cal2gancio"""

import argparse
import sys
from importlib.metadata import version, PackageNotFoundError
from .config import load
from .sync   import sync_all


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cal2gancio",
        description="Sync events from iCal/HTML sources to Gancio.",
    )
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Fetch and post-process events but print them as JSON instead of sending to Gancio.",
    )
    args = parser.parse_args()

    if args.version:
        try:
            print(version("cal2gancio"))
        except PackageNotFoundError:
            print("unknown")
        return

    cfg = load(dry_run=args.dry_run)
    try:
        sync_all(cfg)
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
