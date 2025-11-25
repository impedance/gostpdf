# Repository Guidelines

Перед началом работы обязательно прочитайте `architecture.md` и `hierarchy-analysis.md`.

## Project Structure & Module Organization
- `prd.md` — цель продукта: CLI принимает дерево Markdown, вычисляет папку с картинками, собирает `bundle.md`, рендерит PDF через Pandoc + LaTeX.
- `hierarchy-analysis.md` — порядок обхода `content/<NNN.slug>/0.index.md` и правило маппинга в `/public/images/<doc-slug>/...`; используйте как единственный источник правды.
- `styles/style.yaml` — токены оформления (файл сейчас называется `style.yaml`, не `gost.yaml`); `templates/gost.tex` — LaTeX-шаблон с переменными Pandoc.
- Ожидаемые папки: `content/`, `public/images/`, промежуточный `bundle.md`, тесты в `tests/`. Каталог `tests/fixtures/` пока отсутствует — создайте при добавлении интеграционных тестов.
- Минимальный пример дерева для тестов:
```
content/003.cu/
  0.index.md
  01.section/
    0.index.md
    010100.chapter.md
public/images/cu/section/chapter/image1.png
```

## Getting Started (для джуна)
1) Установите Python 3.11+, Pandoc 3.x, LaTeX (xelatex).  
2) Создайте виртуальное окружение (`python -m venv .venv && source .venv/bin/activate` или аналог) и фиксируйте зависимости в lock-файле (`requirements.txt`, `uv.lock`, `poetry.lock`) после установки. **Перед каждой работой активируйте .venv (например, `source .venv/bin/activate`) и убедитесь, что `which python`/`pytest` указывают на него.**  
   Всегда начинайте с `source .venv/bin/activate` и используйте `./.venv/bin/python`, `./.venv/bin/pytest` для команд.
3) Локальный инструментарий: `pip install ruff pytest` (типизацию можно позже).  
4) Перед правками прогоните быстрый цикл: `ruff check . && ruff format . && mypy . && pytest`.
5) Рендер PDF выполняйте только при необходимости, чтобы экономить время.

## Build, Test, and Development Commands
- Рендер готового бандла:  
  `pandoc bundle.md --from markdown+yaml_metadata_block --template=templates/gost.tex --pdf-engine=xelatex --toc -o output/report.pdf`
- Планируемый CLI по PRD (в репо по умолчанию используется стиль `style.yaml`):  
  `md2pdf --md-dir ./content/003.cu --config ./config/project.yml --style style ./output/report.pdf`
- `config/project.yml` пример минимальной структуры:  
  ```yaml
  content_root: content
  images_root: public/images
  style: style
  template: templates/gost.tex
  ```
- Быстрый цикл: `ruff check .`, `ruff format .`, `mypy .`, `pytest`.
- Smoke-проверка окружения перед рендером: `pandoc --version` и `xelatex --version`.

## Coding Style & Naming Conventions
- PEP 8, отступы 4 пробела; snake_case для функций/переменных, CapWords для классов; явные параметры, без глобалов.
- CLI флаги как в PRD (`--md-dir`, `--config`, `--style`); имена стилей равны файлам в `styles/`.
- Маппинг стилей: `--style <name>` ищет `styles/<name>.yaml` (без суффикса в имени флага). В текущем репо основной стиль — `styles/style.yaml`, шаблон остаётся `templates/gost.tex`; имена стиля и шаблона не обязаны совпадать.
- YAML — 2 пробела, шрифты в кавычках при пробелах; в `gost.tex` не менять формат переменных `$var$`.
- Линт/формат: `ruff check` и `ruff format` без кастомных настроек на старте.

## Typing Strategy
- Постепенная типизация: сначала публичные API (CLI, резолверы путей/изображений, сборка бандла) и ключевые алгоритмы.
- `mypy`/`pyright` запускать перед пушем или в CI; игноры — точечно.

