# -*- coding: utf-8 -*-
"""
[2026-11-12 v0.9] 광고주 홈 · 대행사 신청 — 광고주 화면 마크업 그대로(같은 요소·class·순서·문구, PHP 빼고 더미값)
  home.html          홈(home)         ← U:\\admin\\inc\\home\\home.inc.html (틀 · 달력 머리)
                                        + taskToday.inc.html (오늘 할 일 · 다가오는 일정) + taskComplete.inc.html (완료한 할 일)
                                        + script/home/home.js renderCalendar() · renderSampleTimelines() (달력 칸 · 일정 띠 · 띠 팝업)
                                        + core/json/home/schedule.json.html getSchedule (띠 시작·끝 · 단계 라벨 · 색 · 줄)
  agency_apply.html  대행사 신청(agcy) ← U:\\admin\\inc\\agency.inc.html — "완료(ST_DONE)" 갈래(승인된 대행사가 보는 화면)
  광고주가 JS 로 하던 것
    · 오늘 할 일 / 완료한 할 일 바꾸기(taskTab fetch) · 모바일 할 일 / 달력 탭 · 달의 ‹ › 오늘
      = 숨은 라디오 + :has() (css/bridge/home.css) — 달은 9월~다음 1월 다섯 장을 미리 그려 두고 하나만 보인다
    · 달력 칸 · 띠 위치 = home.js 계산을 여기(파이썬)서 그대로 해서 인라인 style 로 박음(광고주도 인라인 style 로 넣는다)
    · 띠 누르기 → 같은 캠페인 띠만 부각 + 팝업 = js/home.js (CSS 로는 "누른 띠와 같은 캠페인의 다른 줄 띠"를 이을 수 없다)
  더미 = camp_data.CAMPS 의 일정(dts) — 모집시작 = rec-7 · 모집마감 = rec · 발표 = sel · 체험시작 = exp · 체험종료 = rev
    (gen_account 포인트 내역의 "모집 7일 전 시작" 과 같은 약속). 오늘 = gen_pages.TODAY
  실행: python -I build/gen_home.py
"""
import calendar
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402

P, G = D.P, D.G
esc = K.esc
TODAY = P.TODAY
WEEK_SUN = "일월화수목금토"                       # PHP date('w') 순서(일=0)
CSS = K.CSS + '<link rel="stylesheet" href="css/bridge/home.css">'

# [2026-11-12 v0.9] 광고주 화면 키 — 대행사 틀(.work.ag) 없이 광고주 뿌리(.content-wrapper · .page-container)를 바로 놓는다
#   gen_pages.ADV_KEYS 에 아직 없으면 이 실행에서만 더한다(새 집합으로 바꿔 끼움 · 파일은 고치지 않음)
P.ADV_KEYS = P.ADV_KEYS | {"home", "agcy"}

# ── 홈 더미 범위 ─────────────────────────────────────
# 광고주 홈은 "내 캠페인" 전부를 띠 한 줄씩 쌓는다(rank = 그 달 캠페인 순번). 대행사 전체(80여 건)를 다 넣으면
#   한 주 줄이 2,000px 을 넘어 화면이 안 읽힌다 → 업체를 앞에서부터 모아 진행 캠페인 HOME_MIN 건이 될 때까지만 쓴다
HOME_MIN = 10
NOMINAL_H = 700                  # 달력 칸 영역 높이 가정(px) — 광고주는 .calendar-grid-container.offsetHeight 로 잰다
THEMES = ["bar-blue", "bar-pink", "bar-green", "bar-purple", "bar-orange"]   # schedule.json.html $theme
MONTHS = [(2026, 9), (2026, 10), (2026, 11), (2026, 12), (2027, 1)]
FIELDS = [("recruitSTDate", "모집시작일"), ("recruitEDDate", "모집마감일"), ("announceDate", "발표일"),
          ("campaignSTDate", "체험시작일"), ("campaignEDDate", "체험종료일")]
DONE_N = 2                       # 오늘 "확인완료" 누른 셈 치는 건수 → 완료한 할 일


