<p align="right"><a href="index.en.md">English</a> · <b>Русский</b></p>

# lzt-dev-mcp — карта модулей для AI-агентов

Прочитать перед тем, как открывать исходники в этом репозитории.

## Структура

```
src/lzt_dev_mcp/
├── config.py                Settings (pydantic-settings, префикс LZT_DEV_MCP_)
├── errors.py                Типизированная иерархия ошибок — ProdBlocked, TestnetUnavailable и т. д.
├── catalog/                 Группа A: интроспектирует pylzt напрямую (второй потребитель
│                            техники обхода BaseMethod, которую первой применила registry.py
│                            из lzt-testnet)
│   ├── registry.py            collect_base_methods() — тот же паттерн
│   │                          import-then-__subclasses__, что и в
│   │                          lzt-testnet/src/lzt_testnet/catalog/registry.py
│   ├── models.py               collect_response_models() / get_model_schema() — обходит
│   │                          модели __returning__, ключ — имя класса; при любой коллизии
│   │                          "голых" имён громко бросает ModelDeclarationError вместо
│   │                          тихой перезаписи одной модели другой (реально случалось на
│   │                          паре StatusMessageResponse из market/forum в pylzt —
│   │                          починено выше по цепочке на уровне генератора, см. историю
│   │                          aiolzt)
│   └── errors_catalog.py       интроспектирует pylzt.errors через inspect, а не
│                                переписывается вручную
├── testing/                  Инструменты группы A: send_request (по умолчанию testnet,
│   ├── client_factory.py       прод под защитой), list_methods, get_method_schema,
│   └── tools.py                 get_model_schema, describe_api
├── flow/                     Группа B: тонкие типизированные httpx-обёртки над REST API lzt-flow
│   ├── dtos.py                 frozen-датаклассы, отражающие формы ответов lzt-flow
│   ├── http_client.py          FlowHttpClient — ленивый синглтон уровня модуля (lru_cache),
│   │                          поскольку вызов MCP-инструмента не может принять клиента
│   │                          параметром
│   └── tools.py                 13 инструментов: CRUD flow (только создание/чтение — lzt-flow
│                                не предоставляет update/delete), компиляция, импорт/экспорт,
│                                каталог, интроспекция динамических методов, жизненный цикл
│                                рана (create/list/get/trace — опрос, без проксирования SSE)
├── helpers/
│   └── tools.py               get_rate_limits, get_error_catalog, get_testnet_status
├── eventus/                  Группа D: тонкие типизированные httpx-обёртки над REST API
│                              lzt-eventus
│   ├── dtos.py                 frozen-датаклассы, отражающие формы ответов lzt-eventus;
│   │                          `ctx`/`scope` на проводе — полиморфные union'ы, отражены как
│   │                          непрозрачный passthrough `dict[str, object]` вместо
│   │                          варианта на каждый тип
│   ├── http_client.py          EventusHttpClient — ленивый синглтон уровня модуля
│   │                          (lru_cache), тот же паттерн, что и в `flow/http_client.py`
│   └── tools.py                 8 инструментов: создание/список подписок, pending-события
│                                через polling-транспорт + confirm-read, каталог типов
│                                событий, регистрация/список токен-аккаунтов, health
└── server.py / __main__.py   Сборка FastMCP — stdio (по умолчанию) + streamable-HTTP
                               транспорт, одни и те же определения инструментов в обоих
                               случаях
```

## Инварианты, которые нужно знать перед правками

- **Прод-guard абсолютен.** `send_request(target="prod")` без явного аргумента `token` всегда
  вызывает `ProdBlocked` — никакого фолбэка через переменные окружения, никакого
  кешированного/дефолтного токена, никогда. Это единственное свойство безопасности, ради
  защиты которого существует весь этот сервер; любое изменение здесь требует такой же
  внимательности, как платёжный путь, даже если тут ничего не связано с деньгами.
- `target="testnet"` (значение по умолчанию) без настроенного `LZT_DEV_MCP_TESTNET_BASE_URL`
  вызывает `TestnetUnavailable`, а не тихий провал в прод.
- `FlowHttpClient` и `Settings` — ленивые синглтоны уровня модуля (`lru_cache`), а не
  внедряются через конструктор: сигнатура функции MCP-инструмента диктуется тем, что может
  передать вызывающая LLM, поэтому DI приходится делать внутри тела инструмента, а не через
  параметры `__init__`, как в остальной части экосистемы.
- `list_methods()` обязан продолжать возвращать ≥190 методов pylzt (соответствует планке
  покрытия самого lzt-testnet) — если число падает, скорее всего сломалась та же
  последовательность import-then-walk в `catalog/registry.py`, что изначально ломалась и у
  lzt-testnet (точную причину смотри в `docs/for_ai/index.md` того репозитория).
- `RunTraceEntry` (в `flow/dtos.py`) намеренно не читает настоящее поле `duration_ms` из
  lzt-flow — оно вне рамок замороженного контракта, оставлено непрочитанным, а не добавлено
  по случаю.

## Форма набора тестов

- Юнит-тесты (по умолчанию `pytest -q`) — извлечение схем, логика прод-guard'а, разбор DTO —
  работают без живого сервера.
- `pytest -m e2e -q` — требует запущенного `lzt-testnet` (`cd ../lzt-testnet && scripts/run.sh`)
  и запущенного dev-инстанса `lzt-flow` (`cd ../open-lzt && uv run python dev.py --demo`);
  прогоняет `send_request` против реального testnet, `get_testnet_status` и полный round-trip
  flow (create → compile → run → trace).
