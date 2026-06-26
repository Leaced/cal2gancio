"""Entry point: python3 -m ical2gancio"""

import sys
from .config import load
from .sync   import sync_all


def main() -> None:
    cfg = load()
    try:
        sync_all(cfg)
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
