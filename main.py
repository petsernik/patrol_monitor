import re
import os
import shutil
import sys
from datetime import datetime

_recent_backup_sets = []
_recent_unreviewed = []


def build_recent_backup_sets(patrol_file, hours=48):
    global _recent_backup_sets, _recent_unreviewed

    now = datetime.now().timestamp()
    limit = hours * 3600

    sets = []
    unreviewed_sets = []

    for name in os.listdir(backup_dir):
        m = re.fullmatch(rf"{re.escape(patrol_file)}\.bak_\d{{8}}_\d{{6}}", name)
        if not m:
            continue

        path = os.path.join(backup_dir, name)
        if not os.path.isfile(path):
            continue

        mtime = os.path.getmtime(path)
        if now - mtime > limit:
            continue

        try:
            with open(path, encoding="utf-8") as f:
                text = normalize_spaces(f.read())
        except:
            continue

        _, rows = split_table(text)

        titles = set()
        values = {}

        for r in rows:
            t = extract_title(r)
            if not t:
                continue

            titles.add(t)
            values[t] = extract_unreviewed(r)

        sets.append(titles)
        unreviewed_sets.append(values)

    _recent_backup_sets = sets
    _recent_unreviewed = unreviewed_sets


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

    # added helper for summation
    def add(self, other):
        self.added += other.added
        self.modified += other.modified
        self.removed += other.removed
        self.green += other.green
        self.total += other.total


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

def missing_title_in_some_recent_backup(title):
    return any(title not in s for s in _recent_backup_sets)


def was_unreviewed_stable(title, current_value):
    for d in _recent_unreviewed:
        if title in d and d[title] != current_value:
            return False
    return True


def update_row(row1, row2, title):
    cells1 = split_cells(row1)
    cells2 = split_cells(row2)

    changed = False
    if len(cells1) > 1 and len(cells2) > 1 and cells1[1] != cells2[1]:
        cells1[1] = cells2[1]
        changed = True
    if len(cells1) > 2 and len(cells2) > 2 and cells1[2] != cells2[2]:
        cells1[2] = cells2[2]
        changed = True
    if changed:
        row1 = mark_orange(row1)
    else:
        row1 = remove_yellow_if_old(row1, title)
        row1 = remove_orange_if_stable(row1, title)
    style = row1.split("\n", 1)[0]
    return join_row(style, cells1), changed


def mark_green(row):
    cells = split_cells(row)

    if "<s>" not in cells[0]:
        cells[0] = re.sub(r"\[\[(.*?)\]\]", r"<s>[[\1]]</s>", cells[0])

    if len(cells) > 2:
        cells[2] = "{{done|Отпатрулирована*}}"

    return '|- style="background:#d0f0c0;"\n' + "||".join(cells)


def mark_yellow(row):
    cells = split_cells(row)
    return '|- style="background:#fff3cd;"\n' + "||".join(cells)


def mark_orange(row):
    cells = split_cells(row)
    return '|- style="background:#ffcc80;"\n' + "||".join(cells)


def remove_orange_if_stable(row, title):
    lines = row.split("\n", 1)
    style_line = lines[0]

    if "#ffcc80" in style_line:
        if was_unreviewed_stable(title, extract_unreviewed(row)):
            style_line = "|-"

    return style_line + "\n" + lines[1]


def remove_yellow_if_old(row, title):
    lines = row.split("\n", 1)
    style_line = lines[0]

    if "#fff3cd" in style_line:
        if not missing_title_in_some_recent_backup(title):
            style_line = "|-"

    return style_line + "\n" + lines[1]


# --- Main processing ---

def remove_rows_present_in_other(text1: str, text2: str) -> tuple[str, int]:
    if not text2:
        return text1, 0

    header1, rows1 = split_table(text1)
    _, rows2 = split_table(text2)

    titles2 = set()
    for r in rows2:
        t = extract_title(r)
        if t:
            titles2.add(t)

    filtered_rows = []
    _removed = 0
    for r in rows1:
        t = extract_title(r)
        if not t or t not in titles2:
            filtered_rows.append(r)
        else:
            _removed += 1

    return header1 + "\n" + "\n".join(filtered_rows) + "\n", _removed


