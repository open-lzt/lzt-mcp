<p align="right"><a href="README.en.md">English</a> · <b>Русский</b></p>

# lzt-dev-mcp

**MCP-сервер, дающий AI dev-агенту 29 инструментов для работы с экосистемой
`lolzteam`/`lzt.market`** — отправка/тестирование сырых API-запросов (по умолчанию testnet, прод
жёстко заблокирован), управление сценариями `lzt-flow` через его REST API, управление
подписками/токен-аккаунтами/событиями `lzt-eventus`, а также интроспекция поверхности API без
грепа исходников.

[Документация для AI-агентов](docs/for_ai/index.md) — карта модулей + инварианты, читать перед
исходниками.

> Приватный репозиторий, часть набора связанных проектов lolzteam-ecosystem (`pylzt`,
> `lzt-eventus`, `lzt-flow`, `lzt-testnet`, `lzt-dev-mcp`). Секреты в репозитории не хранятся —
> прод-токен, если он вообще используется, передаётся на каждый вызов отдельно и нигде не
> сохраняется.

## Быстрый старт

```bash
uv sync --extra dev
scripts/run.sh          # транспорт stdio — вариант по умолчанию, которого ждёт MCP-клиент
```

`pylzt` во время разработки подключён как локальная path-зависимость (`../aiolzt`
относительно этого репозитория).

Зарегистрируйте сервер в MCP-клиенте (Claude Code, Claude Desktop и т. д.):

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

## Testnet по умолчанию / прод-guard (прочитать перед вызовом `send_request`)

`send_request` по умолчанию работает с `target="testnet"`. Вызов с `target="prod"` без явного,
непустого аргумента `token` **всегда** вызывает исключение `ProdBlocked` — никакого фолбэка через
переменные окружения не существует, никогда. Вызов с `target="testnet"` (по умолчанию), когда
`LZT_DEV_MCP_TESTNET_BASE_URL` не настроен, вызывает `TestnetUnavailable`, а не тихий провал в
прод. Реальный вызов прода требует явного токена на этот конкретный вызов, каждый раз — ни
кешированных credential'ов, ни неявных значений по умолчанию.

## Конфигурация

Префикс переменных окружения `LZT_DEV_MCP_` (см. `.env.example`):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `TESTNET_BASE_URL` | не задана | Куда обращается `send_request(target="testnet")` — обычно запущенный инстанс `lzt-testnet` |
| `LZT_FLOW_BASE_URL` | `http://127.0.0.1:8000` | REST API `lzt-flow`, с которым работает группа B |
| `LZT_FLOW_API_KEY` | не задана | Авторизация для REST API `lzt-flow`, если он её требует |
| `LZT_EVENTUS_BASE_URL` | `http://127.0.0.1:8001` | REST API `lzt-eventus`, с которым работает группа D |
| `LZT_EVENTUS_ADMIN_API_KEY` | не задана | Админ-ключ для маршрутов `lzt-eventus`: `/subscriptions`, `/tokens`, `/events` |
| `ALLOW_PROD` | не задана | Только информационная — **не** обходит требование токена на каждый вызов из пункта выше |

## Примеры

Четыре способа работать с этим сервером — по числу трёх групп инструментов плюс выбор
транспорта.

### 1. Попросить агента протестировать сырой метод API на testnet

Основной предполагаемый сценарий — AI dev-агент исследует API lzt.market, не трогая прод и
реальные деньги:

```
list_methods(search="lot")
→ находит market_account_publishing.CreateLot, market.GetLot, ...

get_method_schema("market.GetLot")
→ {"fields": {"item_id": "int"}, "returning": "Lot"}

send_request("market.GetLot", {"item_id": 123})
→ бьёт в target="testnet" (значение по умолчанию) — реальный HTTP-запрос к настроенному
  инстансу lzt-testnet, нулевой риск для продакшена
```

### 2. Провести полный жизненный цикл сценария `lzt-flow` через его REST API

Используйте это для сборки/тестирования автоматизаций flow без ручных HTTP-вызовов к
`lzt-flow`:

