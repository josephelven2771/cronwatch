"""Allow `python -m cronwatch` invocation."""
import sys
from cronwatch.cli import main

if __name__ == "__main__":
    sys.exit(main())
