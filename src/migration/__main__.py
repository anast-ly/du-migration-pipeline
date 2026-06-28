"""Entry point: `python -m migration`."""

import sys

from .pipeline import main

if __name__ == "__main__":
    sys.exit(main())
