# patrol_monitor
[Go to english description](#English-description)  

Программа обновляет таблицы для патрулирующих, (почти всегда) не удаляя старые строки.
Новые строки отмечаются жёлтым цветом (жёлтый исчезает через 48 часов).
Изменённые строки временно отмечаются оранжевым (если значение стабильно — цвет исчезает).
Проверенные помечаются зелёным (и надписи в тексте обновляются).

Поддерживается обработка нескольких таблиц:

* **независимо** (independent)
* **последовательно с исключением пересечений** (dependent)

Вдохновлена предложениями википедиста [Ailbeve](https://ru.wikipedia.org/wiki/Участник:Ailbeve)
(см. [обсуждение](https://ru.wikipedia.org/w/index.php?title=Обсуждение_Википедии:Запросы_к_патрулирующим#Периодически_проверять/публиковать_статьи_на_которые_ссылаются_правила)),
опирается на запросы в [Quarry](https://quarry.wmcloud.org).

---

## Как использовать

1. Откройте запрос, например:
   [https://quarry.wmcloud.org/query/103590](https://quarry.wmcloud.org/query/103590)

2. Сделайте fork и запустите его.

3. Скачайте результат:
   **Download Data → wikitable**

4. Поместите файл в репозиторий и переименуйте его в:

```
patrol-data-XXXX.wikitable
```

где `XXXX` — ID запроса (например, `103590`)

5. После обновления Quarry:

   * скачайте новый файл
   * переместите его в папку (без переименования)

6. Запустите скрипт:

Один файл

```
python script.py independent 103590
```

Несколько файлов (независимо)

```
python script.py independent 103590 103591
```

Несколько файлов (зависимо)

```
python script.py dependent 103590 103591 103592
```

---

## Режимы работы

### Independent

Каждый файл обновляется **независимо**:

* данные не влияют друг на друга
* удобно для отдельных списков

### Dependent

Файлы обрабатываются **последовательно**:

* сначала обновляется первый файл
* его заголовки исключаются из второго, второй обновляется
* затем объединение исключается из третьего, третий обновляется и т.д.

Это позволяет:

* избегать дублирования между списками
* строить приоритетные цепочки

---

# English description

The program updates patrolling tables (almost always) without removing old rows.

* New rows are highlighted in yellow (the color fades after 48 hours)
* Changed rows are temporarily marked orange (removed when stable)
* Reviewed entries are marked green (and text labels are updated)

Supports processing multiple tables:

* independent mode
* dependent mode (with deduplication across files)

Inspired by suggestions from Wikipedian [Ailbeve](https://ru.wikipedia.org/wiki/Участник:Ailbeve)
(see [discussion](https://ru.wikipedia.org/w/index.php?title=Обсуждение_Википедии:Запросы_к_патрулирующим#Периодически_проверять/публиковать_статьи_на_которые_ссылаются_правила))
and based on queries in Quarry: [https://quarry.wmcloud.org](https://quarry.wmcloud.org).

---

## Usage

1. Open a query, for example:
   [https://quarry.wmcloud.org/query/103590](https://quarry.wmcloud.org/query/103590)

2. Fork and run it.

3. Download the result:
   Download Data → wikitable

4. Copy the file into the repository and rename it to:

```
patrol-data-XXXX.wikitable
```

where `XXXX` is the query ID (e.g. 103590)

5. When Quarry output updates:

   * download the new version
   * move the file in the folder (without renaming)

6. Run the script:

Single file

```
python script.py independent 103590
```

Multiple files (independent)

```
python script.py independent 103590 103591
```

Multiple files (dependent)

```
python script.py dependent 103590 103591 103592
```

---

## Modes

### Independent

Each file is processed separately:

* no interaction between files
* useful for standalone lists

### Dependent

Files are processed in sequence:

* first file is updated
* its titles are removed from the second, second file is updated
* combined titles are removed from the third, third file is updated, etc.

This allows:

* avoiding duplicates across lists
* building priority chains
