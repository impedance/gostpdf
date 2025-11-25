# План разработки MVP Markdown → PDF

## Состояние на сегодня
- Репозиторий на `master`, неслежимый артефакт: `templates/gost-template.pdf`.
- Требование по окружению: работаем только из активированного Python venv (3.11+), зависимости устанавливаем в него.
- Готовы и покрыты юнит-тестами: `walker.py`, `images.py`, `bundle.py`, `config.py`; базовый `mypy` настроен (`walker` в strict).
- Не реализованы: `pandoc_runner.py`, `cli.py`; нет сквозного пайплайна. Бандл мержит метаданные и умеет запись на диск, интеграция в пайплайн/CLI впереди.
- Локальные проверки не запускались: в окружении нет `pytest` (`pytest: command not found`).

## Параллельные задачи (можно стартовать сразу)
- **T1 — Бандл: метаданные и запись**: `bundle.build(order, image_resolver, metadata=None)` мержит метаданные поверх `DEFAULT_BUNDLE_METADATA`, использует `images.rewrite_images` вместо локальной логики, добавляет `write_bundle(text, path)`. Тесты на фронтматтер/переписывание/запись.
- **T2 — Pandoc runner**: `pandoc_runner.render(bundle, style, template, output, filters=())`; собирает args `--from markdown+yaml_metadata_block --template ... --pdf-engine=xelatex --toc` + `--lua-filter`; ошибки процесса → `RuntimeError` с stderr/командой. Моки `subprocess.run` в тестах.
- **T5 — Reporting helper**: форматирование предупреждений `[CODE] path: message` в `reporting.py`, хелперы для вывода; тесты на формат.

## Последовательные/блокирующие шаги
- **T3 — Пайплайн**: `pipeline.run(md_dir, config, *, style_override=None, metadata_override=None, output_override=None) -> (bundle_path, warnings)`; вызывает `walker`, `bundle.build/write_bundle`, `pandoc_runner.render`, мержит метаданные/стили/выход. Зависит от T1, T2 (по интерфейсам).
- **T4 — CLI**: `cli.main(argv=None) -> int`, argparse (`--md-dir`, `--config` default `config/project.yml`, `--style`, `--metadata key=value`, позиционный output), вывод warnings через reporting, возврат кодов. Зависит от T3/T5.
- **T6 — Интеграция/фикстуры**: `tests/fixtures/pipeline` (минимальное дерево, заглушки стиля/шаблона), интеграционный тест пайплайна с мокнутым `pandoc_runner`. Желательно после фикса интерфейсов T1/T3.
- Финал MVP: установить dev-зависимости (`pytest`, `ruff` и т.п.), прогнать `ruff check . && ruff format . && pytest`, опционально реальный рендер, обновление DoD и отчёт.

## Общие правила по задачам
- После завершения каждой задачи прогонять `ruff check .`, `ruff format .`, `pytest` (или эквивалентные проверки), фиксировать результат.
- Обновлять Definition of Done для задачи сразу по итогам выполнения.

## Прогресс (чекбоксы)
- [x] Walker и структура (`walker.py`, фикстуры, тесты)
- [x] Резолв картинок (`images.py`, переписывание ссылок, тесты)
- [x] Сборка бандла (базовая версия, без метаданных из config/CLI)
- [x] Конфиг (`config.py`, валидация, тесты)
- [x] T1: Бандл — метаданные/запись/переписывание через images
- [ ] T2: Pandoc runner (`pandoc_runner.py`, мок-тесты, смоук рендер)
- [ ] T3: Пайплайн (оркестратор, мерж override, запись bundle, вызов runner)
- [ ] T4: CLI (аргументы, вывод warnings, коды выхода)
- [ ] T5: Reporting helper (форматирование предупреждений)
- [ ] T6: Интеграция/фикстуры (pipeline fixture + интеграционный тест)
- [ ] Финальный прогон линтов/тестов, DoD, опционально реальный рендер
- [x] Статическая типизация (базовый mypy, строгие секции точечно)