```python
from lzt_dev_mcp.flow.tools import create_flow, compile_flow, create_run, get_run_trace

flow = await create_flow({"name": "test-flow", "nodes": [...]})
ir = await compile_flow(flow.flow_id)
run = await create_run({"flow_id": flow.flow_id, "run_key": "manual-test-1"})
trace = await get_run_trace(run.run_id)
```

### 3. Интроспектировать поверхность API вместо грепа исходников `pylzt`

Используйте это при написании новой автоматизации, когда нужна форма ошибок/рейт-лимитов без
открытия SDK:

```
get_error_catalog()
→ {"RateLimited": ["retry_after"], "AuthFailed": ["token_id"], "NotFound": ["item_id"], ...}

get_rate_limits()
→ {"general": "120/min", "search": "20/min"}
```

### 4. Запустить через streamable HTTP вместо stdio

Используйте это, когда MCP-клиент — удалённый/веб-клиент, а не локальный менеджер процессов:

```bash
uv run python -m lzt_dev_mcp --http --port 8765
```

Одни и те же 21 определение инструментов в обоих случаях — stdio и HTTP это просто два
транспорта поверх одного сервера.

## Инструменты

### Группа A — тестирование запросов (`lzt_dev_mcp.testing`)
- `list_methods(namespace=None, search=None)` — список методов API pylzt, опционально с
  фильтром.
- `get_method_schema(method_name)` — заявленные поля запроса метода + имя модели ответа.
- `get_model_schema(model_name)` — JSON Schema модели ответа.
- `send_request(method_name, params, target="testnet", token=None)` — отправка реального
  запроса.
- `describe_api(query)` — полнотекстовый поиск по каталогу методов.

### Группа B — управление flow (`lzt_dev_mcp.flow`)
- `list_flows()` / `get_flow(flow_id)` / `create_flow(spec)` — CRUD для flow (только
  создание/чтение; `lzt-flow` не предоставляет update/delete).
- `export_flow(flow_id)` / `import_flow(envelope)` — версионированный round-trip спецификации.
- `compile_flow(flow_id)` — компиляция в неизменяемый FlowIR.
- `list_catalog()` — каталог узлов `lzt-flow` (типы action/logic/trigger).
- `list_dynamic_methods(facade)` / `get_dynamic_method(facade, method)` — методы фасадов
  pylzt, доступные как динамические узлы flow.
- `create_run(req)` — запуск рана (идемпотентно по `run_key`).
- `list_runs()` / `get_run(run_id)` / `get_run_trace(run_id)` — опрос статуса/трейса рана (в этом
  MVP нет проксирования SSE — вместо подписки на живой стрим `lzt-flow` используется опрос).

### Группа C — вспомогательные инструменты (`lzt_dev_mcp.helpers`)
- `get_rate_limits()` — опубликованные лимиты запросов по `RateClass`.
- `get_error_catalog()` — типизированные классы ошибок pylzt с их аргументами.
- `get_testnet_status()` — доступен ли настроенный инстанс `lzt-testnet`.

### Группа D — управление событиями/подписками (`lzt_dev_mcp.eventus`)
- `list_subscriptions()` / `create_subscription(spec)` — CRUD для подписок (создание/список; тут
  не предоставлены update/deactivate — вне рамок MVP).
- `poll_pending_events(subscription_id, event_type=None, limit=100)` /
  `confirm_read(subscription_id, up_to_seq)` — забрать события из подписки с
  polling-транспортом и зафиксировать прогресс чтения.
- `get_event_types()` — каталог типов событий `lzt-eventus`, на которые можно подписаться.
- `register_token_account(spec)` / `list_token_accounts()` — управление токен-аккаунтами.
- `get_eventus_status()` — доступен ли настроенный инстанс `lzt-eventus`.

## Разработка

Локальная разработка, CI пока не настроен:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run pytest -q              # только юнит-тесты (e2e по умолчанию пропускаются)
uv run pytest -m e2e -q       # нужен запущенный инстанс lzt-testnet + lzt-flow
```

## Лицензия

[MIT](LICENSE)
