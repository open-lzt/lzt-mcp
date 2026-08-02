<p align="right"><b>English</b> · <a href="README.md">Русский</a></p>

# lzt-mcp

An MCP server for the `lolzteam`/`lzt.market` ecosystem: test API requests (testnet by default, prod blocked without an explicit token), drive `lzt-flow` flows, manage `lzt-eventus` subscriptions and events.

```bash
uv sync --extra dev
scripts/run.sh
```

[AI-agent docs](docs/for_ai/index.md) — module map and invariants, read before the source.

## Install

```bash
uv sync --extra dev
```

`pylzt` and `lzt-testnet` are git dependencies (`tool.uv.sources` in `pyproject.toml`), both tracking `main` of `open-lzt/pylzt` and `open-lzt/lzt-testnet`. Without `--extra dev`, `lzt-testnet` isn't installed and `pytest -m e2e` won't collect.

## Connecting an MCP client

`.mcp.json` (or the Claude Desktop config) — `cwd` is the absolute path to this repository:

```json
{
  "mcpServers": {
    "lzt-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "lzt_dev_mcp"],
      "cwd": "/absolute/path/to/lzt-mcp"
    }
  }
}
```

By default the server runs on the stdio transport (`scripts/run.sh` does the same). For streamable HTTP:

```bash
uv run python -m lzt_dev_mcp --http --host 127.0.0.1 --port 8770
```

## Tools

29 tools, registered in `server.py`, in four groups.

### Request testing (`lzt_dev_mcp.testing`)

| Tool | What it does |
|---|---|
| `list_methods(namespace=None, search=None)` | list pylzt API methods, filtered by namespace or search |
| `get_method_schema(method_name)` | a method's request fields plus its response model name |
| `get_model_schema(model_name)` | JSON Schema of a response model by name |
| `send_request(method_name, params, target="testnet", token=None)` | a real request: testnet by default, prod guarded |
| `describe_api(query)` | free-text search over the method catalog |

### Flow (`lzt_dev_mcp.flow`)

| Tool | What it does |
|---|---|
| `list_flows()` | flows of the current tenant |
| `get_flow(flow_id)` | a flow's full spec by id |
| `create_flow(spec)` | create a flow from a FlowSpec |
| `export_flow(flow_id)` | export a flow as a versioned FlowSpec envelope |
| `import_flow(envelope)` | import from an exported envelope (gated on compile + dry-run) |
| `compile_flow(flow_id)` | compile a flow into an immutable FlowIR |
| `list_catalog()` | the lzt-flow node catalog (action/logic/trigger types) |
| `list_dynamic_methods(facade)` | pylzt facade methods usable as dynamic flow nodes |
| `get_dynamic_method(facade, method)` | one dynamic method's params and return shape |
| `create_run(req)` | start a run of a compiled flow (idempotent on `run_key`) |
| `list_runs()` | runs of the current tenant |
| `get_run(run_id)` | a run's current status |
| `get_run_trace(run_id)` | a run's per-node execution trace |

### Helpers (`lzt_dev_mcp.helpers`)

| Tool | What it does |
|---|---|
| `get_rate_limits()` | published per-`RateClass` request ceilings |
| `get_error_catalog()` | pylzt's typed error classes with their carried args |
| `get_testnet_status()` | whether the configured lzt-testnet instance is reachable |

### Events (`lzt_dev_mcp.eventus`)

| Tool | What it does |
|---|---|
| `list_subscriptions()` | lzt-eventus subscriptions (admin-key gated) |
| `create_subscription(spec)` | a new subscription (webhook/websocket/sse/polling) |
| `poll_pending_events(subscription_id, event_type=None, limit=100)` | poll pending events for a polling-transport subscription |
| `confirm_read(subscription_id, up_to_seq)` | commit read progress up to a seq |
| `get_event_types()` | the subscribable event-type catalog |
| `register_token_account(spec)` | register an lzt-eventus token account |
| `list_token_accounts()` | token accounts (admin-key gated) |
| `get_eventus_status()` | whether the configured lzt-eventus instance is reachable |

The CRUD in the Flow and Events groups is incomplete on purpose: `lzt-flow` and `lzt-eventus` don't offer update/delete for flows and subscriptions themselves. These tools mirror their REST APIs one-to-one and add nothing on top.

## The prod guard

`send_request(target="prod")` without an explicit non-empty `token` always raises `ProdBlocked` (`errors.py`). There is no environment-variable fallback and there won't be one: `config.py` deliberately has no `allow_prod` setting, so there is no second, weaker answer to the same question. The prod client is built in `client_factory.build_client`:

```python
if target == "prod":
    if not token:
        raise ProdBlocked()
    return Client([token])
```

`target="testnet"` (the default) with no `LZT_DEV_MCP_TESTNET_BASE_URL` configured raises `TestnetUnavailable` rather than quietly falling through to prod.

## Configuration

Environment variables with the `LZT_DEV_MCP_` prefix (`config.py`, `Settings`):

| Variable | Default | Purpose |
|---|---|---|
| `LZT_DEV_MCP_TESTNET_BASE_URL` | unset | where `send_request(target="testnet")` and `get_testnet_status()` point |
| `LZT_DEV_MCP_LZT_FLOW_BASE_URL` | `http://127.0.0.1:8000` | the `lzt-flow` REST API for the Flow group |
| `LZT_DEV_MCP_LZT_FLOW_API_KEY` | unset | `X-API-Key` for mutating `lzt-flow` routes (`compile_flow`, `create_run`, `create_flow`, `import_flow`) |
| `LZT_DEV_MCP_LZT_EVENTUS_BASE_URL` | `http://127.0.0.1:27543` | the `lzt-eventus` REST API for the Events group |
| `LZT_DEV_MCP_LZT_EVENTUS_ADMIN_API_KEY` | unset | admin key for `lzt-eventus` routes: subscriptions, token accounts |

The repo's `.env.example` sets only the first three — `lzt-eventus` works on its default `base_url` without a key until you need the admin routes.

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q              # unit tests; e2e is skipped (the `e2e` marker in pyproject.toml)
uv run pytest -m e2e -q       # needs a running lzt-testnet and an lzt-flow dev instance
```

`.github/workflows/ci.yml` runs the same set (ruff check, ruff format --check, mypy, pytest) on every push to `main` and every PR.

## Ecosystem

- [pylzt](https://github.com/open-lzt/pylzt)
- [auto-lzt](https://github.com/open-lzt/auto-lzt)
- [lzt-eventus](https://github.com/open-lzt/lzt-eventus)
- [lzt-testnet](https://github.com/open-lzt/lzt-testnet)
- [open-lzt](https://github.com/open-lzt/open-lzt)

## License

[MIT](LICENSE)
