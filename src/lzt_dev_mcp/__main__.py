"""CLI entrypoint: `uv run python -m lzt_dev_mcp [--http] [--port N]`."""

from __future__ import annotations

import argparse

from lzt_dev_mcp.logging_setup import configure_logging
from lzt_dev_mcp.server import run


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(prog="lzt-dev-mcp")
    parser.add_argument(
        "--http", action="store_true", help="run streamable-HTTP transport instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host for --http mode")
    parser.add_argument("--port", type=int, default=8770, help="port for --http mode")
    args = parser.parse_args()
    run(mode="http" if args.http else "stdio", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
