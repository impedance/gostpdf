# Архитектура проекта

Документ обязателен к прочтению перед разработкой вместе с `AGENTS.md` и `hierarchy-analysis.md`.

## Цель
CLI собирает структуру Markdown из `content/<NNN.slug>`, резолвит пути к картинкам в `public/images/<slug>/...`, склеивает `bundle.md` и рендерит PDF через Pandoc + LaTeX.

## Модули и ответственности
- `cli.py`: парсинг флагов (`--md-dir`, `--config`, `--style`, output), вызов pipeline, человекочитаемые ошибки.
- `config.py`: чтение `config/project.yml`, валидация путей, маппинг стиля на `styles/<name>.yaml` и шаблона.
- `walker.py`: обход Markdown по правилам из `hierarchy-analysis.md`, отдаёт отсортированный список файлов.
- `images.py`: резолв путей картинок: `content/.../020100.file.md` + `image1.png` ⇒ `/images/<doc-slug>/.../file/image1.png`, переписывание коротких ссылок `::sign-image`.
- `bundle.py`: склейка Markdown в порядке обхода, вставка разделителей/метаданных, опционально запись на диск.
- `pandoc_runner.py`: подготовка аргументов, вызов Pandoc/xelatex, обработка ошибок процессов.
- `logging.py` (или утилита): единообразные сообщения и контекст путей.

## Поток данных (pipeline)
1) CLI → загрузка конфига (`config/project.yml`) → валидация входных путей и стиля.
2) `walker.walk(md_root)` возвращает `list[Path]` Markdown-файлов в нужном порядке и список предупреждений по структуре:
   - `0.index.md` или `index.md` первым на уровне; при отсутствии — warning, содержимое по числовому порядку, потом безпрефиксные файлы.
   - Директории/файлы без числовых префиксов допускаются (например, `000.dev`, `1.cert/2.nocert`), сортируются после числовых.
   - Служебные файлы (`.navigation.yml` и прочие не `.md`) игнорируются с предупреждением.
   - Каталог `doc/` можно пропускать.
3) `bundle.build(order, image_resolver)` читает файлы, переписывает ссылки на картинки через `images.resolve_image_path`, формирует текст `bundle.md`.
4) `pandoc_runner.render(bundle_path, style_path, template_path, output_pdf)` вызывает Pandoc; ошибки процесса пробрасываются как читаемые исключения.

## Контракты и типы (минимум)
- `walk(md_root: Path) -> list[Path]`: бросает `ValueError` при отсутствии входа или несоответствии структуре.
- `resolve_image_path(md_path: Path, image_name: str) -> Path`: возвращает абсолютный путь `/images/<slug>/.../image.ext` без файловой системы; не читает диск.
- `rewrite_images(md_path: Path, text: str) -> str`: переписывает `::sign-image` и короткие пути в абсолютные.
- `build(order: Sequence[Path], image_resolver: Callable[[Path, str], Path]) -> str`: возвращает содержимое бандла; запись на диск вынесена в вызывающий код.
- `render(bundle_path: Path, style: Path, template: Path, output: Path) -> None`: только запуск Pandoc; логика подготовки аргументов внутри.

## Конфиг
Ожидаемый минимальный YAML (`config/project.yml`):
```yaml
content_root: content
images_root: public/images
style: gost
template: templates/gost.tex
```
Расширения: поддержка кастомных стилей (`styles/<name>.yaml`), переопределение выходного каталога.

## Ошибки и валидация
- Ранние проверки: существование `md_root`, доступности стиля и шаблона. Для входной директории фиксируем предупреждения, если нет `0.index.md`/`index.md`, есть файлы без префикса или лишние служебные файлы.
- Сообщения включают путь и причину (пример: `Missing file: content/003.cu/0.index.md`).
- При вызове Pandoc логируем команду и stderr.

## Тестовые опорные точки
- Юнит: `walk` (порядок обхода), `resolve_image_path`/`rewrite_images`, разбор конфига.
- Интеграция: `build` на маленьком дереве из `tests/fixtures` — порядок и корректные пути картинок.
- CLI-smoke: успешный прогон с подменой subprocess, негативный случай на битой ссылке/файле.

## Расширяемость
- Новые стили — добавлением `styles/<name>.yaml` без изменения кода.
- Альтернативные шаблоны — через конфиг.
- Поддержка других входных деревьев — сменой `--md-dir` при сохранении правил обхода из `hierarchy-analysis.md`.
