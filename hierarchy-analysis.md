Summary of the Markdown hierarchy in `content/003.cu` (for bundling)
--------------------------------------------------------------------

- Root entry point: `content/003.cu/0.index.md` — top-level index for the whole document set.
- Top-level sections: directories with numeric prefixes and slugs (`01.ustanovka`, `02.ekspluatatsiya`, …, `09.rukovodstvo-polzovatelya`). Each section contains its own tree of chapters/subchapters.
- Naming scheme for files: `NNNNNN.slug.md`
  - First two digits: chapter number inside parent.
  - Next four digits: order within the chapter.
  - `slug`: short transliterated name.
- Index files: most directories with multiple items have `0.index.md`; treat it as the first file at that level.
- Recursion pattern:
  1. Start at `content/003.cu/0.index.md`.
  2. Iterate child items in numeric order by directory/file name.
  3. For each directory: include its `0.index.md` (if present) first, then descend into its subdirectories/files in numeric order.
  4. For each `.md` file (excluding `0.index.md`), include it in numeric order alongside siblings.
- Skip: `content/003.cu/doc/*` — contains only directories, no markdown content.
- Total markdown files under `content/003.cu`: 342 (spread across sections 01–09 as counted on 202x-xx-xx).

Image placement and mapping (for bundling)
------------------------------------------

- Image root: `public/images/<doc-slug>/...`, where `<doc-slug>` matches the content folder name without the numeric prefix (e.g., `003.cu` → `cu`, `002.rosa-hrom` → `rosa-hrom`, `004.dynamic-directory` → `dynamic-directory`). Docs without a matching folder have no images (e.g., `010.term-opred`).
- For CU specifically: `public/images/cu/` mirrors the content hierarchy but with numeric prefixes stripped and dots removed, leaving slug-only directories. Example: `content/003.cu/02.ekspluatatsiya/060000.ctrl-uzlam/060500.dobav-uzla-v-grupp.md` uses images from `/images/cu/ekspluatatsiya/ctrl-uzlam/`.
- Folder naming pattern under each doc slug: `<section-slug>/<chapter-slug>/...` where slugs come from the content path elements after removing their numeric prefixes and extensions. There are subfolders as deep as needed to match chapter nesting (e.g., `podsistema-otobrazheniya/panel-i-vizua/setup-porog-znach`).
- Filenames inside these folders are simple counters (`image1.png`, `image2.jpeg`, etc.). Markdown references use absolute paths like `/images/cu/podsistema-otobrazheniya/panel-i-vizua/setup-porog-znach/image95.png`; `data-resource-id` (when present) matches the basename (`image95`).
- In text, два режима ссылок на изображения:
  1) Блоки `::sign-image` с frontmatter `src: /imageNN.png` — путь укорочен, без папок. Его нужно резолвить в ту же папку, что получается по алгоритму соответствия markdown → images (см. выше).
  2) Обычные `<img src="/images/<...>/imageNN.png" ... data-resource-id="imageNN"/>` — уже полные абсолютные пути, data-resource-id совпадает с именем файла.
- Other document sets follow the same pattern: `public/images/rosa-hrom/*`, `public/images/rosa-virt/*`, `public/images/rosa-kubis/*`, etc., mirroring their respective `content/NNN.<slug>` structures but without numbers. Some sets have extra variant levels (e.g., `public/images/rosa-hrom/cert/ustanovka`, `.../nocert/ekspluatatsiya`) that correspond to sibling sections in content.
- For bundling: given a markdown file path, derive its image folder by (1) taking the doc slug (content folder without numeric prefix), (2) dropping numeric prefixes from each ancestor directory and the file’s own numeric stem, and (3) concatenating these slugs under `/images/<doc-slug>/...`. Use this to rewrite or validate image links.
