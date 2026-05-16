import os
import re
import math
from datetime import datetime, timedelta

MONTH_FOLDERS = {
    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
    9: 'Sep', 10: 'Oct', 11: 'Nov',
}

ORDINAL_TO_NUM = {'첫째주': 1, '둘째주': 2, '셋째주': 3, '넷째주': 4, '다섯째주': 5}
HEADER_RE = re.compile(r'^### \[(\d+)월 ([가-힣]+째주), \d+주차\]')


def get_section_key(date):
    # Each entry belongs to the section of its ISO week's Monday.
    # This keeps Mon–Fri of the same bootcamp week in one section,
    # even when the week spans two calendar months.
    monday = date - timedelta(days=date.weekday())
    week_ordinal = math.ceil(monday.day / 7)
    return (monday.month, week_ordinal)


def get_subtitle(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('## 소제목:'):
                subtitle = line.replace('## 소제목:', '').strip()
                return subtitle if subtitle else None
    return None


def collect_entries():
    entries = {}

    for folder in MONTH_FOLDERS.values():
        if not os.path.isdir(folder):
            continue
        for filename in os.listdir(folder):
            if filename == 'template.md' or not filename.endswith('.md'):
                continue
            try:
                date = datetime.strptime(filename[:-3], '%Y-%m-%d')
            except ValueError:
                continue
            subtitle = get_subtitle(os.path.join(folder, filename))
            if not subtitle:
                continue
            key = get_section_key(date)
            entries.setdefault(key, []).append((date, subtitle, f'{folder}/{filename}'))

    for key in entries:
        entries[key].sort(key=lambda x: x[0], reverse=True)

    return entries


def update_readme(entries):
    with open('README.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = HEADER_RE.match(line)

        if m:
            month_num = int(m.group(1))
            week_ordinal = ORDINAL_TO_NUM.get(m.group(2), 0)
            key = (month_num, week_ordinal)

            new_lines.append(line)
            i += 1

            # Skip all existing content until the next section header or separator
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('### ') or s == '---':
                    break
                i += 1

            # Insert fresh entries for this section
            section_entries = entries.get(key, [])
            if section_entries:
                new_lines.append('\n')
                for date, subtitle, filepath in section_entries:
                    date_str = date.strftime('%y.%m.%d')
                    new_lines.append(f'- [x] [{date_str}]({filepath}) - [ {subtitle} ]\n')
            new_lines.append('\n')
        else:
            new_lines.append(line)
            i += 1

    with open('README.md', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


if __name__ == '__main__':
    entries = collect_entries()
    update_readme(entries)
    total = sum(len(v) for v in entries.values())
    print(f'README updated with {total} entries.')