## Testing Guidelines (фокус 20/80)
- `pytest` с `test_*.py`; фикстуры в `tests/fixtures` (нужно создать при появлении интеграционных тестов).
- Порядок обхода: используйте `hierarchy-analysis.md` как источник правды; `0.index.md` (или `index.md`) всегда первый в директории, затем дочерние md/папки в числовом порядке имени (с паддингами) и рекурсивно. При отсутствии индекса — предупреждение, содержимое по числовому порядку, потом безпрефиксные файлы по алфавиту.
- Резолв картинок: путь `content/003.cu/02.section/020100.file.md` ⇒ `/images/cu/section/file/image1.png` (числовые префиксы удаляются, ветки `cert/nocert` и т.п. учитываются, если есть в контенте).
- Сборка `bundle.md`: интеграционный тест на порядок, разделители, ссылки.
- CLI-smoke с подменой Pandoc/subprocess и тест читаемой ошибки при битой ссылке/файле.
- Пример теста резолва (упрощённый):
```python
def test_resolve_image_path():
    md = Path("content/003.cu/02.section/020100.file.md")
    assert resolve_image_path(md, "image1.png") == Path("/images/cu/section/file/image1.png")
```
- TDD под задачи с логикой (обход, резолв, сборка): сначала пишем минимальный failing тест на ожидаемый порядок/путь/выход, затем реализуем, затем рефакторим с теми же тестами; для IO/вызовов Pandoc — мокайте subprocess и файловую систему.

## Architecture & Practices
- KISS/YAGNI: реализуем только обход, резолв, сборку, запуск Pandoc; без лишних слоёв.
- SRP и разделение IO/логики: чтение/запуск Pandoc отделяем от вычислений. Пример утилиты:
```python
def strip_numeric(stem: str) -> str:
    return stem.split(".", 1)[-1] if "." in stem else stem

def resolve_image_path(md_path: Path, image_name: str) -> Path:
    parts = [strip_numeric(p) for p in md_path.with_suffix("").parts]
    doc_slug = parts[1].split(".", 1)[-1]  # 003.cu -> cu
    return Path("/images") / doc_slug / Path(*parts[2:]) / image_name
```
- DRY умеренно: общие утилиты для путей/конфигов, короткие функции, плоские модули (`walker.py` — обход, `images.py` — резолв, `bundle.py` — склейка, `cli.py` — интерфейс). Сейчас реализованы только `walker.py` и `reporting.py`; остальные модули из `architecture.md`/`PLAN.md` предстоит добавить.
- Ошибки: ранние и читаемые (`raise ValueError(f"Missing file: {path}")`), логируйте путь/контекст.

### Коды предупреждений (см. `src/md2pdf/reporting.py`)
- `SKIPPED_NON_MD`: пропущен не-markdown файл или служебный каталог (включая `doc/` в `003.cu`, который сейчас помечается этим кодом).
- `MISSING_INDEX`: отсутствует `0.index.md` или `index.md` на уровне.
- `NON_NUMERIC_FILE`: markdown без числового префикса, попадает в сортировку по алфавиту.

## Developer Workflow (шаги)
- Планируете задачу → пишете чистую логику и тесты → запускаете `ruff`/`pytest` → при необходимости рендерите PDF → обновляете документацию/фикстуры → делаете PR.
- По итогам каждой задачи прогоняйте обязательные линтеры/форматтеры и тесты (`ruff check .`, `ruff format .`, `pytest` или их эквиваленты), фиксируйте результат в отчёте.
- После завершения каждой задачи актуализируйте definition of done, фиксируя выполненные пункты.
- Всегда сверяйтесь с `PLAN.md`: при выполнении задач отмечайте чекбоксы и обновляйте прогресс/definition of done, чтобы состояние плана соответствовало сделанному.

## Commit & Pull Request Guidelines
- Коммиты: короткий императив (`Add bundle builder`), логически атомарные.
- PR: описание изменений, выполненные команды (ruff/pytest/mypy при наличии), лог/образец PDF если рендерили; ссылки на задачи, явные отклонения от иерархии или стиля.

## Agent-Specific Instructions
- Всегда отвечайте пользователю на русском языке.
- Соблюдайте требования типизации и принципов архитектуры из этого файла.
