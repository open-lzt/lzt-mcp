#!/usr/bin/env bash
# Boots lzt-dev-mcp in stdio mode (default MCP client transport).
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python -m lzt_dev_mcp
