# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.5] 일정 · 업체 화면 생성기 (기획서 v0.5 6-6 · 6-7)
  대시보드(gen_dashboard.py)와 같은 더미 업체·캠페인을 쓴다 — 같은 시드로 make_biz() 를 다시 부르면 똑같이 나온다.
  일정 화면 = Square 격자(행 = 담당자, 맨 위 = 미담당, 맨 아래 = 날짜별 합계), 업체 화면 = 목록 + 오른쪽 상세 + 등록.
  화면 동작은 HTML/CSS 우선(라디오·체크박스 + CSS), 꼭 필요한 것만 js/pages.js.
  실행: python -I build/gen_pages.py  →  mvp/schedule.html · mvp/biz.html
"""
import html
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_dashboard as G  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 9)          # 더미 기준일(대시보드와 같음)
esc = html.escape
WD = "월화수목금토일"


def d_of(off):
    return TODAY + timedelta(days=off)


def md(off):
    d = d_of(off)
    return f"{d.month}/{d.day}"


def mdw(off):
    d = d_of(off)
    return f"{d.month}/{d.day} ({WD[d.weekday()]})"


# ── 공통 데이터 ─────────────────────────────────────────
BIZS = G.make_biz()
TOTAL_ISSUE = sum(v["n"] for b in BIZS for v in b["issues"].values())
STAFF_TEAM = [(tname, members) for _x, tname, members in G.TEAMS]

# 일정 종류 4색 — 상태 배지 색과 겹치지 않는 별도 팔레트(기획서 4장)
KIND = [("rec", "모집 마감"), ("sel", "선정 마감"), ("exp", "체험 시작"), ("rev", "리뷰 마감")]
EXP_LABEL = {"v": "방문·체험 시작", "s": "배송 시작", "p": "원고 시작"}


def camp_dues(b, camp):
    """이 캠페인에 걸린 이슈별 가장 이른 기한"""
    out = {}
    for k, it in b["issues"].items():
        ds = [d for c, d in it["items"] if c == camp]
        if ds:
            out[k] = min(ds)
    return out


def camp_dates(b, camp):
    """캠페인 일정 4개(오늘 기준 일수). 걸린 이슈의 기한과 맞춘다"""
    r = random.Random(G.ccode(camp) * 31 + int(b["id"][1:]))
    st = G.camp_state(b, camp)
    du = camp_dues(b, camp)
    if st == "모집 중":
        rec = du.get("apply", r.randint(1, 6)); sel = rec + 2; exp = sel + 2; rev = exp + 10
    elif st == "선정 중":
        sel = du.get("select", r.randint(0, 2)); rec = sel - 3; exp = sel + 2; rev = exp + 10
    elif st in ("체험 중", "배송·체험 중", "원고 작성 중"):
        exp = du.get("prep", r.randint(-3, 2)); rec = exp - 7; sel = exp - 4; rev = exp + 9
    elif st == "리뷰 중":
        rev = min(du.get("review", 99), du.get("nudge", 99))
        rev = rev if rev != 99 else r.randint(0, 5); exp = rev - 9; sel = exp - 3; rec = sel - 3
    elif st == "기한 지남":
        rec = du.get("late", -2); sel = rec + 2; exp = sel + 2; rev = exp + 10
    elif st == "정산 중":
        rev = r.randint(-6, -2); exp = rev - 9; sel = exp - 3; rec = sel - 3
    else:
        rec = r.randint(-2, 8); sel = rec + 2; exp = sel + 2; rev = exp + 10
    return {"rec": rec, "sel": sel, "exp": exp, "rev": rev}


def events():
    """모든 캠페인 일정 → [(담당자 id 또는 '', 업체, 캠페인, 종류, 일수)]"""
    out = []
    for b in BIZS:
        sid = b["owner"][0] if b["owner"] else ""
        for c in b["camps"]:
            for k, off in camp_dates(b, c).items():
                out.append({"sid": sid, "b": b, "camp": c, "kind": k, "off": off})
    return out


EVS = events()


def hot(b, camp):
    return any(d <= 0 for it in b["issues"].values() for c, d in it["items"] if c == camp)


def kind_label(ev):
    return EXP_LABEL[G.ctype(ev["camp"])] if ev["kind"] == "exp" else dict(KIND)[ev["kind"]]


def cp_id(b, camp):
    return f'{b["id"]}-{G.ccode(camp)}'


# ── 공통 셸 ─────────────────────────────────────────────
def page(title, active, body, panel, extra_style=""):
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 뷰마 대행사 ({G.VERSION} 시안)</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="css/agency.css">
<link rel="stylesheet" href="css/pages.css">
{extra_style}
</head>
<body>
<!-- [2026-11-10] 대행사 {title} 시안 {G.VERSION} — 기획서 v0.5. build/gen_pages.py 로 생성(직접 수정 금지) -->
<div class="shell">
{G.sidebar(TOTAL_ISSUE, active)}
<div class="main">
{G.topbar()}
<div class="work">
{body}
<aside class="panel" aria-label="상세" aria-live="polite">
{panel}
</aside>
</div>
</div>
</div>
<script src="js/pages.js"></script>
</body>
</html>
'''


def ty_badges(camp):
    ty, ch = G.CAMP_META[camp]
    return f'<span class="ty ty-{ty}">{G.TYPE_NAME[ty]}</span><span class="chn">{ch}</span>'


# ════════════════════════ 일정 ════════════════════════
WEEKS = [(-7, "11/2 – 11/8"), (0, "11/9 – 11/15"), (7, "11/16 – 11/22")]
ROWS = [("un", "미담당 업체", None, None)] + [(sid, name, lead, tname) for tname, members in STAFF_TEAM for sid, name, lead in members]


def ev_card(ev):
    b, c = ev["b"], ev["camp"]
    past = " past" if ev["off"] < 0 else ""
    dot = '<i class="hotdot" title="기한 지남·오늘 이슈 있음"></i>' if hot(b, c) else ""
    lab = kind_label(ev)
    return (f'<button type="button" class="ev k-{ev["kind"]}{past}" data-cp="{cp_id(b, c)}" '
            f'aria-label="{esc(b["name"])} {esc(c)} {lab} {mdw(ev["off"])}">'
            f'<b>{dot}{esc(b["name"])}</b><span>{lab}{" · 지남" if past else ""}</span></button>')


def day_cell(evs):
    evs = sorted(evs, key=lambda e: [k for k, _ in KIND].index(e["kind"]))
    if not evs:
        return '<td class="dc"></td>'
    shown = "".join(ev_card(e) for e in evs[:3])
    more = ""
    if len(evs) > 3:
        # 3건 넘으면 "+N" — 펼침은 <details> (JS 없음)
        more = f'<details class="more"><summary>+{len(evs) - 3}</summary>{"".join(ev_card(e) for e in evs[3:])}</details>'
    return f'<td class="dc">{shown}{more}</td>'


def week_table(start, label, idx):
    days = list(range(start, start + 7))
    head = "".join(
        f'<th scope="col" class="{"today" if o == 0 else ""}{" wkend" if d_of(o).weekday() >= 5 else ""}">'
        f'{WD[d_of(o).weekday()]} <b>{md(o)}</b>{"<em>오늘</em>" if o == 0 else ""}</th>' for o in days)
    rows = []
    team_now = None
    for sid, name, lead, tname in ROWS:
        if tname and tname != team_now:
            team_now = tname
            rows.append(f'<tr class="t-row t-{"none" if tname == "팀 없음" else "on"}"><th colspan="8" scope="rowgroup">{tname}</th></tr>')
        mine = [e for e in EVS if e["sid"] == ("" if sid == "un" else sid)]
        wk = [e for e in mine if start <= e["off"] < start + 7]
        nbiz = len({e["b"]["id"] for e in mine})
        sub = f'업체 {nbiz} · 이번 주 기한 {len(wk)}'
        who = ('<span class="who none">미담당</span>' if sid == "un"
               else f'<span class="who"><i>{name[0]}</i>{name}</span>{"<span class=lead>팀장</span>" if lead else ""}')
        cells = "".join(day_cell([e for e in wk if e["off"] == o]) for o in days)
        rows.append(f'<tr class="s-row s-{sid}{" s-un" if sid == "un" else ""}">'
                    f'<th scope="row" class="sname"><label for="who-{sid}" class="who-l">{who}</label><small>{sub}</small></th>{cells}</tr>')
    tot = "".join(f'<td class="dt">{sum(1 for e in EVS if e["off"] == o) or "·"}</td>' for o in days)
    week_n = sum(1 for e in EVS if start <= e["off"] < start + 7)
    rows.append(f'<tr class="tot-row"><th scope="row">날짜별 합계 <b>{week_n}</b></th>{tot}</tr>')
    return (f'<table class="sched wk-{idx}"><caption class="sr">{label} 담당자별 일정</caption>'
            f'<thead><tr><th scope="col" class="sname">담당자</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>')


def month_view():
    """월 보기 — 11월 달력. 칸 = 날짜, 종류별 건수 + 앞 2건(담당자 거르기 적용)"""
    first = date(2026, 11, 1)
    start = first - timedelta(days=first.weekday())     # 그 주 월요일
    cells = []
    for i in range(35):
        dd = start + timedelta(days=i)
        off = (dd - TODAY).days
        evs = sorted([e for e in EVS if e["off"] == off], key=lambda e: [k for k, _ in KIND].index(e["kind"]))
        cnt = "".join(f'<span class="mk k-{k}">{lab.split()[0]} {sum(1 for e in evs if e["kind"] == k)}</span>'
                      for k, lab in KIND if any(e["kind"] == k for e in evs))
        lines = "".join(
            f'<button type="button" class="mev k-{e["kind"]} s-{e["sid"] or "un"}" data-cp="{cp_id(e["b"], e["camp"])}">'
            f'{esc(e["b"]["name"])} · {kind_label(e)}</button>' for e in evs)
        out = " out" if dd.month != 11 else ""
        cells.append(f'<div class="mday{out}{" today" if off == 0 else ""}"><p class="mnum">{dd.day}</p>'
                     f'<div class="mcnt">{cnt}</div><div class="mlist">{lines}</div></div>')
    heads = "".join(f'<div class="mhead">{w}</div>' for w in WD)
    return f'<div class="month">{heads}{"".join(cells)}</div>'


def camp_panel(b, camp):
    """일정 카드를 누르면 오른쪽에 — 캠페인 일정 4개 · 걸린 이슈(대시보드 바로가기)"""
    dts = camp_dates(b, camp)
    st = G.camp_state(b, camp)
    owner = b["owner"][1] if b["owner"] else "미담당"
    tl = "".join(
        f'<li class="tl k-{k}{" past" if dts[k] < 0 else ""}{" now" if dts[k] == 0 else ""}"><i></i>'
        f'<b>{EXP_LABEL[G.ctype(camp)] if k == "exp" else lab}</b><span>{mdw(dts[k])} · {G.due_label(dts[k])}</span></li>'
        for k, lab in KIND)
    iss = [(k, sum(1 for c, _d in it["items"] if c == camp), min(d for c, d in it["items"] if c == camp))
           for k, it in b["issues"].items() if any(c == camp for c, _d in it["items"])]
    chips = "".join(f'<a class="ichip {G.due_class(d)}" href="dashboard.html#open={b["id"]}-{k}">{G.ISSUE_NAME[k]} {n}<small>{G.due_label(d)}</small></a>'
                    for k, n, d in iss) or '<p class="muted">걸린 이슈가 없습니다</p>'
    ty = G.ctype(camp)
    return (f'<section class="pane cg-{ty}" data-cp="{cp_id(b, camp)}" hidden>'
            f'<header class="pane-h"><p class="pane-biz">{esc(b["name"])} <span>담당 {owner}</span></p>'
            f'<h2 class="cp-title">{ty_badges(camp)}<b>{esc(camp)}</b></h2>'
            f'<p class="pane-camp"><span class="cg-state">{st}</span></p></header>'
            f'<div class="pane-b"><h3 class="sec-t">일정</h3><ol class="timeline">{tl}</ol>'
            f'<h3 class="sec-t">이 캠페인에 걸린 이슈</h3><div class="ichips">{chips}</div>'
            f'<p class="note">이슈를 누르면 대시보드의 그 칸이 열립니다 — 처리는 대시보드에서.</p></div>'
            f'<footer class="pane-f"><a href="biz.html#biz={b["id"]}" class="btn ghost">업체 보기 →</a>'
            f'<a href="#" class="btn">상세 관리 →</a></footer></section>')


def schedule_page():
    # 거르기 장치는 표보다 앞의 형제 input 이어야 CSS ~ 로 닿는다
    who_inputs = '<input type="radio" name="who" id="who-all" class="vr" checked>' + "".join(
        f'<input type="radio" name="who" id="who-{sid}" class="vr">' for sid, *_ in ROWS)
    kind_inputs = "".join(f'<input type="checkbox" id="kd-{k}" class="vr" checked>' for k, _ in KIND)
    wk_inputs = "".join(f'<input type="radio" name="wk" id="wk-{i}" class="vr"{" checked" if i == 1 else ""}>' for i in range(3))
    view_inputs = '<input type="radio" name="sv" id="sv-week" class="vr" checked><input type="radio" name="sv" id="sv-month" class="vr">'
    who_chips = '<label for="who-all" class="pill">전체</label>' + "".join(
        f'<label for="who-{sid}" class="pill">{"미담당" if sid == "un" else name}</label>' for sid, name, *_ in ROWS)
    kind_chips = "".join(f'<label for="kd-{k}" class="kchip k-{k}"><i></i>{lab}</label>' for k, lab in KIND)
    wk_nav = "".join(
        f'<span class="wknav wn-{i}">'
        + (f'<label for="wk-{i - 1}" class="pill" aria-label="이전 주">‹</label>' if i > 0 else '<span class="pill off">‹</span>')
        + f'<b>{lab}</b>'
        + (f'<label for="wk-{i + 1}" class="pill" aria-label="다음 주">›</label>' if i < 2 else '<span class="pill off">›</span>')
        + (f'<label for="wk-1" class="pill today-b">오늘</label>' if i != 1 else "") + '</span>'
        for i, (_s, lab) in enumerate(WEEKS))
    tables = "".join(week_table(s, lab, i) for i, (s, lab) in enumerate(WEEKS))
    # 담당자 거르기 CSS — 사람 수만큼 규칙이 생기므로 여기서 만든다
    who_css = "\n".join(
        f'#who-{sid}:checked ~ .sched-wrap .s-row:not(.s-{sid}),#who-{sid}:checked ~ .sched-wrap .t-row,'
        f'#who-{sid}:checked ~ .sched-wrap .mev:not(.s-{sid}){{display:none}}'
        f'#who-{sid}:checked ~ .s-tools label[for=who-{sid}]{{background:var(--c-14);color:#fff;border-color:var(--c-14)}}'
        for sid, *_ in ROWS)
    style = f'<style>/* [2026-11-10] 담당자 거르기 — 생성 */\n{who_css}</style>'
    body = f'''<section class="board sched-page" aria-labelledby="t-sched">
	<div class="board-h"><div><h1 id="t-sched">일정</h1>
		<p class="sub">행 = 담당자, 맨 위 = 미담당 업체, 맨 아래 = 날짜별 합계 · 카드 색 = 일정 종류 · 이름을 누르면 그 사람만</p></div>
		<a class="btn" href="#">엑셀 내려받기</a></div>
	{who_inputs}{kind_inputs}{wk_inputs}{view_inputs}
	<div class="s-tools">
		<div class="seg sm"><label for="sv-week">주</label><label for="sv-month">월</label></div>
		<div class="wknavs">{wk_nav}<b class="mon-lab">2026년 11월</b></div>
		<div class="kchips" role="group" aria-label="일정 종류">{kind_chips}</div>
	</div>
	<div class="s-tools s-who" role="group" aria-label="담당자">{who_chips}</div>
	<div class="sched-wrap">{tables}{month_view()}</div>
</section>'''
    panel = ('<div class="pane-empty"><p class="empty-ico" aria-hidden="true">📅</p><p><b>일정 카드를 누르세요</b></p>'
             '<p class="muted">캠페인 일정 4개와 걸린 이슈를 보여 줍니다.<br>처리는 대시보드에서 합니다.</p></div>'
             + "".join(camp_panel(b, c) for b in BIZS for c in b["camps"]))
    return page("일정", "cal", body, panel, style)


# ════════════════════════ 업체 ════════════════════════
INDUSTRY = ["미용", "음식점", "카페·베이커리", "병의원", "교육", "레저", "반려동물", "숙박", "뷰티", "농산물"]
REGION = ["서울 마포구", "서울 성동구", "서울 강남구", "서울 종로구", "경기 성남시", "경기 수원시", "부산 해운대구", "제주 제주시", "인천 연수구", "강원 강릉시"]
ARCHIVED = [("을왕리 조개구이", "음식점", "인천 중구", "2026-09-30"), ("해방촌 꽃집", "기타", "서울 용산구", "2026-10-12"),
            ("광안리 요트투어", "레저", "부산 수영구", "2026-10-28")]


# 업체 이름에서 업종·지역을 짐작(더미가 이름과 어긋나 보이지 않게)
IND_KEY = [(("헤어", "네일", "속눈썹"), "미용"), (("피부과", "치과"), "병의원"), (("학원",), "교육"),
           (("카페", "베이커리", "커피"), "카페·베이커리"), (("필라테스", "키즈풀", "보드게임"), "레저"),
           (("애견",), "반려동물"), (("농원",), "농산물")]
REG_KEY = {"연남": "서울 마포구", "망원": "서울 마포구", "합정": "서울 마포구", "홍대": "서울 마포구", "신촌": "서울 서대문구",
           "성수": "서울 성동구", "건대": "서울 광진구", "을지로": "서울 중구", "서촌": "서울 종로구", "익선동": "서울 종로구",
           "강남": "서울 강남구", "청담": "서울 강남구", "판교": "경기 성남시", "분당": "경기 성남시", "잠실": "서울 송파구",
           "송리단길": "서울 송파구", "광교": "경기 수원시", "수원": "경기 수원시", "부산": "부산 해운대구", "제주": "제주 제주시",
           "대구": "대구 중구", "일산": "경기 고양시", "목동": "서울 양천구", "용산": "서울 용산구", "여의도": "서울 영등포구",
           "인천": "인천 중구", "전주": "전북 전주시", "강릉": "강원 강릉시", "춘천": "강원 춘천시", "평택": "경기 평택시"}


def guess_ind(name):
    return next((ind for keys, ind in IND_KEY if any(k in name for k in keys)), "음식점")


def extra(b):
    r = random.Random(1000 + int(b["id"][1:]))
    r.choice(INDUSTRY); r.choice(REGION)          # 난수 순서 유지(아래 값이 바뀌지 않게)
    return {"ind": guess_ind(b["name"]), "reg": REG_KEY.get(b["name"].split()[0], "서울"), "acc": len(b["camps"]) + r.randint(0, 14),
            "used": r.choice([0, 55000, 110000, 165000, 220000, 330000, 495000]),
            "reg_d": f"2026-{r.randint(3, 10):02d}-{r.randint(1, 28):02d}",
            "tel": f"010-****-{r.randint(1000, 9999)}", "bno": f"{r.randint(100, 899)}-**-*****"}


def staff_opts(sel=""):
    return "".join(f'<option value="{sid}"{" selected" if sid == sel else ""}>{name} ({tname})</option>'
                   for tname, members in STAFF_TEAM for sid, name, _l in members)


def biz_row(b):
    x = extra(b)
    n_iss = sum(v["n"] for v in b["issues"].values())
    hot_n = sum(1 for v in b["issues"].values() for _c, d in v["items"] if d <= 0)
    owner = (f'<span class="who"><i>{b["owner"][1][0]}</i>{b["owner"][1]}</span>' if b["owner"]
             else '<span class="who none">미담당</span>')
    team = b["owner"][3] if b["owner"] else "—"
    cls = " f-un" if not b["owner"] else ""
    cls += " f-iss" if n_iss else ""
    iss = (f'<a class="ichip {"is-hot" if hot_n else "is-later"}" href="dashboard.html#biz={b["id"]}">{n_iss}'
           f'{f"<small>급함 {hot_n}</small>" if hot_n else ""}</a>' if n_iss else '<span class="muted">—</span>')
    return (f'<tr class="brow{cls}" data-biz="{b["id"]}" data-active="{len(b["camps"])}" data-name="{esc(b["name"])} {x["ind"]} {x["reg"]}">'
            f'<td class="ck"><input type="checkbox" class="js-ck" aria-label="{esc(b["name"])} 선택"></td>'
            f'<th scope="row"><button type="button" class="bname js-open" data-biz="{b["id"]}">{esc(b["name"])}</button></th>'
            f'<td>{x["ind"]}</td><td>{x["reg"]}</td><td class="js-owner">{owner}</td><td class="js-team">{team}</td>'
            f'<td class="num">{len(b["camps"])} / {x["acc"]}</td><td class="num">{x["used"]:,}P</td><td>{iss}</td>'
            f'<td class="muted">{x["reg_d"]}</td></tr>')


def archived_rows():
    return "".join(
        f'<tr class="brow f-arch" data-active="0" data-name="{n} {i} {r}"><td class="ck"><input type="checkbox" class="js-ck" aria-label="{n} 선택"></td>'
        f'<th scope="row"><span class="bname arch">{n}</span> <span class="tag-arch">보관</span></th><td>{i}</td><td>{r}</td>'
        f'<td><span class="muted">—</span></td><td>—</td><td class="num">0 / {3 + k}</td><td class="num">0P</td><td><span class="muted">—</span></td>'
        f'<td class="muted">보관 {d}</td></tr>' for k, (n, i, r, d) in enumerate(ARCHIVED))


def biz_drawer(b):
    """업체 상세 — 오른쪽 패널, 탭은 라디오 + CSS"""
    x = extra(b)
    bid = b["id"]
    tabs = [("ov", "개요"), ("cp", "캠페인"), ("use", "사용내역"), ("rep", "보고서"), ("memo", "메모"), ("log", "이력")]
    radios = "".join(f'<input type="radio" name="tab-{bid}" id="tab-{bid}-{k}" class="vr tabr tr-{k}"{" checked" if k == "ov" else ""}>' for k, _ in tabs)
    tabbar = "".join(f'<label for="tab-{bid}-{k}" class="tab tl-{k}">{lab}</label>' for k, lab in tabs)
    n_iss = {k: v["n"] for k, v in b["issues"].items()}
    ichips = "".join(f'<a class="ichip" href="dashboard.html#open={bid}-{k}">{G.ISSUE_NAME[k]} {n}</a>' for k, n in n_iss.items()) \
        or '<span class="muted">이슈 없음</span>'
    owner_sel = b["owner"][0] if b["owner"] else ""
    ov = (f'<h3 class="sec-t">리뷰어에게 보이는 정보</h3><dl class="kv2"><dt>노출명</dt><dd>{esc(b["name"])}</dd>'
          f'<dt>주소</dt><dd>{x["reg"]} ○○로 ***</dd><dt>소개</dt><dd>{x["ind"]} · 동네 단골이 많은 곳</dd></dl>'
          f'<h3 class="sec-t">대행사 내부 정보 <small>리뷰어·업체 고객에게 안 보임</small></h3><dl class="kv2">'
          f'<dt>연락처</dt><dd>{x["tel"]}</dd><dt>사업자번호</dt><dd>{x["bno"]}</dd><dt>등록일</dt><dd>{x["reg_d"]}</dd></dl>'
          f'<h3 class="sec-t">담당자</h3><div class="assign"><select class="input js-own-sel" aria-label="담당자">'
          f'<option value="">미담당</option>{staff_opts(owner_sel)}</select>'
          f'<button type="button" class="btn primary js-own-save" data-biz="{bid}">변경</button></div>'
          f'<p class="note">바꾸면 이 업체의 진행 캠페인 {len(b["camps"])}개가 모두 새 담당자에게 넘어갑니다 · 이력에 남음</p>'
          f'<h3 class="sec-t">지금 걸린 이슈</h3><div class="ichips">{ichips}</div>')
    cps = "".join(
        f'<li class="cpl cg-{G.ctype(c)}"><div class="cn-l1">{ty_badges(c)}<b>{esc(c)}</b></div>'
        f'<span class="cn-l2">{G.camp_state(b, c)} · 다음 일정 {mdw(min((o for o in camp_dates(b, c).values() if o >= 0), default=0))}</span>'
        f'<a href="schedule.html" class="lk">일정 →</a></li>' for c in b["camps"])
    r = random.Random(77 + int(bid[1:]))
    use = "".join(f'<tr><td>11/{r.randint(1, 9):02d}</td><td>{esc(r.choice(b["camps"]))}</td><td>{r.choice(["예치", "지급", "추가 리워드", "예치금 복귀"])}</td>'
                  f'<td class="num">{r.choice([-55000, -27500, -11000, 16500]):,}P</td></tr>' for _ in range(5))
    rep = ('<ul class="replist"><li><b>11월 보고서</b><span class="st on">켜짐</span><span class="muted">만료 12/9 · 열람 3회</span>'
           '<button type="button" class="btn sm">링크 복사</button></li>'
           '<li><b>10월 보고서</b><span class="st off">만료</span><span class="muted">만료 11/8</span>'
           '<button type="button" class="btn sm">다시 켜기</button></li></ul>'
           '<button type="button" class="btn primary">+ 보고서 링크 만들기</button>'
           '<p class="note">보고서에는 리워드·포인트·수수료 금액이 나오지 않습니다(업체 고객용).</p>')
    memo = ('<textarea class="input memo-in" rows="3" placeholder="업체 메모 (대행사 안에서만 보임)"></textarea>'
            '<button type="button" class="btn sm primary">메모 남기기</button>'
            '<ul class="memos"><li><b>김지은</b> · 11/6<p>사장님이 평일 저녁 방문만 원하심. 주말 체험은 받지 않기로.</p></li></ul>')
    log = "".join(f'<li><span class="muted">{d}</span> {t}</li>' for d, t in
                  [("11/8 14:20", "캠페인 ‘" + esc(b["camps"][0]) + "’ 등록"),
                   ("11/3 10:02", f'담당자 지정 → {b["owner"][1] if b["owner"] else "미담당"}'),
                   ("10/21 09:40", "업체 등록")])
    active = len(b["camps"])
    arch_btn = (f'<button type="button" class="btn ghost-danger" disabled title="진행 캠페인이 있어 보관할 수 없습니다">보관</button>'
                f'<span class="muted small">진행 중 {active}건을 먼저 완료·중단하세요</span>' if active else
                '<button type="button" class="btn ghost-danger">보관</button>')
    return (f'<section class="pane bdrawer" data-bdrawer="{bid}" hidden>{radios}'
            f'<header class="pane-h"><p class="pane-biz">{x["ind"]} · {x["reg"]}</p>'
            f'<h2>{esc(b["name"])}</h2><div class="tabs" role="tablist">{tabbar}</div></header>'
            f'<div class="pane-b">'
            f'<div class="tp tp-ov">{ov}</div><div class="tp tp-cp"><ul class="cplist">{cps}</ul></div>'
            f'<div class="tp tp-use"><table class="mini"><thead><tr><th>일자</th><th>캠페인</th><th>구분</th><th>금액</th></tr></thead>'
            f'<tbody>{use}</tbody></table><p class="note">통포인트 1개에서 쓰고, 업체별로 사용내역만 나눠 봅니다.</p></div>'
            f'<div class="tp tp-rep">{rep}</div><div class="tp tp-memo">{memo}</div><div class="tp tp-log"><ul class="logs">{log}</ul></div>'
            f'</div><footer class="pane-f"><div class="arch">{arch_btn}</div><button type="button" class="btn">정보 수정</button></footer></section>')


def register_dialog():
    return f'''<dialog class="dlg" id="dlg-reg" aria-labelledby="dlg-reg-t">
	<form method="dialog" class="dlg-f">
		<header><h2 id="dlg-reg-t">업체 등록</h2><button value="cancel" class="t-x dark" aria-label="닫기">✕</button></header>
		<fieldset><legend>리뷰어에게 보이는 정보</legend>
			<label>노출명 <input class="input" required placeholder="예: 연남 헤어살롱"></label>
			<label>주소 <input class="input" placeholder="도로명 주소"></label>
			<label>업종 <select class="input">{"".join(f"<option>{i}</option>" for i in INDUSTRY)}</select></label>
			<label>소개 <textarea class="input" rows="2" placeholder="리뷰어가 신청 전에 보는 한두 줄"></textarea></label>
		</fieldset>
		<fieldset><legend>대행사 내부 정보 <small>리뷰어·업체 고객에게 안 보임</small></legend>
			<label>연락처 <input class="input" placeholder="사장님 연락처"></label>
			<label>사업자번호 <input class="input" placeholder="000-00-00000"></label>
			<label>담당자 <select class="input"><option value="">미담당(나중에 배정)</option>{staff_opts()}</select></label>
		</fieldset>
		<footer><button value="cancel" class="btn">취소</button><button value="ok" class="btn primary js-reg-ok">등록</button></footer>
	</form>
</dialog>'''


def biz_page():
    rows = "".join(biz_row(b) for b in BIZS) + archived_rows()
    n_un = sum(1 for b in BIZS if not b["owner"])
    n_iss = sum(1 for b in BIZS if b["issues"])
    body = f'''<section class="board biz-page" aria-labelledby="t-biz">
	<div class="board-h"><div><h1 id="t-biz">업체</h1>
		<p class="sub">업체 {len(BIZS)}곳 · 미담당 <b class="hot-t">{n_un}곳</b> · 보관 {len(ARCHIVED)}곳 · 업체마다 담당자 1명(캠페인은 업체 담당자를 따름)</p></div>
		<button type="button" class="btn primary js-reg">+ 업체 등록</button></div>
	<input type="radio" name="bf" id="bf-all" class="vr" checked><input type="radio" name="bf" id="bf-un" class="vr">
	<input type="radio" name="bf" id="bf-iss" class="vr"><input type="radio" name="bf" id="bf-arch" class="vr">
	<div class="s-tools">
		<label class="search b-search"><span class="sr">업체 검색</span><input type="search" class="js-bsearch" placeholder="업체명·업종·지역"></label>
		<div class="bfs" role="group" aria-label="거르기">
			<label for="bf-all" class="pill">전체 {len(BIZS)}</label><label for="bf-un" class="pill">미담당 {n_un}</label>
			<label for="bf-iss" class="pill">이슈 있음 {n_iss}</label><label for="bf-arch" class="pill">보관함 {len(ARCHIVED)}</label></div>
	</div>
	<div class="bulk" hidden><b class="js-bulk-n">0곳 선택</b>
		<select class="input js-bulk-own" aria-label="새 담당자"><option value="">담당자 고르기</option>{staff_opts()}</select>
		<button type="button" class="btn sm primary js-bulk-apply">담당자 변경</button>
		<button type="button" class="btn sm ghost-danger js-bulk-arch">보관</button>
		<span class="bulk-msg js-bulk-msg" role="status"></span>
		<button type="button" class="btn sm ghost js-bulk-clear">선택 해제</button></div>
	<div class="grid-wrap"><table class="btable">
		<thead><tr><th class="ck"><input type="checkbox" class="js-ckall" aria-label="보이는 업체 모두 선택"></th><th>업체</th><th>업종</th><th>지역</th>
		<th>담당자</th><th>팀</th><th class="num">진행 / 누적</th><th class="num">이번 달 사용</th><th>이슈</th><th>등록</th></tr></thead>
		<tbody>{rows}</tbody></table>
		<p class="empty-row js-bempty" hidden>조건에 맞는 업체가 없습니다</p></div>
</section>{register_dialog()}'''
    panel = ('<div class="pane-empty"><p class="empty-ico" aria-hidden="true">🏠</p><p><b>업체를 고르세요</b></p>'
             '<p class="muted">개요 · 캠페인 · 사용내역 · 보고서 · 메모 · 이력</p></div>'
             + "".join(biz_drawer(b) for b in BIZS))
    return page("업체", "biz", body, panel)


if __name__ == "__main__":
    (ROOT / "schedule.html").write_text(schedule_page(), encoding="utf-8")
    (ROOT / "biz.html").write_text(biz_page(), encoding="utf-8")
    print(f"written schedule.html · biz.html · 업체 {len(BIZS)} · 일정 {len(EVS)}")
