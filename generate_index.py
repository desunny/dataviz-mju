#!/usr/bin/env python3
"""
명지대 융합데이터 시각화 - 랜딩 페이지 + 포트폴리오 인덱스 생성기

roster.csv(코드↔실명 매핑, 비공개)를 읽어 첫 화면 index.html을 만든다.
수업 소개(랜딩) 콘텐츠는 정적이며, 포트폴리오 카드만 roster에서 생성된다.
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
    for year in data:
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
                "group_id": group_id, "year": year, "label": label,
                "count": len(students), "cards": "\n".join(cards),
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
<title>융합데이터 시각화 · 명지대학교 2026</title>
<meta name="description" content="융합데이터시각화: 인문학적 통찰과 데이터의 만남 — 명지대학교 2026학년도 1학기. 학생 데이터 시각화 작품 포트폴리오.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#f4f1ea; --bg2:#ece7dc; --ink:#2a2724; --ink2:#4a453f; --muted:#8a8378;
  --terra:#b5612f; --terra-d:#9a4f24; --slate:#5f7081; --line:#dcd5c7;
  --card:#ffffff; --dark:#23282e; --dark2:#2d343c;
}}
html{{scroll-behavior:smooth}}
body{{font-family:'IBM Plex Sans KR',sans-serif;background:var(--bg);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}}
.serif{{font-family:'Nanum Myeongjo',serif}}
section{{padding:84px 24px}}
.inner{{max-width:1080px;margin:0 auto}}
.eyebrow{{font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--terra);font-weight:600;margin-bottom:14px}}
h2.sec{{font-family:'Nanum Myeongjo',serif;font-size:clamp(24px,3.4vw,36px);font-weight:800;letter-spacing:-.01em;line-height:1.3;color:var(--ink)}}
.sec-sub{{color:var(--ink2);font-size:16px;margin-top:14px;max-width:680px}}

/* ===== HERO ===== */
.hero{{position:relative;min-height:92vh;display:flex;align-items:center;justify-content:center;text-align:center;
  background:radial-gradient(1100px 520px at 50% -5%,#fff,transparent 60%),linear-gradient(180deg,#f7f4ee,#ece7dc);overflow:hidden;padding:120px 24px 80px}}
.hero .net{{position:absolute;inset:0;background-image:radial-gradient(circle at 12% 30%,rgba(181,97,47,.10) 0 2px,transparent 3px),radial-gradient(circle at 82% 22%,rgba(95,112,129,.12) 0 2px,transparent 3px),radial-gradient(circle at 70% 75%,rgba(181,97,47,.08) 0 2px,transparent 3px),radial-gradient(circle at 28% 80%,rgba(95,112,129,.10) 0 2px,transparent 3px);pointer-events:none}}
.hero-content{{position:relative;max-width:880px}}
.hero .badge-uni{{display:inline-flex;align-items:center;gap:8px;font-size:13px;letter-spacing:.08em;color:var(--ink2);border:1px solid var(--line);background:rgba(255,255,255,.6);padding:7px 16px;border-radius:999px;margin-bottom:28px}}
.hero h1{{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:clamp(30px,5.4vw,58px);line-height:1.22;letter-spacing:-.02em;color:var(--ink)}}
.hero h1 .accent{{color:var(--terra)}}
.hero .tagline{{margin-top:22px;font-size:clamp(16px,2vw,20px);color:var(--ink2)}}
.hero .meta{{margin-top:14px;font-size:14px;color:var(--muted)}}
.cta-row{{margin-top:40px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;gap:8px;padding:14px 28px;border-radius:12px;font-weight:600;font-size:15px;text-decoration:none;transition:.18s;border:1px solid transparent}}
.btn-primary{{background:var(--terra);color:#fff}}
.btn-primary:hover{{background:var(--terra-d);transform:translateY(-2px);box-shadow:0 12px 28px rgba(181,97,47,.3)}}
.btn-ghost{{background:transparent;color:var(--ink);border-color:var(--line)}}
.btn-ghost:hover{{border-color:var(--terra);color:var(--terra)}}

/* ===== PHILOSOPHY ===== */
.philo{{background:var(--dark);color:#ece7dc}}
.philo .eyebrow{{color:#e0915f}}
.philo h2.sec{{color:#fff}}
.philo .quote{{font-family:'Nanum Myeongjo',serif;font-size:clamp(22px,3.2vw,34px);font-weight:700;line-height:1.5;color:#fff;margin:8px 0 26px}}
.philo .quote em{{color:#e0915f;font-style:normal}}
.philo p{{color:#bdb6a8;max-width:760px;font-size:16px}}
.philo .pills{{display:flex;gap:10px;flex-wrap:wrap;margin-top:30px}}
.philo .pill{{border:1px solid #3c434c;background:#2d343c;padding:9px 16px;border-radius:999px;font-size:14px;color:#ddd6c8}}
.philo .pill b{{color:#e0915f}}

/* ===== CONCEPTS ===== */
.grid3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:22px;margin-top:48px}}
.concept{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:30px;transition:.18s}}
.concept:hover{{transform:translateY(-4px);box-shadow:0 16px 36px rgba(42,39,36,.08);border-color:#cdbfa6}}
.concept .ic{{font-size:24px;width:50px;height:50px;display:grid;place-items:center;border-radius:12px;background:var(--bg2);margin-bottom:18px}}
.concept h3{{font-size:18px;font-weight:700;margin-bottom:8px}}
.concept .en{{font-size:12px;letter-spacing:.06em;color:var(--terra);font-weight:600;text-transform:uppercase;margin-bottom:10px}}
.concept p{{color:var(--ink2);font-size:14.5px}}

/* ===== TOOLS ===== */
.tools{{background:var(--bg2)}}
.tool-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px;margin-top:44px}}
.tool{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:30px;text-align:center;position:relative}}
.tool.main{{border:2px solid var(--terra);box-shadow:0 12px 30px rgba(181,97,47,.12)}}
.tool .star{{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--terra);color:#fff;font-size:12px;font-weight:600;padding:4px 14px;border-radius:999px}}
.tool .name{{font-family:'Nanum Myeongjo',serif;font-size:22px;font-weight:700;margin-bottom:8px}}
.tool .role{{color:var(--ink2);font-size:14px}}

/* ===== ROADMAP ===== */
.roadmap .inner{{position:relative}}
.phases{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-top:48px}}
.phase{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px 24px;position:relative;overflow:hidden}}
.phase::before{{content:'';position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--terra)}}
.phase .pnum{{font-family:'Nanum Myeongjo',serif;font-size:13px;color:var(--terra);font-weight:700;letter-spacing:.05em}}
.phase .wk{{font-size:12px;color:var(--muted);margin:4px 0 14px}}
.phase h3{{font-size:17px;font-weight:700;line-height:1.4}}

/* ===== PROJECT ===== */
.project{{background:var(--dark);color:#ece7dc}}
.project .eyebrow{{color:#e0915f}}
.project h2.sec{{color:#fff}}
.project .sec-sub{{color:#bdb6a8}}
.proj-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-top:44px}}
.proj{{background:#2d343c;border:1px solid #3c434c;border-radius:16px;padding:30px;text-align:center}}
.proj .ic{{font-size:34px;margin-bottom:14px}}
.proj .cat{{font-family:'Nanum Myeongjo',serif;font-size:22px;font-weight:700;color:#fff;margin-bottom:8px}}
.proj p{{color:#bdb6a8;font-size:14px}}

/* ===== EVAL ===== */
.eval-row{{display:flex;flex-wrap:wrap;gap:40px;align-items:center;justify-content:space-between;margin-top:44px}}
.eval-bars{{flex:1;min-width:300px;display:flex;flex-direction:column;gap:16px}}
.ebar{{display:flex;align-items:center;gap:14px}}
.ebar .lbl{{width:64px;font-size:14px;font-weight:600;color:var(--ink2)}}
.ebar .track{{flex:1;height:14px;background:var(--bg2);border-radius:999px;overflow:hidden}}
.ebar .fill{{height:100%;background:linear-gradient(90deg,var(--terra),var(--terra-d));border-radius:999px}}
.ebar .pct{{width:46px;text-align:right;font-weight:700;font-size:14px;color:var(--terra)}}
.goals{{flex:1;min-width:280px}}
.goals h3{{font-size:17px;font-weight:700;margin-bottom:16px}}
.goals li{{list-style:none;padding-left:26px;position:relative;margin-bottom:12px;color:var(--ink2);font-size:15px}}
.goals li::before{{content:'✓';position:absolute;left:0;color:var(--terra);font-weight:700}}

/* ===== PORTFOLIO ===== */
.portfolio{{background:var(--bg)}}
.toolbar{{position:sticky;top:0;z-index:20;background:rgba(244,241,234,.9);backdrop-filter:blur(10px);padding:18px 0;border-bottom:1px solid var(--line);margin:36px 0 28px}}
.tabs{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.tab{{cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink2);padding:9px 16px;border-radius:10px;font:inherit;font-size:14px;transition:.15s}}
.tab:hover{{color:var(--ink);border-color:var(--terra)}}
.tab.active{{background:var(--terra);color:#fff;border-color:var(--terra);font-weight:600}}
.badge{{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:999px;background:rgba(0,0,0,.08);font-size:12px}}
.tab.active .badge{{background:rgba(255,255,255,.25)}}
.search{{width:100%;padding:12px 16px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;font:inherit;font-size:14px}}
.search::placeholder{{color:var(--muted)}}
.panel{{display:none}}
.panel.active{{display:block;animation:fade .25s ease}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px}}
.card{{display:flex;flex-direction:column;justify-content:space-between;min-height:132px;padding:22px;background:var(--card);border:1px solid var(--line);border-radius:14px;text-decoration:none;color:inherit;transition:.18s}}
.card:hover{{border-color:var(--terra);transform:translateY(-3px);box-shadow:0 12px 30px rgba(42,39,36,.1)}}
.card-title{{font-size:16px;font-weight:600;line-height:1.45;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.card-meta{{display:flex;justify-content:space-between;align-items:baseline;margin-top:18px;gap:8px}}
.card-meta .name{{font-size:15px;font-weight:600}}
.card-meta .sid{{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}}
.empty{{color:var(--muted);text-align:center;padding:60px 0;display:none}}

footer{{background:var(--dark);color:#bdb6a8;text-align:center;padding:60px 24px}}
footer .fq{{font-family:'Nanum Myeongjo',serif;font-size:clamp(18px,2.4vw,24px);color:#fff;font-weight:700;margin-bottom:10px}}
footer .fs{{font-size:14px;color:#9a9387}}
footer .fmeta{{margin-top:24px;font-size:13px;color:#7d776c}}

.nav{{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;justify-content:space-between;align-items:center;padding:14px 24px;background:rgba(244,241,234,.0);transition:.25s}}
.nav.solid{{background:rgba(244,241,234,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
.nav .brand{{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:16px;color:var(--ink)}}
.nav .links{{display:flex;gap:22px}}
.nav .links a{{font-size:14px;color:var(--ink2);text-decoration:none;transition:.15s}}
.nav .links a:hover{{color:var(--terra)}}
@media(max-width:640px){{.nav .links{{display:none}}section{{padding:60px 20px}}}}
</style>
</head>
<body>

<nav class="nav" id="nav">
  <div class="brand">융합데이터시각화</div>
  <div class="links">
    <a href="#philosophy">철학</a>
    <a href="#concepts">핵심 개념</a>
    <a href="#roadmap">학기 로드맵</a>
    <a href="#portfolio">포트폴리오</a>
  </div>
</nav>

<!-- HERO -->
<header class="hero">
  <div class="net"></div>
  <div class="hero-content">
    <span class="badge-uni">명지대학교 · 2026학년도 1학기 · 담당교수 최예신</span>
    <h1 class="serif">융합데이터시각화<br><span class="accent">인문학적 통찰</span>과 데이터의 만남</h1>
    <p class="tagline">데이터를 읽고, 쓰고, 말하는 새로운 언어</p>
    <p class="meta">숫자는 건조하지만, 그 안에 담긴 이야기는 인간적입니다.</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="#portfolio">학생 작품 보기 →</a>
      <a class="btn btn-ghost" href="#philosophy">수업 소개</a>
    </div>
  </div>
</header>

<!-- PHILOSOPHY -->
<section class="philo" id="philosophy">
  <div class="inner">
    <div class="eyebrow">Our Philosophy</div>
    <p class="quote">데이터는 새로운 잉크(Ink)이고,<br><em>여러분은 작가</em>입니다.</p>
    <p>데이터 시각화는 통계나 코딩이 아닌, <b style="color:#fff">의미를 전달하는 설득의 기술</b>입니다.
    우리의 목표는 인문학적 맥락(Context)과 공감(Empathy)을 데이터에 입혀 강력한 서사(Narrative)를 만드는 것.
    기술적 장벽은 도구가 해결합니다 — 여러분은 ‘무엇을 보여줄지’만 고민하세요.</p>
    <div class="pills">
      <span class="pill">🧠 <b>논리적 사고</b></span>
      <span class="pill">🌿 <b>Flourish</b> 노코드 툴</span>
      <span class="pill">🤖 <b>ChatGPT &amp; Python</b></span>
    </div>
  </div>
</section>

<!-- CONCEPTS -->
<section id="concepts">
  <div class="inner">
    <div class="eyebrow">What We Learn</div>
    <h2 class="sec">‘본다’는 것의 과학,<br>그리고 ‘속이지 않는’ 디자인 윤리</h2>
    <p class="sec-sub">눈으로 보는 0.1초의 직관부터, 데이터를 왜곡하지 않는 정직한 디자인 원칙까지 배웁니다.</p>
    <div class="grid3">
      <div class="concept">
        <div class="ic">👁️</div>
        <div class="en">Pre-attentive Processing</div>
        <h3>전주의적 처리</h3>
        <p>뇌는 0.1초 만에 색상·길이·방향의 패턴을 파악합니다. 좋은 시각화는 이 본능을 활용해 핵심을 즉시 전달합니다.</p>
      </div>
      <div class="concept">
        <div class="ic">📊</div>
        <div class="en">Anscombe's Quartet</div>
        <h3>왜 시각화인가</h3>
        <p>평균·분산이 모두 같아도, 시각화하면 전혀 다른 패턴이 보입니다. 통계값만으로는 진실을 놓칩니다.</p>
      </div>
      <div class="concept">
        <div class="ic">⚖️</div>
        <div class="en">Lie Factor</div>
        <h3>데이터 속 거짓말</h3>
        <p>잘려나간 Y축, 3D 원근법의 착시. 그래프는 팩트처럼 보이지만 쉽게 조작될 수 있습니다 — 윤리가 중요합니다.</p>
      </div>
      <div class="concept">
        <div class="ic">🖋️</div>
        <div class="en">Data-Ink Ratio</div>
        <h3>뺄셈의 미학</h3>
        <p>불필요한 장식과 배경(Chartjunk)을 제거해 데이터가 숨 쉬게 하십시오. 지울수록 정보는 명확해집니다.</p>
      </div>
      <div class="concept">
        <div class="ic">🗺️</div>
        <div class="en">Minard · John Snow</div>
        <h3>역사 속 명작</h3>
        <p>나폴레옹 행군 지도(1869)는 6차원 정보를 한 장에, 콜레라 지도(1854)는 점 하나로 진실을 밝혔습니다.</p>
      </div>
      <div class="concept">
        <div class="ic">🤖</div>
        <div class="en">AI as Your Assistant</div>
        <h3>AI &amp; 파이썬</h3>
        <p>코드를 직접 작성하는 것이 아니라, AI의 결과물을 검토(Review)하고 실행(Execute)합니다. 코딩 몰라도 괜찮습니다.</p>
      </div>
    </div>
  </div>
</section>

<!-- TOOLS -->
<section class="tools">
  <div class="inner">
    <div class="eyebrow">Toolkit</div>
    <h2 class="sec">무엇으로 그릴 것인가</h2>
    <div class="tool-row">
      <div class="tool">
        <div class="name">Python · matplotlib</div>
        <div class="role">데이터 분석 및 AI 활용</div>
      </div>
      <div class="tool main">
        <span class="star">수업 주력 도구</span>
        <div class="name">Flourish</div>
        <div class="role">인터랙티브 스토리텔링 — Bar Chart Race·스크롤리텔링을 코딩 없이</div>
      </div>
      <div class="tool">
        <div class="name">Tableau</div>
        <div class="role">비즈니스 대시보드</div>
      </div>
    </div>
  </div>
</section>

<!-- ROADMAP -->
<section class="roadmap" id="roadmap">
  <div class="inner">
    <div class="eyebrow">Semester Roadmap</div>
    <h2 class="sec">데이터 리터러시에서<br>포트폴리오까지</h2>
    <div class="phases">
      <div class="phase"><div class="pnum">Phase 1</div><div class="wk">1–3주</div><h3>시각 지각 원리<br>&amp; 리터러시</h3></div>
      <div class="phase"><div class="pnum">Phase 2</div><div class="wk">4–7주</div><h3>Flourish<br>집중 실습</h3></div>
      <div class="phase"><div class="pnum">Phase 3</div><div class="wk">9–12주</div><h3>AI 활용<br>데이터 전처리</h3></div>
      <div class="phase"><div class="pnum">Phase 4</div><div class="wk">13–16주</div><h3>기말 프로젝트<br>&amp; 발표</h3></div>
    </div>
  </div>
</section>

<!-- PROJECT -->
<section class="project">
  <div class="inner">
    <div class="eyebrow">Final Project</div>
    <h2 class="sec">인문학적 상상력의 시각화</h2>
    <p class="sec-sub">단순한 현황 파악이 아닌, ‘왜?’에 대한 답을 찾는 데이터 서사를 구성합니다.</p>
    <div class="proj-row">
      <div class="proj"><div class="ic">📖</div><div class="cat">문학</div><p>셰익스피어 작품 속 단어 빈도 분석</p></div>
      <div class="proj"><div class="ic">🗺️</div><div class="cat">역사</div><p>조선시대 과거 급제자의 지역 분포</p></div>
      <div class="proj"><div class="ic">🎵</div><div class="cat">문화</div><p>K-Pop 가사의 감정 변화 추이</p></div>
    </div>
  </div>
</section>

<!-- EVALUATION -->
<section id="evaluation">
  <div class="inner">
    <div class="eyebrow">Evaluation &amp; Goals</div>
    <h2 class="sec">평가 기준 및 성취 목표</h2>
    <div class="eval-row">
      <div class="eval-bars">
        <div class="ebar"><span class="lbl">과제</span><div class="track"><div class="fill" style="width:100%"></div></div><span class="pct">40%</span></div>
        <div class="ebar"><span class="lbl">중간</span><div class="track"><div class="fill" style="width:50%"></div></div><span class="pct">20%</span></div>
        <div class="ebar"><span class="lbl">기말</span><div class="track"><div class="fill" style="width:50%"></div></div><span class="pct">20%</span></div>
        <div class="ebar"><span class="lbl">출석</span><div class="track"><div class="fill" style="width:50%"></div></div><span class="pct">20%</span></div>
      </div>
      <div class="goals">
        <h3>성취 목표</h3>
        <ul>
          <li>도구의 숙련도보다 <b>메시지의 명확성</b></li>
          <li>데이터 디자인 <b>윤리</b> 준수</li>
          <li>매주 실습이 모여 완성되는 <b>포트폴리오</b></li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- PORTFOLIO -->
<section class="portfolio" id="portfolio">
  <div class="inner">
    <div class="eyebrow">Student Portfolio</div>
    <h2 class="sec">학생 작품 갤러리 <span style="color:var(--terra)">·</span> 총 {total}개</h2>
    <p class="sec-sub">한 학기 동안 학생들이 직접 만든 데이터 시각화 작품입니다. 카드를 클릭하면 새 탭에서 작품이 열립니다.</p>
    <div class="toolbar">
      <div class="tabs">
{tabs}
      </div>
      <input class="search" type="search" placeholder="이름 · 학번 · 작품 제목 검색…" id="search">
    </div>
{panels}
    <p class="empty" id="empty">검색 결과가 없습니다.</p>
  </div>
</section>

<footer>
  <p class="fq serif">데이터의 숲에서 길을 찾는 안내자가 되십시오.</p>
  <p class="fs">융합데이터시각화의 세계에 오신 것을 환영합니다.</p>
  <p class="fmeta">© 2026 명지대학교 융합데이터시각화 · 담당교수 최예신</p>
</footer>

<script>
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('solid',scrollY>40));
const tabs=[...document.querySelectorAll('.tab')];
const panels=[...document.querySelectorAll('.panel')];
const search=document.getElementById('search');
const empty=document.getElementById('empty');
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
function activate(id){{
  tabs.forEach(t=>t.classList.toggle('active',t.dataset.target===id));
  panels.forEach(p=>p.classList.toggle('active',p.id===id));
  filter();
}}
tabs.forEach(t=>t.addEventListener('click',()=>activate(t.dataset.target)));
search.addEventListener('input',filter);
if(tabs.length)activate(tabs[0].dataset.target);
</script>
</body>
</html>
"""


def main():
    data = scan()
    if not data:
        print("⚠️  roster.csv에서 학생을 찾지 못했습니다.")
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
