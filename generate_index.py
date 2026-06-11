#!/usr/bin/env python3
"""
명지대 융합데이터 시각화 - 포트폴리오 인덱스 생성기

roster.csv(코드↔실명 매핑, 비공개)를 읽어 첫 화면 index.html을 만든다.
공개 페이지에는 마스킹된 학번/이름만 들어가고, 링크는 익명 코드를 가리킨다.

  학번:  60210230  →  6021○○○○   (뒤 4자리 마스킹)
  이름:  정우영      →  정○영       (가운데 마스킹)
  링크:  2026/12/04.html            (익명 코드)

사용법:
    python3 anonymize.py        # 새 원본 파일 → 익명 코드 + roster.csv 갱신
    python3 generate_index.py   # roster.csv → index.html 생성
"""

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROSTER = ROOT / "roster.csv"
CLASS_LABELS = {"12": "12시 수업", "15": "15시 수업"}
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def mask_id(sid: str) -> str:
    """학번 뒤 4자리를 마스킹: 60210230 → 6021○○○○"""
    if len(sid) <= 4:
        return sid
    return sid[:-4] + "○" * 4


def mask_name(name: str) -> str:
    """이름 가운데를 마스킹: 정우영→정○영, 홍길→홍○, 남궁민수→남○○수"""
    name = name.strip()
    n = len(name)
    if n <= 1:
        return name
    if n == 2:
        return name[0] + "○"
    return name[0] + "○" * (n - 2) + name[-1]


