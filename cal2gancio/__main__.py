"""Entry point: python3 -m cal2gancio"""

import sys
from importlib.metadata import version, PackageNotFoundError
from .config import load
from .sync   import sync_all


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] in ("-V", "--version"):
        try:
            print(version("cal2gancio"))
        except PackageNotFoundError:
            print("unknown")
        return

    cfg = load()
    try:
        sync_all(cfg)
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
