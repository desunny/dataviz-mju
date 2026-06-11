#!/usr/bin/env python3
"""
학생 작품 파일을 익명 코드로 변환하고 매핑표(roster.csv)를 만든다.

- '학번_이름.html' → '01.html', '02.html' ... (반 내 학번 오름차순 순번)
- roster.csv: code,year,class,student_id,name (코드↔실명 매핑, 비공개)

이미 익명 코드로 바뀐 파일은 건너뛴다(재실행 안전).
roster.csv가 이미 있으면 기존 코드 매핑을 보존하고 신규 학생만 이어붙인다.

사용법:
    python3 anonymize.py
"""

import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROSTER = ROOT / "roster.csv"
ORIG_RE = re.compile(r"^(\d+)_(.+)$")   # 학번_이름


def load_roster():
    rows = []
    if ROSTER.exists():
        with ROSTER.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return rows


def main():
    roster = load_roster()
    # 이미 매핑된 (year,class,student_id) 집합
    seen = {(r["year"], r["class"], r["student_id"]) for r in roster}
    # 반별 기존 최대 순번
    maxnum = {}
    for r in roster:
        key = (r["year"], r["class"])
        n = int(r["code"])
        maxnum[key] = max(maxnum.get(key, 0), n)

    new_rows = []
    for year_dir in sorted(ROOT.iterdir()):
        if not (year_dir.is_dir() and re.fullmatch(r"\d{4}", year_dir.name)):
            continue
        for class_dir in sorted(year_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            key = (year_dir.name, class_dir.name)
            # 원본 형식(학번_이름)만 대상, 학번 오름차순
            originals = []
            for f in class_dir.glob("*.html"):
                stem = unicodedata.normalize("NFC", f.stem)
                m = ORIG_RE.match(stem)
                if m:
                    originals.append((m.group(1), m.group(2).strip(), f))
            originals.sort(key=lambda t: t[0])
            for sid, name, f in originals:
                if (year_dir.name, class_dir.name, sid) in seen:
                    continue
                num = maxnum.get(key, 0) + 1
                maxnum[key] = num
                code = f"{num:02d}"
                target = class_dir / f"{code}.html"
                if target.exists():
                    print(f"⚠️  건너뜀(이미 존재): {target}")
                    continue
                f.rename(target)
                new_rows.append({
                    "code": code, "year": year_dir.name, "class": class_dir.name,
                    "student_id": sid, "name": name,
                })
                print(f"  {year_dir.name}/{class_dir.name}: {sid}_{name} → {code}.html")

    if not new_rows:
        print("변경할 원본 파일이 없습니다 (이미 익명화됨).")
        return

    roster.extend(new_rows)
    roster.sort(key=lambda r: (r["year"], r["class"], r["code"]))
    with ROSTER.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "year", "class", "student_id", "name"])
        w.writeheader()
        w.writerows(roster)
    print(f"\n✅ {len(new_rows)}개 파일 익명화, roster.csv 갱신 (총 {len(roster)}명)")


if __name__ == "__main__":
    main()