def process(t1: str, quarry: str) -> tuple[str, Stats]:
    header, rows1 = split_table(t1)

    dict1 = {extract_title(r): r for r in rows1 if extract_title(r)}
    dict2 = {}
    _, rows2 = split_table(quarry)
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
            if "{{done" in updated_row or "#d0f0c0" in updated_row:
                stats.green += 1
        else:
            stats.green += 1
            if "{{done" in row1 or "#d0f0c0" in row1:
                result.append(mark_green(row1))
            elif not "❌ Никогда" in row1:
                result.append(mark_green(row1))
                stats.modified += 1
            else:
                stats.removed += 1

    for title, row2 in dict2.items():
        if title not in dict1:
            result.append(mark_yellow(row2))
            stats.added += 1

    result.sort(key=lambda r: (
        extract_unreviewed(r),
        extract_fp_stable(r),
        extract_title(r) or "",
        extract_last_review(r)
    ))

    stats.total = len(result)

    return header + "\n" + "\n".join(result) + "\n", stats


def process_single_file(patrol_file, latest_quarries):
    m = re.fullmatch(r"patrol-data-(\d+)\.wikitable", patrol_file)
    if not m:
        raise ValueError(f"Invalid patrol file: {patrol_file}")

    patrol_id = m.group(1)

    if patrol_id not in latest_quarries:
        raise FileNotFoundError(f"No quarry found for patrol id {patrol_id}")

    run, selected_path = latest_quarries[patrol_id]
    print(f"[LOG] Processing {patrol_file} with quarry run={run}")

    with open(patrol_file, encoding="utf-8") as f:
        t1 = normalize_spaces(f.read())

    with open(selected_path, encoding="utf-8") as f:
        quarry_text = normalize_spaces(f.read())

    result, stats = process(t1, quarry_text)

    with open(patrol_file, "w", encoding="utf-8") as f:
        f.write(result)

    _, rows = split_table(result)
    titles = {extract_title(r) for r in rows if extract_title(r)}

    return stats, titles


def independent_process(*files):
    all_quarry_paths, latest_quarries = get_quarries()

    total_stats = Stats()

    for f in files:
        # validate
        patrol_file = normalize_patrol_filename(f)
        if not os.path.exists(patrol_file):
            raise FileNotFoundError(patrol_file)

        # build cache
        build_recent_backup_sets(patrol_file)

        # processing
        stats, _ = process_single_file(patrol_file, latest_quarries)
        total_stats.add(stats)

    return total_stats


def dependent_process(*files):
    all_quarry_paths, latest_quarries = get_quarries()

    total_stats = Stats()
    accumulated_titles = set()

    for f in files:
        patrol_file = normalize_patrol_filename(f)

        if not os.path.exists(patrol_file):
            raise FileNotFoundError(patrol_file)

        with open(patrol_file, encoding="utf-8") as f1:
            t1 = normalize_spaces(f1.read())

        if accumulated_titles:
            header, rows = split_table(t1)
            filtered_rows = []

            for r in rows:
                title = extract_title(r)
                if not title or title not in accumulated_titles:
                    filtered_rows.append(r)

            t1 = header + "\n" + "\n".join(filtered_rows) + "\n"

        m = re.fullmatch(r"patrol-data-(\d+)\.wikitable", patrol_file)
        patrol_id = m.group(1)

        if patrol_id not in latest_quarries:
            raise FileNotFoundError(f"No quarry for {patrol_id}")

        run, selected_path = latest_quarries[patrol_id]

        with open(selected_path, encoding="utf-8") as f:
            quarry_text = normalize_spaces(f.read())

        # build cache
        build_recent_backup_sets(patrol_file)

        # processing
        result, stats = process(t1, quarry_text)

        with open(patrol_file, "w", encoding="utf-8") as f:
            f.write(result)

        _, rows = split_table(result)
        for r in rows:
            title = extract_title(r)
            if title:
                accumulated_titles.add(title)

        total_stats.add(stats)

    return total_stats


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
        print(f"Deleted old file: {path}")
        total_size -= size


