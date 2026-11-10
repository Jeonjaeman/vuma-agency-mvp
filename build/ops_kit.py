# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 운영·계정·팀 화면 공통 조각 — 광고주 화면 구성을 옮길 때 같은 모양으로 찍어 내기
  tabs()  = 라디오 탭(css/ops.css .ot — 번호 순서로 묶임)
  table() = 머리 + 줄 표(.otable), 업체·담당자 칸은 class="col-biz"(한 업체 범위면 숨김 · Q18)
  pop()   = popover 창(JS 없음)
  write() = 셸(gen_pages.page)로 감싸 파일 쓰기 (메뉴에 켜기 = gen_dashboard.READY 에 키 추가)
"""
import html

import gen_pages as P

G = P.G
esc = html.escape
ROOT = G.ROOT
CSS = '<link rel="stylesheet" href="css/ops.css">'


def won(n):
    return f"{n:,}P"


def badge(cls, text):
    return f'<span class="st {cls}">{text}</span>'


def add_tag(text="대행사"):
    """광고주 화면에 없는 대행사 추가분 표시"""
    return f'<span class="add-tag">{text}</span>'


def head(title, sub="", right="", legend=True):
    lg = '<p class="legend-add"><i></i>점선 = 광고주 화면에 없는 대행사 추가분</p>' if legend else ""
    return (f'<div class="board-h"><div><h1>{title}</h1>{f"<p class=sub>{sub}</p>" if sub else ""}{lg}</div>'
            f'<div class="h-r">{right}</div></div>')


def tabs(name, items, checked=0):
    """items = [(탭 이름, 본문 html)] — 탭 이름에 <em>숫자</em> 를 넣어도 됨"""
    radios = "".join(f'<input type="radio" name="{name}" id="{name}-{i}" class="tr"{" checked" if i == checked else ""}>'
                     for i in range(len(items)))
    labels = "".join(f'<label for="{name}-{i}">{lab}</label>' for i, (lab, _b) in enumerate(items))
    panes = "".join(f'<section class="tp">{body}</section>' for _l, body in items)
    return f'<div class="ot">{radios}<nav class="otabs" aria-label="탭">{labels}</nav>{panes}</div>'


def table(heads, rows, ck=False, bulk=""):
    """heads = [(이름, 칸 class)] · rows = [(tr 속성 문자열, [칸 html...])]"""
    th = (('<th class="ck"><input type="checkbox" class="js-ckall" aria-label="모두 고르기"></th>' if ck else "")
          + "".join(f'<th scope="col" class="{c}">{h}</th>' for h, c in heads))
    trs = []
    for attrs, cells in rows:
        tds = "".join(f'<td class="{heads[i][1]}">{v}</td>' for i, v in enumerate(cells))
        trs.append(f'<tr {attrs}>{"<td class=ck><input type=checkbox aria-label=고르기></td>" if ck else ""}{tds}</tr>')
    body = "".join(trs) or f'<tr><td colspan="{len(heads) + ck}" class="empty">내역이 없습니다</td></tr>'
    return (f'<div class="owrap"><table class="otable"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'
            f'{f"<div class=obulk>{bulk}</div>" if bulk else ""}</div>')


def fbar(*parts, count=None):
    cnt = f'<span class="sp"></span><span class="cnt">{count}</span>' if count is not None else ""
    return f'<div class="fbar">{"".join(parts)}{cnt}</div>'


def select(label, options):
    opts = "".join(f"<option>{o}</option>" for o in options)
    return f'<label><span class="sr">{label}</span><select aria-label="{label}">{opts}</select></label>'


def search(ph):
    return f'<input type="search" placeholder="{ph}" aria-label="{ph}">'


def dates():
    return '<input type="date" aria-label="시작일" value="2026-10-10"> ~ <input type="date" aria-label="끝일" value="2026-11-09">'


def btn(label, msg="", cls="btn sm", pop=""):
    if pop:
        return f'<button type="button" class="{cls}" popovertarget="{pop}">{label}</button>'
    return f'<button type="button" class="{cls} js-flash" data-msg="{esc(msg or "시안: 저장되지 않습니다")}">{label}</button>'


def pop(pid, title, body, ok="저장", msg=""):
    return (f'<div id="{pid}" class="pop" popover><header><h2>{title}</h2>'
            f'<button type="button" class="btn sm" popovertarget="{pid}" popovertargetaction="hide">닫기</button></header>'
            f'<div class="pop-b">{body}</div><footer>'
            f'<button type="button" class="btn" popovertarget="{pid}" popovertargetaction="hide">취소</button>'
            f'{btn(ok, msg, "btn primary")}</footer></div>')


# 광고주 캠페인 상단 탭(campaignTabs.inc.html) 그대로 — 포인트 지급 확인은 탭에 없음(사이드바만)
CTOP = [("camp", "캠페인 리스트", "campaigns.html"), ("rvw", "리뷰어 관리", "reviewers.html"),
        ("photo", "리뷰 사진 관리", "photos.html"), ("srch", "검색결과 리포트", "search_report.html"),
        ("insp", "리뷰 검수", "inspect.html"), ("video", "영상 제작 요청", "video.html")]


def camp_tabs(active):
    n = G.COUNTS.get("review", 0)
    em = f'<em>{n if n < 100 else "99+"}</em>' if n else ""      # 검수 대기 수(99 넘으면 99+)
    links = "".join(f'<a href="{href}" class="{"on" if k == active else ""}"{" aria-current=page" if k == active else ""}>{lab}'
                    f'{em if k == "insp" else ""}</a>'
                    for k, lab, href in CTOP)
    return f'<nav class="ctop" aria-label="캠페인 관리 탭">{links}</nav>'


def biz_cell(b):
    return f'<a href="biz.html#biz={b["id"]}">{esc(b["name"])}</a>'


def owner_of(b):
    return b["owner"][1] if b["owner"] else "미담당"


def write(fname, title, active, body, js="ops.js"):
    (ROOT / fname).write_text(P.page(title, active, f'<section class="ops">{body}</section>', None, CSS, js), encoding="utf-8")
    print(f"written {fname}")
