"""Worker entrypoint: ``python -m dula_worker.main`` (or the console script)."""

from __future__ import annotations

import asyncio

from dula_common.logging import configure_logging

from dula_worker.config import get_settings
from dula_worker.consumer import run


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    asyncio.run(run(settings))


if __name__ == "__main__":
    main()