# ════════════════ 공통 ════════════════
def write(fname, title, active, body, js):
    out = P.page(title, active, body, None, CSS, js)
    (K.ROOT / fname).write_text(out, encoding="utf-8")
    print(f"written {fname} ({len(out.encode('utf-8')) / 1024:.0f} KB)")


def msi(name):
    return f'<span class="material-symbols-outlined" aria-hidden="true">{name}</span>'


def code(c):
    return 10200 + D.CAMPS.index(c)        # 캠페인 코드 — gen_ops2.code() · gen_campaigns.code() 와 같은 값


def region(b):
    return b["name"].split()[0]            # [지역] — gen_ops2.region() 과 같은 약속


def thumb(c):
    """대표 이미지 자리 — 외부 그림 대신 캠페인마다 색이 다른 한 칸짜리 SVG(<img> 그대로)"""
    hue = random.Random(f"thumb-{c['id']}").randint(0, 359)
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'>"
           f"<rect width='1' height='1' fill='hsl({hue},55%,72%)'/></svg>")
    return "data:image/svg+xml," + quote(svg)


def dates_of(c):
    """광고주 campaignMstr 일정 5칸 → 날짜"""
    d = c["dts"]
    offs = [d["rec"] - 7, d["rec"], d["sel"], d["exp"], d["rev"]]
    return {k: TODAY + timedelta(days=o) for (k, _l), o in zip(FIELDS, offs)}


def date_text(d):
    """dateText($date, "y.m.d.w") → 26.11.09(월)"""
    return f"{d:%y.%m.%d}({WEEK_SUN[(d.weekday() + 1) % 7]})"


def dday(d):
    diff = (d - TODAY).days
    return f"D-{diff}" if diff > 0 else "D-Day" if diff == 0 else f"D+{abs(diff)}"


def area_name(c):
    return f"[{esc(region(c['b']))}] {esc(c['name'])}"


def camp_href(c):
    return f'campaigns.html#c-{c["id"]}'


def pick_camps():
    out = []
    for b in P.BIZS:
        out += [c for c in D.CAMPS if c["bid"] == b["id"] and c["dts"] and c["group"] in D.ACTIVE]
        if len(out) >= HOME_MIN:
            break
    return out


CAMPS = pick_camps()


# ════════════════ 할 일 (getTaskData) ════════════════
def in_range(c, lo, hi):
    return any(lo <= (v - TODAY).days <= hi for v in dates_of(c).values())


def today_due(c):
    """taskToday.inc.html — 체험종료 → 체험시작 → 발표 → 모집마감 → 모집시작 순으로 '오늘 이전' 첫 칸"""
    ds = dates_of(c)
    for k, label in reversed(FIELDS):
        if ds[k] <= TODAY:
            return label, ds[k]
    return None


def next_due(c):
    """taskToday.inc.html 다가오는 일정 — 모집시작 → … → 체험종료 순으로 '오늘 뒤' 첫 칸"""
    ds = dates_of(c)
    for k, label in FIELDS:
        if ds[k] > TODAY:
            return label, ds[k]
    return None


TODAY_ALL = [c for c in CAMPS if in_range(c, -7, 0)]
DONE = TODAY_ALL[-DONE_N:]                                  # campaignMstrCheck 에 오늘 적힌 셈
TODAY_LIST = [c for c in TODAY_ALL if c not in DONE]         # NOT EXISTS campaignMstrCheck
NEXT_LIST = [c for c in CAMPS if in_range(c, 1, 7)]


def type_row(c):
    return (f'<div class="task-type-row"><span class="campaign-id">{code(c)}</span>'
            f'<span class="type-badge type-experience">{area_name(c)}</span></div>')