def extract_title(path: Path) -> str:
    """HTML <title> 추출 (없으면 빈 문자열). 대용량 파일도 앞부분만 읽음."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            head = f.read(8192)
        m = TITLE_RE.search(head)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    except OSError:
        pass
    return ""


def scan():
    """roster.csv → {year: {class: [ {id, name, title, href} ]}} (마스킹 적용)."""
    if not ROSTER.exists():
        raise SystemExit("⚠️  roster.csv가 없습니다. 먼저 'python3 anonymize.py'를 실행하세요.")
    data = {}
    with ROSTER.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: (r["year"], r["class"], r["code"]))
    for r in rows:
        year, cls, code = r["year"], r["class"], r["code"]
        href = f"{year}/{cls}/{code}.html"
        path = ROOT / href
        data.setdefault(year, {}).setdefault(cls, []).append({
            "id": mask_id(r["student_id"]),
            "name": mask_name(r["name"]),
            "title": extract_title(path) if path.exists() else "",
            "href": href,
        })
    return data


def render(data) -> str:
    cards_by_group = []
    years = list(data.keys())
    for year in years:
        for class_name, students in data[year].items():
            label = CLASS_LABELS.get(class_name, f"{class_name}반")
            group_id = f"{year}-{class_name}"
            cards = []
            for s in students:
                name = html.escape(s["name"])
                sid = html.escape(s["id"])
                title = html.escape(s["title"]) if s["title"] else "데이터 시각화 작품"
                href = html.escape(s["href"])
                cards.append(f"""        <a class="card" href="{href}" target="_blank" rel="noopener"
           data-name="{name}" data-id="{sid}" data-title="{title}">
          <div class="card-title">{title}</div>
          <div class="card-meta"><span class="name">{name}</span><span class="sid">{sid}</span></div>
        </a>""")
            cards_by_group.append({
                "group_id": group_id,
                "year": year,
                "label": label,
                "count": len(students),
                "cards": "\n".join(cards),
            })

    tabs = "\n".join(
        f'        <button class="tab" data-target="{g["group_id"]}">'
        f'{g["year"]} · {g["label"]} <span class="badge">{g["count"]}</span></button>'
        for g in cards_by_group
    )
    panels = "\n".join(
        f'      <section class="panel" id="{g["group_id"]}">\n'
        f'        <div class="grid">\n{g["cards"]}\n        </div>\n      </section>'
        for g in cards_by_group
    )
    total = sum(g["count"] for g in cards_by_group)

    return TEMPLATE.format(tabs=tabs, panels=panels, total=total)


TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>융합데이터 시각화 · 학생 포트폴리오</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0b1020;--panel:#11182e;--card:#1a2440;--card-h:#243156;--line:#2a3658;--text:#e8ecf6;--muted:#8b97b8;--accent:#6ea8ff}}
body{{font-family:'IBM Plex Sans KR',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.5}}
.hero{{padding:64px 24px 32px;text-align:center;background:radial-gradient(900px 400px at 50% -10%,rgba(110,168,255,.18),transparent)}}
.hero h1{{font-size:clamp(26px,4vw,42px);font-weight:700;letter-spacing:-.02em}}
.hero p{{color:var(--muted);margin-top:12px;font-size:15px}}
.hero .total{{display:inline-block;margin-top:18px;padding:6px 16px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:13px}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 24px 80px}}
.toolbar{{position:sticky;top:0;z-index:10;background:rgba(11,16,32,.85);backdrop-filter:blur(10px);padding:16px 0;border-bottom:1px solid var(--line);margin-bottom:28px}}
.tabs{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.tab{{cursor:pointer;border:1px solid var(--line);background:var(--panel);color:var(--muted);padding:9px 16px;border-radius:10px;font:inherit;font-size:14px;transition:.15s}}
.tab:hover{{color:var(--text);border-color:var(--accent)}}
.tab.active{{background:var(--accent);color:#06122b;border-color:var(--accent);font-weight:600}}
.badge{{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:999px;background:rgba(255,255,255,.12);font-size:12px}}
.tab.active .badge{{background:rgba(0,0,0,.18)}}
.search{{width:100%;padding:11px 16px;border:1px solid var(--line);background:var(--panel);color:var(--text);border-radius:10px;font:inherit;font-size:14px}}
.search::placeholder{{color:var(--muted)}}
.panel{{display:none}}
.panel.active{{display:block;animation:fade .25s ease}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px}}
.card{{display:flex;flex-direction:column;justify-content:space-between;min-height:128px;padding:20px;background:var(--card);border:1px solid var(--line);border-radius:14px;text-decoration:none;color:inherit;transition:.18s}}
.card:hover{{background:var(--card-h);border-color:var(--accent);transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.35)}}
.card-title{{font-size:16px;font-weight:600;line-height:1.4;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.card-meta{{display:flex;justify-content:space-between;align-items:baseline;margin-top:16px;gap:8px}}
.card-meta .name{{font-size:15px;font-weight:500}}
.card-meta .sid{{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}}
.empty{{color:var(--muted);text-align:center;padding:60px 0;display:none}}
footer{{text-align:center;color:var(--muted);font-size:13px;padding:32px 24px 48px;border-top:1px solid var(--line)}}
</style>
</head>
<body>
  <header class="hero">
    <h1>융합데이터 시각화</h1>
    <p>명지대학교 · 학생 데이터 시각화 작품 포트폴리오</p>
    <span class="total">전체 {total}개 작품</span>
  </header>
  <div class="wrap">
    <div class="toolbar">
      <div class="tabs">
{tabs}
      </div>
      <input class="search" type="search" placeholder="이름 · 학번 · 작품 제목 검색…" id="search">
    </div>
{panels}
    <p class="empty" id="empty">검색 결과가 없습니다.</p>
  </div>
  <footer>© 명지대학교 융합데이터 시각화 · 발표 시 카드를 클릭하면 새 탭에서 작품이 열립니다.</footer>
<script>
const tabs=[...document.querySelectorAll('.tab')];
const panels=[...document.querySelectorAll('.panel')];
const search=document.getElementById('search');
const empty=document.getElementById('empty');
function activate(id){{
  tabs.forEach(t=>t.classList.toggle('active',t.dataset.target===id));
  panels.forEach(p=>p.classList.toggle('active',p.id===id));
  filter();
}}
tabs.forEach(t=>t.addEventListener('click',()=>activate(t.dataset.target)));
function filter(){{
  const q=search.value.trim().toLowerCase();
  const active=document.querySelector('.panel.active');
  if(!active)return;
  let shown=0;
  active.querySelectorAll('.card').forEach(c=>{{
    const hay=(c.dataset.name+' '+c.dataset.id+' '+c.dataset.title).toLowerCase();
    const ok=!q||hay.includes(q);
    c.style.display=ok?'':'none';
    if(ok)shown++;
  }});
  empty.style.display=shown?'none':'block';
}}
search.addEventListener('input',filter);
if(tabs.length)activate(tabs[0].dataset.target);
</script>
</body>
</html>
"""


def main():
    data = scan()
    if not data:
        print("⚠️  연도/반 폴더에서 학생 HTML을 찾지 못했습니다.")
        return
    out = ROOT / "index.html"
    out.write_text(render(data), encoding="utf-8")
    total = sum(len(s) for y in data.values() for s in y.values())
    print(f"✅ index.html 생성 완료 — 작품 {total}개")
    for year, classes in data.items():
        for cname, students in classes.items():
            print(f"   {year} · {CLASS_LABELS.get(cname, cname)}: {len(students)}명")


if __name__ == "__main__":
    main()
