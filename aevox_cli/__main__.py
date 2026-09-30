"""Support ``python -m aevox_cli`` as an alternative entry point."""

from .cli import main

raise SystemExit(main())