def task_card(c):
    label, d = today_due(c)
    cls = "normal" if dday(d) == "D-Day" else "urgent"
    return (f'<div class="task-card {cls}" data-biz="{c["bid"]}"><div class="task-meta">'
            f'<span class="task-badge urgent-badge">{dday(d)}</span><span class="task-date">{date_text(d)}</span>'
            f'<span class="task-desc">{label}이에요!</span></div>'
            f'<div class="task-body"><div class="task-thumb"><img src="{thumb(c)}" alt=""></div>'
            f'<div class="task-info">{type_row(c)}<div class="task-actions">'
            f'<a class="btn-tag" href="{camp_href(c)}">상세보기</a>'
            f'<button type="button" class="btn-tag btn-dark js-flash" data-msg="시안: 저장되지 않습니다">확인완료</button>'
            f'</div></div></div></div>')


def done_card(c):
    label, d = today_due(c)
    # ★ 광고주 원본에 날짜 뒤 ')' 가 하나 더 붙어 있다(…(월))) — 그대로 옮김
    return (f'<div class="task-card completed" data-biz="{c["bid"]}"><div class="task-meta">'
            f'<span class="task-date">{date_text(d)})</span><span class="task-desc">{label} 확인 (완료)</span></div>'
            f'<div class="task-body"><div class="task-thumb"><img src="{thumb(c)}" alt=""></div>'
            f'<div class="task-info">{type_row(c)}<div class="task-actions">'
            f'<a class="btn-tag" href="{camp_href(c)}">상세보기</a></div></div></div></div>')


def schedule_item(c):
    label, d = next_due(c)
    return (f'<a class="schedule-item" href="{camp_href(c)}" data-biz="{c["bid"]}">'
            f'<div class="schedule-meta"><span class="schedule-date">{date_text(d)}</span>'
            f'<span class="schedule-note">{label}입니다.</span></div>{type_row(c)}</a>')


def task_area():
    """task-render-area 안 — 오늘 할 일(taskToday) 셋 + 완료한 할 일(taskComplete) 하나를 형제로 두고 라디오로 고른다"""
    return (f'<div class="task-count-msg task-count-msg-active">오늘 확인해야할 일이 '
            f'<span class="count-highlight">{len(TODAY_LIST)}개</span> 있어요!</div>'
            f'<div class="task-list task-list-active">{"".join(task_card(c) for c in TODAY_LIST)}</div>'
            f'<section class="schedule-section"><div class="section-header"><div class="section-title">'
            f'{msi("checklist")}<span>다가오는 일정</span></div></div>'
            f'<div class="schedule-list">{"".join(schedule_item(c) for c in NEXT_LIST)}</div></section>'
            f'<div class="task-list task-list-completed">{"".join(done_card(c) for c in DONE)}</div>')


def left_panel():
    radios = "".join(f'<input type="radio" name="hm-task" id="hm-task-{i}" class="hm-r"{" checked" if i == 0 else ""}>'
                     for i in range(2))
    return (f'<div class="left-panel active-panel"><section class="task-section">{radios}'
            f'<div class="task-toggle-header">'
            f'<label class="task-toggle-btn btn-today-tasks" for="hm-task-0">{msi("checklist")}<span>오늘 할 일</span></label>'
            f'<label class="task-toggle-btn btn-completed-tasks" for="hm-task-1"><span>완료한 할 일</span></label></div>'
            f'<div class="task-render-area" id="task-render-area">{task_area()}</div></section></div>')


