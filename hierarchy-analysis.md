Summary of the Markdown hierarchy in `content/*` (for bundling)
---------------------------------------------------------------

- Документные наборы сейчас:  
  - `000.dev` (5 md, нет `0.index.md`, лаборатория/примеры, есть вложенные каталоги без числовых префиксов).  
  - `001.dev-portal-user` (14 md, нет корневого `0.index.md`, внутри встречается `index.md` без цифрового префикса и `.navigation.yml`).  
  - `002.rosa-hrom` (423 md, корневой `0.index.md`, две ветки `1.cert` и `2.nocert`, далее 6-значные префиксы).  
  - `003.cu` (373 md, корневой `0.index.md`, классическая схема с `01.*` каталогами и `NNNNNN.slug.md`).  
  - `004.dynamic-directory` (92 md, корневой `0.index.md`).  
  - `005.rosa-virt` (266 md, корневой `0.index.md`).  
  - `006.rosa-barii` (33 md, корневой `0.index.md`).  
  - `007.rosa-migration` (109 md, корневой `0.index.md`).  
  - `008.rosa-kubis` (77 md, корневой `0.index.md`).  
  - `009.rosa-resource-manager` (88 md, корневой `0.index.md`).  
  - `010.term-opred` (1 md, без `0.index.md`).

Правила обхода и сортировки описаны в `architecture.md` (раздел «Инварианты структуры контента»); этот файл держим как срез текущего содержимого и исключений.

Index vs `.navigation.yml`
--------------------------

- `0.index.md` кладут там, где раздел содержит вводный текст (сейчас 169 таких файлов, большинство непустые).
- Если у раздела только заголовок без тела, вместо `0.index.md` используют `.navigation.yml` с полем `title` (195 каталогов с навигацией и без индекса).
- Корневые наборы держат пустые `0.index.md` вместе с `.navigation.yml` (cu, rosa-hrom, dynamic-directory, rosa-virt, rosa-barii, rosa-kubis, rosa-migration, rosa-resource-manager).
- Почти все каталоги с markdown содержимым имеют либо индекс, либо `.navigation.yml`; исключения только `content/000.dev/001.components` и `content/003.cu/01.ustanovka/000000.service`.

Image placement and mapping — см. `architecture.md` (раздел «Инварианты структуры контента»).
