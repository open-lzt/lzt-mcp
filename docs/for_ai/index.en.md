<p align="right"><b>English</b> · <a href="index.md">Русский</a></p>

# lzt-dev-mcp — module map for AI agents

Read this before opening source in this repo.

## Layout

```
src/lzt_dev_mcp/
├── config.py                Settings (pydantic-settings, prefix LZT_DEV_MCP_)
├── errors.py                Typed error hierarchy — ProdBlocked, TestnetUnavailable, etc.
├── catalog/                 Group A: introspects pylzt directly (2nd consumer of the
│                            BaseMethod-walk technique lzt-testnet's registry.py pioneered)
│   ├── registry.py            collect_base_methods() — same import-then-__subclasses__
│   │                          pattern as lzt-testnet/src/lzt_testnet/catalog/registry.py
│   ├── models.py               collect_response_models() / get_model_schema() — walks
│   │                          __returning__ models, keyed by class name; raises
│   │                          ModelDeclarationError loudly on any bare-name collision rather
│   │                          than silently overwriting one with the other (previously hit
│   │                          for real by pylzt's market/forum StatusMessageResponse pair
│   │                          — fixed upstream at the generator level, see aiolzt's history)
│   └── errors_catalog.py       introspects pylzt.errors via inspect, not hand-transcribed
├── testing/                  Group A tools: send_request (testnet-default, prod-guarded),
│   ├── client_factory.py       list_methods, get_method_schema, get_model_schema, describe_api
│   └── tools.py
├── flow/                     Group B: thin typed httpx wrappers over lzt-flow's REST API
│   ├── dtos.py                 frozen dataclasses mirroring lzt-flow's response shapes
│   ├── http_client.py          FlowHttpClient — module-level lazy singleton (lru_cache),
│   │                          since an MCP tool call can't take a client as a parameter
│   └── tools.py                 13 tools: flow CRUD (create/read only — no update/delete,
│                                lzt-flow doesn't expose them), compile, import/export,
│                                catalog, dynamic-method introspection, run lifecycle
│                                (create/list/get/trace — polls, doesn't proxy the SSE stream)
├── helpers/
│   └── tools.py               get_rate_limits, get_error_catalog, get_testnet_status
├── eventus/                  Group D: thin typed httpx wrappers over lzt-eventus's REST API
│   ├── dtos.py                 frozen dataclasses mirroring lzt-eventus's response shapes;
│   │                          `ctx`/`scope` are polymorphic unions on the wire, mirrored as
│   │                          opaque `dict[str, object]` passthrough rather than per-variant
│   ├── http_client.py          EventusHttpClient — module-level lazy singleton (lru_cache),
│   │                          same pattern as `flow/http_client.py`
│   └── tools.py                 8 tools: subscription create/list, polling-transport pending
│                                events + confirm-read, event-type catalog, token-account
│                                register/list, health
└── server.py / __main__.py   FastMCP wiring — stdio (default) + streamable-HTTP transport,
                               same tool definitions either way
```

## Invariants worth knowing before editing

- **Prod-guard is absolute.** `send_request(target="prod")` with no explicit `token` argument
  always raises `ProdBlocked` — no env-var fallback, no cached/default token, ever. This is the
  one safety property this whole server exists to protect; any change here needs the same
  scrutiny as a payment path even though nothing here touches money.
- `target="testnet"` (the default) with no configured `LZT_DEV_MCP_TESTNET_BASE_URL` raises
  `TestnetUnavailable` rather than silently falling through to prod.
- `FlowHttpClient` and `Settings` are lazy module-level singletons (`lru_cache`), not constructor-
  injected — an MCP tool function signature is dictated by what the calling LLM can supply, so
  DI has to happen inside the tool body, not via `__init__` params like the rest of the ecosystem.
- `list_methods()` must keep returning ≥190 pylzt methods (matches lzt-testnet's own coverage
  bar) — if it drops, `catalog/registry.py`'s import-then-walk sequence probably broke the same
  way lzt-testnet's did originally (see that repo's `docs/for_ai/index.md` for the exact gotcha).
- `RunTraceEntry` (in `flow/dtos.py`) intentionally does NOT read lzt-flow's real `duration_ms`
  field — out of the frozen contract's scope, left unread rather than added opportunistically.

## Test suite shape

- Unit tests (default `pytest -q`) — schema extraction, prod-guard logic, DTO parsing — run with
  no live server.
- `pytest -m e2e -q` — needs a running `lzt-testnet` (`cd ../lzt-testnet && scripts/run.sh`) and a
  running `lzt-flow` dev instance (`cd ../open-lzt && uv run python dev.py --demo`); exercises
  `send_request` against real testnet, `get_testnet_status`, and a full flow round-trip
  (create → compile → run → trace).