# ════════════════ 달력 (renderCalendar · renderSampleTimelines) ════════════════
def grid_of(y, m):
    """[(날짜, row, col, isOther)] — home.js renderCalendar 와 같은 칸"""
    first = (date(y, m, 1).weekday() + 1) % 7
    last = calendar.monthrange(y, m)[1]
    total = -(-(first + last) // 7) * 7
    start = date(y, m, 1) - timedelta(days=first)
    return [(start + timedelta(days=i), i // 7, i % 7, not (first <= i < first + last)) for i in range(total)]


def month_sched(y, m):
    """schedule.json.html getSchedule — 그 달에 일정이 걸린 캠페인 → 띠 자료"""
    lo, last = date(y, m, 1), calendar.monthrange(y, m)[1]
    hi = date(y, m, last)
    inm = lambda d: lo <= d <= hi            # noqa: E731
    out = []
    for c in CAMPS:
        ds = dates_of(c)
        if not any(inm(v) for v in ds.values()):
            continue
        s = {"c": c, "id": code(c), "rank": len(out),
             "start": 1 if ds["recruitSTDate"] <= lo else ds["recruitSTDate"].day,
             "end": last if ds["campaignEDDate"] >= hi else ds["campaignEDDate"].day,
             "theme": random.Random(f"theme-{c['id']}").choice(THEMES), "labels": []}
        if inm(ds["recruitSTDate"]):
            s["labels"].append((ds["recruitSTDate"].day, "모집시작"))
        if ds["recruitEDDate"] != ds["announceDate"] and inm(ds["recruitEDDate"]):
            s["labels"].append((ds["recruitEDDate"].day, "모집종료"))
        if ds["announceDate"] != ds["campaignSTDate"] and inm(ds["announceDate"]):
            s["labels"].append((ds["announceDate"].day, "발표일"))
        if inm(ds["campaignSTDate"]):
            s["labels"].append((ds["campaignSTDate"].day, "체험시작"))
        # ※ 광고주 서버는 campaignEDDate 라벨 값을 보내지 않는다 → '체험종료' 라벨은 안 나온다(그대로)
        out.append(s)
    return out


def idx_of(grid, day):
    return next((i for i, (d, _r, _c, o) in enumerate(grid) if not o and d.day == day), -1)


def radius(first, last_):
    if not first and not last_:
        return "border-radius: 0;"
    if first and not last_:
        return "border-radius: 12px 0px 0px 12px;"
    if not first and last_:
        return "border-radius: 0px 12px 12px 0px;"
    return ""


def bars(grid, rows, sched, row_tops):
    out = []
    for s in sched:
        si, ei = max(0, idx_of(grid, s["start"])), min(len(grid) - 1, idx_of(grid, s["end"]))
        if si > ei:
            continue
        cur = si
        while cur <= ei:
            row = grid[cur][1]
            le = cur
            while le < ei and grid[le + 1][1] == row:
                le += 1
            sc, ec = grid[cur][2], grid[le][2]
            left, width = sc / 7 * 100, (ec - sc + 1) / 7 * 100
            top = row_tops[row] + 40 + s["rank"] * 26
            inner = f'<span class="bar-text" style="padding-left:12px;">{s["id"]}</span>' if cur == si else ""
            for day, text in s["labels"]:
                li = idx_of(grid, day)
                if cur <= li <= le:
                    pct = (grid[li][2] - sc) / (ec - sc + 1) * 100
                    inner += (f'<div class="phase-label" style="left:calc({pct:g}% + 4px);">'
                              f'<span class="phase-arrow"></span>{text}</div>')
            out.append(f'<div class="timeline-bar {s["theme"]}" data-event-id="{s["id"]}" data-cid="{s["c"]["id"]}" '
                       f'data-top="{top}" data-col="{sc}" data-l="{left:g}" data-w="{width:g}" data-biz="{s["c"]["bid"]}" '
                       f'style="top: {top}px; left: calc({left:g}%); width: calc({width:g}%); {radius(cur == si, le == ei)}">'
                       f'{inner}</div>')
            cur = le + 1
    return "".join(out)


def cells(y, m, grid):
    out = []
    for d, row, col, other in grid:
        today = not other and d == TODAY
        cls = "cal-cell" + (" today-cell" if today else " current-week" if row >= 2 and not other else "")
        num = ("today-num" if today else "other-num" if other else "sun-num" if col == 0 else "sat-num" if col == 6 else "")
        out.append(f'<div class="{cls}"><div class="cal-date-num{" " + num if num else ""}">{d.day}</div></div>')
    return "".join(out)


def cal_month(i, y, m):
    grid = grid_of(y, m)
    rows = len(grid) // 7
    sched = month_sched(y, m)
    max_rank = [-1] * rows
    for s in sched:
        si, ei = max(0, idx_of(grid, s["start"])), min(len(grid) - 1, idx_of(grid, s["end"]))
        for k in range(si, ei + 1):
            max_rank[grid[k][1]] = max(max_rank[grid[k][1]], s["rank"])
    default_h = max(60, NOMINAL_H // rows)
    heights = [max(default_h, 40 + (r + 1) * 26 + 10 if r != -1 else default_h) for r in max_rank]
    tops, y_ = [], 0
    for h in heights:
        tops.append(y_)
        y_ += h + 1
    prev_, next_ = max(0, i - 1), min(len(MONTHS) - 1, i + 1)
    today_i = MONTHS.index((TODAY.year, TODAY.month))
    dow = "".join(f'<div class="dow{" sun" if k == 0 else " sat" if k == 6 else ""}">{w}</div>' for k, w in enumerate(WEEK_SUN))
    return (f'<div class="calendar-wrap" data-cal="{i}"><div class="calendar-header"><div class="cal-header-left">'
            f'<div class="cal-year-month"><div class="cal-dropdown-wrap wrap-cal-year"><span class="cal-year">{y}년</span>'
            f'<div class="cal-dropdown-list list-cal-year"></div></div>'
            f'<div class="cal-dropdown-wrap wrap-cal-month"><span class="cal-month">{m}월</span>'
            f'<div class="cal-dropdown-list list-cal-month"></div></div></div>'
            f'<div class="cal-nav-group">'
            f'<label class="cal-nav-btn btn-prev" for="hm-cal-{prev_}" aria-label="이전">{msi("chevron_left")}</label>'
            f'<label class="cal-nav-btn btn-next" for="hm-cal-{next_}" aria-label="다음">{msi("chevron_right")}</label>'
            f'<label class="btn-today" for="hm-cal-{today_i}">오늘</label></div></div></div>'
            f'<div class="cal-day-header">{dow}</div>'
            f'<div class="calendar-grid-container"><div class="cal-grid">'
            f'<div class="cal-dates" style="grid-auto-rows: initial; grid-template-rows: {" ".join(f"{h}px" for h in heights)};">'
            f'{cells(y, m, grid)}</div><div class="timeline-layer">{bars(grid, rows, sched, tops)}</div>'
            f'</div></div></div>')


def popups():
    """띠 팝업 틀(home.js popupHtml 과 같은 마크업) — js/home.js 가 복제해 위치만 정해 붙인다"""
    out = []
    for c in CAMPS:
        out.append(f'<template data-pop="{c["id"]}"><div class="cal-popup" id="cal-popup" mstrCode="{c["id"]}">'
                   f'<div class="popup-body"><div class="popup-thumb"><img src="{thumb(c)}" alt=""></div>'
                   f'<div class="popup-info"><div class="task-type-row">'
                   f'<span class="type-badge type-experience">{G.TYPE_NAME[c["ty"]]}</span>'
                   f'<span class="campaign-id">{code(c)}</span></div>'
                   f'<div class="popup-location-row"><span class="popup-location">[{esc(region(c["b"]))}]</span>'
                   f'<span class="popup-title">{esc(c["name"])}</span></div>'
                   f'<p class="popup-count">신청 {c["applied"]}/ <span>모집 {c["n"]}</span></p>'
                   f'</div></div></div></template>')
    return "".join(out)


def right_panel():
    today_i = MONTHS.index((TODAY.year, TODAY.month))
    radios = "".join(f'<input type="radio" name="hm-cal" id="hm-cal-{i}" class="hm-r"{" checked" if i == today_i else ""}>'
                     for i in range(len(MONTHS)))
    return f'<div class="right-panel">{radios}{"".join(cal_month(i, y, m) for i, (y, m) in enumerate(MONTHS))}</div>'


def home_page():
    radios = "".join(f'<input type="radio" name="hm-mt" id="hm-mt-{i}" class="hm-r"{" checked" if i == 0 else ""}>'
                     for i in range(2))
    body = (f'<div class="content-wrapper">{radios}'
            f'<div class="mobile-home-tabs" role="tablist" aria-label="홈 탭">'
            f'<label class="mobile-tab-btn" for="hm-mt-0" data-target="left">할 일</label>'
            f'<label class="mobile-tab-btn" for="hm-mt-1" data-target="right">달력</label></div>'
            f'<div class="mobile-tab-content-box">{left_panel()}{right_panel()}</div></div>{popups()}')
    write("home.html", "홈", "home", body, "ops.js home.js")


# ════════════════ 대행사 신청 (agency.inc.html · 완료 갈래) ════════════════
AG_COMPANY = "새봄 마케팅"            # 가짜 상호(공개 시안)
AG_HIST = [   # 새 것부터 (step, 신청일 off, tryNo, 반려 사유)
    (2, -21, 2, ""),
    (3, -34, 1, "사업자등록증 사진이 흐려 상호와 등록번호를 읽을 수 없습니다.\n선명한 사본(스캔 또는 PDF)으로 다시 첨부해 주세요."),
]
STEP = {0: ("접수", "badge--gray"), 1: ("심사", "badge--info"), 2: ("완료", "badge--success"), 3: ("반려", "badge--danger")}


def ymd(off):
    return f"{TODAY + timedelta(days=off):%Y.%m.%d}"


def nl2br(t):
    return "<br />\n".join(esc(x) for x in t.split("\n"))


def try_no(n):
    return f"· {n}차" if n > 1 else ""


def status_section():
    step, off, n, _r = AG_HIST[0]
    label, cls = STEP[step]
    return (f'<section class="mp-section"><div class="mp-section-header">'
            f'<span class="material-symbols-outlined icon-mid">handshake</span><h3 class="mp-section-title">대행사 신청</h3></div>'
            f'<div class="mp-info-list"><dl class="mp-info-row"><dt>진행 상태</dt><dd>'
            f'<span class="badge {cls}">{label}</span>'
            f'<span style="color:#777;font-size:13px;"> · {ymd(off)} 신청 {try_no(n)}</span>'
            f'<p style="margin:8px 0 0;font-size:14px;line-height:1.9;color:#0e0e0e;">'
            f'<strong>대행사 등록이 완료되었습니다.</strong></p></dd></dl></div></section>')


def history_section():
    rows = []
    for step, off, n, reason in AG_HIST:
        label, cls = STEP[step]
        why = (f'<div style="margin-top:4px;color:#8a2b2b;line-height:1.9;">반려 사유 : {nl2br(reason)}</div>'
               if step == 3 and reason.strip() else "")
        rows.append(f'<div style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;line-height:1.9;">'
                    f'<span class="badge {cls}">{label}</span>'
                    f'<strong style="margin-left:6px;">{esc(AG_COMPANY)}</strong>'
                    f'<span style="color:#777;font-size:13px;"> · {ymd(off)} {try_no(n)}</span>{why}</div>')
    return (f'<section class="mp-section"><div class="mp-section-header">'
            f'<span class="material-symbols-outlined icon-mid">history</span><h3 class="mp-section-title">신청 이력</h3></div>'
            f'<div style="padding:4px 0;">{"".join(rows)}</div></section>')


def agency_page():
    foot = ('<div style="margin:16px 0 0;padding:12px 14px;background:#f7f8fb;border-radius:8px;font-size:13px;line-height:1.8;color:#555;">'
            '신청하시면 운영자가 사업자등록증을 확인한 뒤 <strong>완료 또는 반려</strong>로 처리합니다.\n'
            '결과는 알림으로 알려 드립니다.<br />\n'
            '반려되어도 내용을 보완해 <strong>다시 신청</strong>하실 수 있고, 지난 신청과 이어서 보입니다.<br />\n'
            '담당자명·연락처·이메일은 <strong>암호화해 보관</strong>하며, 사업자등록증은 외부에서 열 수 없는 자리에 둡니다.</div>')
    # 완료(ST_DONE) 갈래 = 신청 폼 없음($agCanApply 거짓) → 지금 상태 · 신청 이력 · 아래 안내
    body = (f'<div class="page-container mp-container"><div class="mp-card">'
            f'{status_section()}{history_section()}{foot}</div></div>')
    write("agency_apply.html", "대행사 신청", "agcy", body, "ops.js")


if __name__ == "__main__":
    home_page()
    agency_page()
