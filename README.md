<p align="right"><a href="README.en.md">English</a> · <b>Русский</b></p>

# lzt-mcp

MCP-сервер для экосистемы `lolzteam`/`lzt.market`: тестовые запросы к API (testnet по умолчанию,
прод заблокирован без явного токена), управление сценариями `lzt-flow`, управление
подписками/событиями `lzt-eventus`.

```bash
uv sync --extra dev
scripts/run.sh
```

[Документация для AI-агентов](docs/for_ai/index.md) — карта модулей и инварианты, читать перед
исходниками.

## Установка

```bash
uv sync --extra dev
```

`pylzt` и `lzt-testnet` — git-зависимости (`tool.uv.sources` в `pyproject.toml`), обе тянутся с
ветки `main` репозиториев `open-lzt/pylzt` и `open-lzt/lzt-testnet`. Без `--extra dev`
`lzt-testnet` не ставится и `pytest -m e2e` не соберётся.

## Подключение к MCP-клиенту

`.mcp.json` (или конфиг Claude Desktop) — `cwd` указывает на абсолютный путь до этого репозитория:

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

По умолчанию сервер поднимается на транспорте stdio (`scripts/run.sh` делает то же самое).
Для streamable HTTP:

```bash
uv run python -m lzt_dev_mcp --http --host 127.0.0.1 --port 8770
```

## Инструменты

29 инструментов, зарегистрированы в `server.py` из четырёх групп:

### Тестирование запросов (`lzt_dev_mcp.testing`)

| Инструмент | Что делает |
|---|---|
| `list_methods(namespace=None, search=None)` | Список методов API pylzt с фильтром по namespace/поиску |
| `get_method_schema(method_name)` | Поля запроса метода + имя модели ответа |
| `get_model_schema(model_name)` | JSON Schema модели ответа по имени |
| `send_request(method_name, params, target="testnet", token=None)` | Реальный запрос: testnet по умолчанию, прод — под гвардом |
| `describe_api(query)` | Полнотекстовый поиск по каталогу методов |

### Flow (`lzt_dev_mcp.flow`)

| Инструмент | Что делает |
|---|---|
| `list_flows()` | Список flow текущего тенанта |
| `get_flow(flow_id)` | Полная спецификация flow по id |
| `create_flow(spec)` | Создать flow из FlowSpec |
| `export_flow(flow_id)` | Экспорт flow как версионированного конверта FlowSpec |
| `import_flow(envelope)` | Импорт flow из экспортированного конверта (гейт: компиляция + dry-run) |
| `compile_flow(flow_id)` | Компиляция flow в неизменяемый FlowIR |
| `list_catalog()` | Каталог узлов lzt-flow (типы action/logic/trigger) |
| `list_dynamic_methods(facade)` | Методы фасада pylzt, доступные как динамические узлы flow |
| `get_dynamic_method(facade, method)` | Параметры и форма возврата одного динамического метода |
| `create_run(req)` | Запуск скомпилированного flow (идемпотентно по `run_key`) |
| `list_runs()` | Список ранов текущего тенанта |
| `get_run(run_id)` | Текущий статус рана |
| `get_run_trace(run_id)` | Трейс выполнения рана по узлам |

### Вспомогательные (`lzt_dev_mcp.helpers`)

| Инструмент | Что делает |
|---|---|
| `get_rate_limits()` | Опубликованные лимиты запросов по `RateClass` |
| `get_error_catalog()` | Типизированные классы ошибок pylzt с их аргументами |
| `get_testnet_status()` | Доступен ли настроенный инстанс lzt-testnet |

### События (`lzt_dev_mcp.eventus`)

| Инструмент | Что делает |
|---|---|
| `list_subscriptions()` | Список подписок lzt-eventus (гейт админ-ключом) |
| `create_subscription(spec)` | Новая подписка (webhook/websocket/sse/polling) |
| `poll_pending_events(subscription_id, event_type=None, limit=100)` | Опрос ожидающих событий подписки на polling-транспорте |
| `confirm_read(subscription_id, up_to_seq)` | Зафиксировать прогресс чтения подписки до seq |
| `get_event_types()` | Каталог типов событий, на которые можно подписаться |
| `register_token_account(spec)` | Регистрация токен-аккаунта lzt-eventus |
| `list_token_accounts()` | Список токен-аккаунтов (гейт админ-ключом) |
| `get_eventus_status()` | Доступен ли настроенный инстанс lzt-eventus |

CRUD в группах Flow и События неполный не случайно: `lzt-flow` и `lzt-eventus` сами не
предоставляют update/delete для flow и подписок — инструменты отражают их REST API один в один,
ничего сверху не достроено.

## Гард прода

`send_request(target="prod")` без явного непустого `token` всегда бросает `ProdBlocked`
(`errors.py`) — фолбэка через переменные окружения нет и не будет: `config.py` намеренно не
содержит настройки `allow_prod`, чтобы не было второго, более слабого ответа на тот же вопрос.
Прод-клиент собирает `client_factory.build_client`:

```python
if target == "prod":
    if not token:
        raise ProdBlocked()
    return Client([token])
```

`target="testnet"` (значение по умолчанию) без настроенного `LZT_DEV_MCP_TESTNET_BASE_URL`
бросает `TestnetUnavailable`, а не тихо уходит на прод.

## Конфигурация

Переменные окружения с префиксом `LZT_DEV_MCP_` (`config.py`, `Settings`):

| Переменная | Дефолт | Назначение |
|---|---|---|
| `LZT_DEV_MCP_TESTNET_BASE_URL` | не задан | Куда бьёт `send_request(target="testnet")` и `get_testnet_status()` |
| `LZT_DEV_MCP_LZT_FLOW_BASE_URL` | `http://127.0.0.1:8000` | REST API `lzt-flow` для группы Flow |
| `LZT_DEV_MCP_LZT_FLOW_API_KEY` | не задан | `X-API-Key` для мутирующих маршрутов `lzt-flow` (`compile_flow`, `create_run`, `create_flow`, `import_flow`) |
| `LZT_DEV_MCP_LZT_EVENTUS_BASE_URL` | `http://127.0.0.1:27543` | REST API `lzt-eventus` для группы События |
| `LZT_DEV_MCP_LZT_EVENTUS_ADMIN_API_KEY` | не задан | Админ-ключ для маршрутов `lzt-eventus`: подписки, токен-аккаунты |

`.env.example` в репозитории задаёт только первые три переменные — `lzt-eventus` работает с
дефолтным `base_url` без ключа, пока не нужны админ-маршруты.

## Разработка

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q              # юнит-тесты, e2e пропускаются (маркер `e2e` в pyproject.toml)
uv run pytest -m e2e -q       # нужен запущенный lzt-testnet + dev-инстанс lzt-flow
```

`.github/workflows/ci.yml` гоняет тот же набор (ruff check, ruff format --check, mypy, pytest) на
каждый push в `main` и на каждый PR.

## Экосистема

- [pylzt](https://github.com/open-lzt/pylzt)
- [auto-lzt](https://github.com/open-lzt/auto-lzt)
- [lzt-eventus](https://github.com/open-lzt/lzt-eventus)
- [lzt-testnet](https://github.com/open-lzt/lzt-testnet)
- [open-lzt](https://github.com/open-lzt/open-lzt)

## Лицензия

[MIT](LICENSE)