# --- Execution ---

def get_quarries():
    quarry_pattern = re.compile(r"quarry-(\d+)-.*-run(\d+)\.wikitable")

    latest_quarries = {}  # {id: (run, path)}
    all_quarry_paths = []

    for filename in os.listdir(quarry_folder):
        m = quarry_pattern.fullmatch(filename)
        if not m:
            continue

        qid = m.group(1)
        run = int(m.group(2))
        path = os.path.join(quarry_folder, filename)

        all_quarry_paths.append(path)

        if qid not in latest_quarries or run > latest_quarries[qid][0]:
            latest_quarries[qid] = (run, path)

    return all_quarry_paths, latest_quarries


def normalize_patrol_filename(value: str) -> str:
    if re.fullmatch(r"\d+", value):
        return f"patrol-data-{value}.wikitable"

    if re.fullmatch(r"patrol-data-\d+\.wikitable", value):
        return value

    raise ValueError(
        f"Invalid patrol_data_file: {value}\n"
        f"Expected either ID (e.g. 103623) or filename patrol-data-XXXX.wikitable"
    )


def normalize_spaces(text: str) -> str:
    """
    Normalize all whitespace except newlines:
    - Tabs, non-breaking spaces, etc. → regular space
    - Collapse multiple spaces into one
    - Keep line breaks (\n) as is
    - Strip leading/trailing spaces per line
    """
    text = re.sub(r'[^\S\n]+', ' ', text, flags=re.UNICODE)
    text = re.sub(r' +', ' ', text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines)


if __name__ == "__main__":
    # usage:
    # python script.py dependent 103623 103604
    # python script.py independent 103623 103604

    if len(sys.argv) < 3:
        raise ValueError(
            "Usage:\n"
            "  script.py dependent <files...>\n"
            "  script.py independent <files...>"
        )

    mode = sys.argv[1]
    raw_files = sys.argv[2:]

    patrol_files = []
    for rf in raw_files:
        pf = normalize_patrol_filename(rf)

        if not os.path.exists(pf):
            raise FileNotFoundError(pf)

        if pf.startswith("quarry"):
            raise ValueError("Patrol data files must not start with 'quarry'")

        patrol_files.append(pf)

    quarry_folder = os.path.dirname(os.path.abspath(__file__))

    # 📁 create folders
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    quarries_dir = "quarries"
    os.makedirs(quarries_dir, exist_ok=True)

    # 🕒 create backups for all patrol files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for pf in patrol_files:
        backup_path = os.path.join(
            backup_dir,
            f"{pf}.bak_{timestamp}"
        )
        shutil.copy(pf, backup_path)
        print(f"Backup created: {backup_path}")

    # ⚙️ processing
    if mode == "independent":
        stats = independent_process(*patrol_files)
    elif mode == "dependent":
        stats = dependent_process(*patrol_files)
    else:
        raise ValueError("Mode must be 'independent' or 'dependent'")

    # 📦 move ALL quarry files
    all_quarry_paths, _ = get_quarries()

    for path in all_quarry_paths:
        try:
            filename = os.path.basename(path)
            new_path = os.path.join(quarries_dir, filename)

            shutil.move(path, new_path)
            print(f"Moved: {path} -> {new_path}")
        except Exception as e:
            print(f"Failed to move {path}: {e}")

    # 🧹 limit folders
    enforce_folder_limit(backup_dir, 50 * 1024 * 1024)
    enforce_folder_limit(quarries_dir, 50 * 1024 * 1024)

    print("Done ✅")
    print(stats)
