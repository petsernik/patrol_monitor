import re
import os
import shutil
from datetime import datetime

_recent_backup_sets = []


def build_recent_backup_sets(hours=48):
    global _recent_backup_sets

    now = datetime.now().timestamp()
    limit = hours * 3600

    sets = []

    for name in os.listdir(backup_dir):
        path = os.path.join(backup_dir, name)
        if not os.path.isfile(path):
            continue

        mtime = os.path.getmtime(path)
        if now - mtime > limit:
            continue

        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except:
            continue

        _, rows = split_table(text)

        s = set()
        for r in rows:
            if r.title:
                s.add(r.title)

        sets.append(s)

    _recent_backup_sets = sets


# --- Statistics class ---

class Stats:
    def __init__(self):
        self.added = 0
        self.modified = 0
        self.removed = 0
        self.green = 0
        self.total = 0

    def __str__(self):
        return (
            f"Added: {self.added}, Changed: {self.modified}, Deleted: {self.removed}\n"
            f"Patrolled: {self.green}, Total: {self.total}"
        )


# --- Table parsing ---

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


# --- Fields for sorting ---

def extract_unreviewed(row):
    cells = split_cells(row)
    nums = re.findall(r"\d+", cells[1]) if len(cells) > 1 else []
    return int(nums[0]) if nums else 0


def extract_fp_stable(row):
    return not ("❌ Никогда" in row)


def extract_last_review(row):
    m = re.search(r"\d{4}-\d{2}-\d{2}", row)
    return m.group(0) if m else "9999-99-99"


# --- Change logic ---

def missing_in_some_recent_backup(title):
    # missing in at least one of the recent backups
    return any(title not in s for s in _recent_backup_sets)


def update_row(row1, row2, title):
    row1 = remove_yellow_style_if_old(row1, title)
    cells1 = split_cells(row1)
    cells2 = split_cells(row2)

    changed = False
    # check changes in unreviewed_count and status
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

    # protect against double <s>
    if "<s>" not in cells[0]:
        cells[0] = re.sub(r"\[\[(.*?)\]\]", r"<s>[[\1]]</s>", cells[0])

    if len(cells) > 2:
        cells[2] = "{{done|Отпатрулирована*}}"

    return '|- style="background:#d0f0c0;"\n' + "||".join(cells)


def mark_yellow(row):
    cells = split_cells(row)
    return '|- style="background:#fff3cd;"\n' + "||".join(cells)


def remove_yellow_style_if_old(row, title):
    lines = row.split("\n", 1)
    style_line = lines[0]

    # remove only yellow color
    if "#fff3cd" in style_line:
        # remove yellow ONLY if it was present in ALL backups
        if not missing_in_some_recent_backup(title):
            style_line = "|-"

    return style_line + "\n" + lines[1]


# --- Main processing ---

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
            updated_row, changed = update_row(row1, dict2[title], title)
            result.append(updated_row)
            if changed:
                stats.modified += 1
        else:
            stats.green += 1
            # only in the first → green
            if "{{done" in row1 or "#d0f0c0" in row1:
                # mark as patrolled
                result.append(mark_green(row1))
            elif not "❌ Никогда" in row1:
                # mark as patrolled
                result.append(mark_green(row1))
                stats.modified += 1
            else:
                # remove from the list
                stats.removed += 1

    for title, row2 in dict2.items():
        if title not in dict1:
            # only in the second → yellow
            result.append(mark_yellow(row2))
            stats.added += 1

    # sorting
    result.sort(key=lambda r: (
        extract_unreviewed(r),
        extract_fp_stable(r),
        extract_title(r) or "",
        extract_last_review(r)
    ))

    stats.total = len(result)

    return header + "\n" + "\n".join(result) + "\n", stats


# --- Backup folder size limit ---

def enforce_folder_limit(folder, max_bytes):
    files = []

    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            files.append((path, os.path.getmtime(path), os.path.getsize(path)))

    # sort by time (oldest first)
    files.sort(key=lambda x: x[1])

    total_size = sum(f[2] for f in files)

    while total_size > max_bytes and files:
        path, _, size = files.pop(0)
        os.remove(path)
        print(f"Deleted old backup: {path}")
        total_size -= size


# --- Execution ---

if __name__ == "__main__":
    file1 = "patrol_data.wikitable"
    quarry_folder = os.path.dirname(os.path.abspath(__file__))

    # 📁 create backups folder
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    # 🕒 backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        backup_dir,
        f"patrol_data.wikitable.bak_{timestamp}"
    )

    # 💾 save backup
    shutil.copy(file1, backup_path)
    print(f"Backup created: {backup_path}")

    # cache recent backups
    build_recent_backup_sets()

    # 🧹 limit backup folder size (10 MB)
    enforce_folder_limit(backup_dir, 10 * 1024 * 1024)

    # 📖 read files
    with open(file1, encoding="utf-8") as f:
        t1 = f.read()

    # read all quarry*.wikitable files
    quarry_files = []
    for root, _, files in os.walk(quarry_folder):
        for filename in files:
            if re.fullmatch(r"quarry.*\.wikitable", filename):
                path = os.path.join(root, filename)
                with open(path, encoding="utf-8") as f:
                    quarry_files.append(f.read())

    # ⚙️ processing
    result, stats = process(t1, quarry_files)

    # ✍️ overwrite
    with open(file1, "w", encoding="utf-8") as f:
        f.write(result)

    print("Done ✅")
    print(stats)
