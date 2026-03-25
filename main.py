import re
import os
import shutil
from datetime import datetime


# --- Класс статистики ---

class Stats:
    def __init__(self):
        self.added = 0
        self.modified = 0
        self.removed = 0
        self.green = 0
        self.total = 0

    def __str__(self):
        return (
            f"Добавлено: {self.added}, "
            f"Изменено: {self.modified}, "
            f"Удалено: {self.removed}\n"
            f"Отпатрулировано: {self.green} статей из {self.total}"
        )


# --- Парсинг таблицы ---

def split_table(text):
    lines = text.strip().splitlines()
    header, rows = [], []
    current = []
    in_rows = False

    for line in lines:
        if line.startswith("|-"):
            in_rows = True
            if current:
                rows.append("\n".join(current))
            current = [line]
        elif in_rows:
            current.append(line)
        else:
            header.append(line)

    if current:
        rows.append("\n".join(current))

    return "\n".join(header), rows


def extract_title(row):
    m = re.search(r"\[\[(.*?)\]\]", row)
    return m.group(1).strip() if m else None


def split_cells(row):
    body = row.split("\n", 1)[1]
    return body.split("||")


def join_row(style, cells):
    return style + "\n" + "||".join(cells)


# --- Поля для сортировки ---

def extract_unreviewed(row):
    cells = split_cells(row)
    nums = re.findall(r"\d+", cells[1]) if len(cells) > 1 else []
    return int(nums[0]) if nums else 0


def extract_fp_stable(row):
    return not ("Никогда" in row)


def extract_last_review(row):
    m = re.search(r"\d{4}-\d{2}-\d{2}", row)
    return m.group(0) if m else "9999-99-99"


# --- Логика изменений ---

def update_row(row1, row2):
    row1 = remove_yellow_style(row1)
    cells1 = split_cells(row1)
    cells2 = split_cells(row2)

    changed = False
    # проверяем изменения в unreviewed_count и статус
    if len(cells1) > 1 and len(cells2) > 1 and cells1[1] != cells2[1]:
        cells1[1] = cells2[1]
        changed = True
    if len(cells1) > 2 and len(cells2) > 2 and cells1[2] != cells2[2]:
        cells1[2] = cells2[2]
        changed = True

    style = row1.split("\n", 1)[0]
    return join_row(style, cells1), changed


def mark_green(row):
    cells = split_cells(row)

    # защита от двойного <s>
    if "<s>" not in cells[0]:
        cells[0] = re.sub(r"\[\[(.*?)\]\]", r"<s>[[\1]]</s>", cells[0])

    if len(cells) > 2:
        cells[2] = "{{done|Отпатрулирована}}"

    return '|- style="background:#d0f0c0;"\n' + "||".join(cells)


def mark_yellow(row):
    cells = split_cells(row)
    return '|- style="background:#fff3cd;"\n' + "||".join(cells)

def remove_yellow_style(row):
    lines = row.split("\n", 1)
    style_line = lines[0]

    # убираем только жёлтый цвет
    if "#fff3cd" in style_line:
        style_line = "|-"

    return style_line + "\n" + lines[1]

# --- Основная обработка ---
def process(t1, quarry_texts):
    header, rows1 = split_table(t1)

    dict1 = {extract_title(r): r for r in rows1 if extract_title(r)}
    dict2 = {}
    for text in quarry_texts:
        _, rows2 = split_table(text)
        for r in rows2:
            title = extract_title(r)
            if title:
                dict2[title] = r

    result = []
    stats = Stats()

    for title, row1 in dict1.items():
        if title in dict2:
            updated_row, changed = update_row(row1, dict2[title])
            result.append(updated_row)
            if changed:
                stats.modified += 1
        else:
            stats.green += 1
            # только в первой → зелёный
            if "{{done" in row1 or "#d0f0c0" in row1:
                result.append(row1)
            elif not "❌ Никогда" in row1:
                # помечаем проверенным
                result.append(mark_green(row1))
                stats.modified += 1
            else:
                # удаляем из списка
                stats.removed += 1

    for title, row2 in dict2.items():
        if title not in dict1:
            # только во второй → жёлтый
            result.append(mark_yellow(row2))
            stats.added += 1

    # сортировка
    result.sort(key=lambda r: (
        extract_unreviewed(r),
        extract_fp_stable(r),
        extract_title(r) or "",
        extract_last_review(r)
    ))

    stats.total = len(result)

    return header + "\n" + "\n".join(result) + "\n", stats

# --- Ограничение размера бэкапов ---

def enforce_backup_limit(folder, max_bytes):
    files = []

    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            files.append((path, os.path.getmtime(path), os.path.getsize(path)))

    # сортируем по времени (старые → первые)
    files.sort(key=lambda x: x[1])

    total_size = sum(f[2] for f in files)

    while total_size > max_bytes and files:
        path, _, size = files.pop(0)
        os.remove(path)
        print(f"Deleted old backup: {path}")
        total_size -= size


# --- Запуск ---

if __name__ == "__main__":
    file1 = "patrol_data.wikitable"
    quarry_folder = os.path.dirname(os.path.abspath(__file__))

    # 📁 создаём папку backups
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    # 🕒 имя бэкапа
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        backup_dir,
        f"patrol_data.wikitable.bak_{timestamp}"
    )

    # 💾 сохраняем бэкап
    shutil.copy(file1, backup_path)
    print(f"Backup created: {backup_path}")

    # 🧹 ограничиваем размер папки бэкапов (10 MB)
    enforce_backup_limit(backup_dir, 10 * 1024 * 1024)

    # 📖 читаем файлы
    with open(file1, encoding="utf-8") as f:
        t1 = f.read()

    # читаем все quarry*.wikitable файлы
    quarry_files = []
    for root, _, files in os.walk(quarry_folder):
        for filename in files:
            if re.fullmatch(r"quarry.*\.wikitable", filename):
                path = os.path.join(root, filename)
                with open(path, encoding="utf-8") as f:
                    quarry_files.append(f.read())

    # ⚙️ обработка
    result, stats = process(t1, quarry_files)

    # ✍️ перезапись
    with open(file1, "w", encoding="utf-8") as f:
        f.write(result)

    print("Done ✅")
    print(stats)