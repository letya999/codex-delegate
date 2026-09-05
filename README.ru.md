<p align="center">
  <a href="README.md">English</a> · <strong>Русский</strong>
</p>

<p align="center">
  <h1 align="center">Codex Delegate</h1>
</p>

<p align="center">
  <a href="https://github.com/letya999/codex-delegate"><img src="https://img.shields.io/badge/статус-активен-brightgreen" alt="статус"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/лицензия-MIT-blue" alt="Лицензия: MIT"></a>
  <a href="https://skills.sh"><img src="https://img.shields.io/badge/skills.sh-доступен-black" alt="skills.sh"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/cli-codex-purple" alt="CLI: codex">
</p>

Скилл-делегат для неинтерактивного запуска OpenAI Codex CLI (`codex`) от [Артема Летюшева](https://github.com/letya999).

Основная команда — `scripts/delegate_codex.py`. Главный потребитель — управляющий агент или оркестратор: каждый запуск выполняет Codex в ограниченном подпроцессе (`codex exec`) и возвращает структурированный JSON-конверт.

---

## Одна цель, изолированный подпроцесс, нулевое доверие

Скрипт-обёртка служит детерминированным барьером безопасности между управляющим агентом и Codex CLI:

- **Строго неинтерактивный запуск:** Вызывает `codex exec` напрямую через `subprocess.run(..., shell=False)` без диалогового перехвата.
- **Песочница только для чтения по умолчанию:** По умолчанию включает изоляцию `read-only`, защищая файловую систему от случайных изменений.
- **Точный захват ответа:** Флаг `--output-last-message` сохраняет итоговый ответ агента без необходимости сложного парсинга JSONL.
- **Верификация результатов:** Ответ считается непроверенным до независимой инспекции через diff и тесты.
- **Изоляция секретов:** Не считывает, не печатает и не передаёт `OPENAI_API_KEY`, токены `~/.codex/auth.json` или файлы `.env`.

## Матрица возможностей

| Параметр / Возможность | Спецификация | Поведение и гарантии |
|---|---|---|
| **Команда запуска** | `codex exec "<task>"` | Неинтерактивное выполнение в режиме exec |
| **Ограничение каталога** | `--cd <cwd>` | Ограничивает область действия целевой папкой проекта |
| **Поток событий** | `--json` | Сохраняет поток событий JSONL в `events.jsonl` |
| **Извлечение ответа** | `--output-last-message <file>` | Записывает чистый финальный ответ агента в манифест |
| **Песочница по умолчанию** | Read-only sandbox | Блокирует несанкционированные изменения на диске |
| **Автономные правки** | `--always-approve` | Включает `--sandbox workspace-write --approve-for-me` |
| **Полный обход песочницы** | `--full-access` | Передаёт `--dangerously-bypass-approvals-and-sandbox` только при явной авторизации |
| **Переопределение бинарника** | Переменная `CODEX_BIN` | Приоритетный путь до вызова из PATH |
| **Коды возврата** | `0, 2, 65, 124, 126, 127` | Предсказуемая маршрутизация ошибок для агентов |

## Установка

Через `npx skills`:

```bash
npx skills add letya999/codex-delegate
```

Или клонированием в каталог скиллов:

```bash
git clone https://github.com/letya999/codex-delegate.git .agents/skills/codex-delegate
```

## Быстрый старт

### POSIX (macOS, Linux, WSL)

```bash
python3 scripts/delegate_codex.py \
  --cwd "$PWD" \
  --task "Проанализируй репозиторий и выдели самую критичную проблему." \
  --timeout 45m
```

### Windows PowerShell

```powershell
py -3 .\scripts\delegate_codex.py `
  --cwd (Get-Location).Path `
  --task "Проанализируй репозиторий и выдели самую критичную проблему." `
  --timeout 45m
```

---

<details>
<summary>Схема JSON-манифеста и интеграция с агентом</summary>

Обёртка записывает `events.jsonl`, `stderr.log`, `last-message.txt` и `result.json` во временный каталог:

```json
{
  "tool": "codex",
  "cwd": "C:\\work\\repo",
  "exit_code": 0,
  "output_dir": "C:\\Temp\\codex-delegate-xyz",
  "stdout": "C:\\Temp\\codex-delegate-xyz\\events.jsonl",
  "events": "C:\\Temp\\codex-delegate-xyz\\events.jsonl",
  "stderr": "C:\\Temp\\codex-delegate-xyz\\stderr.log",
  "response": "Финальный ответ агента, сохраненный через --output-last-message"
}
```

Если Codex завершился с кодом 0, но не вернул ответ, обёртка завершается с кодом `65`.

</details>

<details>
<summary>Флаги CLI и параметры запуска</summary>

| Флаг | Тип | Описание |
|---|---|---|
| `--cwd` | Путь (обязательный) | Рабочий каталог проекта. Код `2`, если каталог не существует. |
| `--task` | Строка (обязательный) | Текст поручения для Codex. |
| `--timeout` | Время (по умолчанию: `45m`) | Таймаут: `90s`, `45m`, `2h` или число секунд. |
| `--model` | Строка | Модель для Codex. |
| `--always-approve` | Флаг | Разрешает изменения в каталоге (`workspace-write`). |
| `--full-access` | Флаг | Полный обход песочницы (`--dangerously-bypass-approvals-and-sandbox`). |
| `--resume` | Строка | Идентификатор сессии для возобновления. |
| `--output-dir` | Путь | Каталог для сохранения логов и манифеста. |

</details>

<details>
<summary>Правила безопасности и изоляция секретов</summary>

- **Защита секретов:** Никогда не считывает и не логирует `OPENAI_API_KEY`, OAuth токены и `~/.codex/auth.json`.
- **Песочница по умолчанию:** Защищает хост-систему от непреднамеренных модификаций.
- **Защита от циклов:** Делегированный Codex не должен запускать новые подпроцессы через обёртки.

</details>

<details>
<summary>Протокол независимой верификации</summary>

Ответы делегата не считаются окончательным доказательством. При изменении файлов:

1. Проверьте diff: `git diff --stat` и `git diff`.
2. Запустите тесты независимо: `pytest`, `npm test`, `cargo test`.
3. Проверьте добавленные файлы и импорты.

</details>

<details>
<summary>Набор тестов</summary>

Запуск тестов через стандартную библиотеку `unittest`:

```bash
python -m unittest discover -s tests -v
```

</details>

<details>
<summary>Точки входа скилла</summary>

- [SKILL.md](SKILL.md) — Спецификация инструкций для кодинг-агентов.
- [QUICKSTART.md](QUICKSTART.md) — Краткое руководство.
- [references/runtime-setup.md](references/runtime-setup.md) — Проверка окружения перед запуском.
- [references/headless-reference.md](references/headless-reference.md) — Справочник флагов Codex CLI.
- [.well-known/agent-skills/index.json](.well-known/agent-skills/index.json) — Индекс для каталога skills.sh.
- [dist/codex-delegate.zip](dist/codex-delegate.zip) — Архив скилла.

</details>

<details>
<summary>Лицензия</summary>

MIT License. См. полный текст в [LICENSE](LICENSE). Copyright (c) 2026 Artem Letyushev.

</details>
