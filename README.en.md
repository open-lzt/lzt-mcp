<p align="right"><b>English</b> · <a href="README.md">Русский</a></p>

# lzt-dev-mcp

**MCP server giving an AI dev-agent 29 tools for working on the `lolzteam`/`lzt.market`
ecosystem** — send/test raw API requests (testnet by default, prod hard-guarded), manage
`lzt-flow` scenarios over its REST API, manage `lzt-eventus` subscriptions/token-accounts/events,
and introspect the API surface without grepping source.

[AI-agent docs](docs/for_ai/index.en.md) — module map + invariants, read this before the source.

> Private repo, part of the lolzteam-ecosystem sibling set (`pylzt`, `lzt-eventus`,
> `lzt-flow`, `lzt-testnet`, `lzt-dev-mcp`). No secrets committed — a prod token, if ever used,
> is passed per call and never stored.

## Quickstart

```bash
uv sync --extra dev
scripts/run.sh          # stdio transport — the default an MCP client expects
```

`pylzt` is a local path dependency (`../aiolzt` relative to this repo) during development.

Register it with an MCP client (Claude Code, Claude Desktop, etc.):

```json
{
  "mcpServers": {
    "lzt-dev-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "lzt_dev_mcp"],
      "cwd": "C:/Users/User/Desktop/lzt-mcp"
    }
  }
}
```

## Testnet-default / prod-guard (read this before calling `send_request`)

`send_request` defaults to `target="testnet"`. Calling it with `target="prod"` and no explicit,
non-empty `token` argument **always** raises `ProdBlocked` — there is no environment-variable
fallback, ever. Calling it with the default `target="testnet"` when no
`LZT_DEV_MCP_TESTNET_BASE_URL` is configured raises `TestnetUnavailable` rather than silently
falling through to prod. A real prod call requires an explicit token on that specific call, every
time — no cached credential, no implicit default.

## Configuration

Env prefix `LZT_DEV_MCP_` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `TESTNET_BASE_URL` | unset | Where `send_request(target="testnet")` points — usually a running `lzt-testnet` instance |
| `LZT_FLOW_BASE_URL` | `http://127.0.0.1:8000` | The `lzt-flow` REST API Group B talks to |
| `LZT_FLOW_API_KEY` | unset | Auth for the `lzt-flow` REST API, if it requires one |
| `LZT_EVENTUS_BASE_URL` | `http://127.0.0.1:8001` | The `lzt-eventus` REST API Group D talks to |
| `LZT_EVENTUS_ADMIN_API_KEY` | unset | Admin key for `lzt-eventus`'s `/subscriptions`, `/tokens`, `/events` routes |
| `ALLOW_PROD` | unset | Informational only — does **not** bypass the per-call token requirement above |

## Examples

Four ways to drive this server, matching its three tool groups plus the transport choice.

### 1. Ask an agent to test a raw API method against testnet

The intended default path — an AI dev-agent exploring the lzt.market API without touching prod
or real money:

```
list_methods(search="lot")
→ finds market_account_publishing.CreateLot, market.GetLot, ...

get_method_schema("market.GetLot")
→ {"fields": {"item_id": "int"}, "returning": "Lot"}

send_request("market.GetLot", {"item_id": 123})
→ hits target="testnet" (the default) — a real HTTP round-trip against the configured
  lzt-testnet instance, zero risk to production
```

### 2. Drive a full `lzt-flow` scenario lifecycle over its REST API

Use this to build/test flow automations without hand-rolling HTTP calls against `lzt-flow`:

```python
from lzt_dev_mcp.flow.tools import create_flow, compile_flow, create_run, get_run_trace

flow = await create_flow({"name": "test-flow", "nodes": [...]})
ir = await compile_flow(flow.flow_id)
run = await create_run({"flow_id": flow.flow_id, "run_key": "manual-test-1"})
trace = await get_run_trace(run.run_id)
```

### 3. Introspect the API surface instead of grepping `pylzt` source

Use this when writing a new automation and you need the error/rate-limit shape without opening
the SDK:

```
get_error_catalog()
→ {"RateLimited": ["retry_after"], "AuthFailed": ["token_id"], "NotFound": ["item_id"], ...}

get_rate_limits()
→ {"general": "120/min", "search": "20/min"}
```

### 4. Run it over streamable HTTP instead of stdio

Use this when the MCP client is a remote/web client rather than a local process manager:

```bash
uv run python -m lzt_dev_mcp --http --port 8765
```

Same 21 tool definitions either way — stdio and HTTP are just two transports over one server.

## Tools

### Group A — request testing (`lzt_dev_mcp.testing`)
- `list_methods(namespace=None, search=None)` — list pylzt API methods, optionally filtered.
- `get_method_schema(method_name)` — a method's declared request fields + response model name.
- `get_model_schema(model_name)` — a response model's JSON Schema.
- `send_request(method_name, params, target="testnet", token=None)` — send a real request.
- `describe_api(query)` — free-text search over the method catalog.

### Group B — flow management (`lzt_dev_mcp.flow`)
- `list_flows()` / `get_flow(flow_id)` / `create_flow(spec)` — flow CRUD (create/read only;
  `lzt-flow` doesn't expose update/delete).
- `export_flow(flow_id)` / `import_flow(envelope)` — versioned spec round-trip.
- `compile_flow(flow_id)` — compile into an immutable FlowIR.
- `list_catalog()` — `lzt-flow`'s node catalog (action/logic/trigger types).
- `list_dynamic_methods(facade)` / `get_dynamic_method(facade, method)` — pylzt facade
  methods usable as dynamic flow nodes.
- `create_run(req)` — start a run (idempotent on `run_key`).
- `list_runs()` / `get_run(run_id)` / `get_run_trace(run_id)` — poll run status/trace (no SSE
  proxying in this MVP — poll instead of subscribing to `lzt-flow`'s live stream).

### Group C — helpers (`lzt_dev_mcp.helpers`)
- `get_rate_limits()` — published per-`RateClass` request ceilings.
- `get_error_catalog()` — pylzt's typed error classes with their carried args.
- `get_testnet_status()` — whether the configured `lzt-testnet` instance is reachable.

### Group D — event/subscription management (`lzt_dev_mcp.eventus`)
- `list_subscriptions()` / `create_subscription(spec)` — subscription CRUD (create/list; no
  update/deactivate exposed here — out of MVP scope).
- `poll_pending_events(subscription_id, event_type=None, limit=100)` / `confirm_read(subscription_id,
  up_to_seq)` — pull events off a polling-transport subscription and commit read progress.
- `get_event_types()` — `lzt-eventus`'s subscribable event-type catalog.
- `register_token_account(spec)` / `list_token_accounts()` — token-account management.
- `get_eventus_status()` — whether the configured `lzt-eventus` instance is reachable.

## Contributing

Local dev, no CI configured yet:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run pytest -q              # unit tests only (e2e skipped by default)
uv run pytest -m e2e -q       # needs a running lzt-testnet + lzt-flow instance
```

## License

[MIT](LICENSE)
