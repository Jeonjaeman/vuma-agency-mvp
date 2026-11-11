# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 리스트 · 캠페인 상세 — 광고주 사이트 구성 그대로(구조재설계_v0.8안 · 조사\광고주_운영화면_스펙)
  광고주: campaign.inc.html(리스트) · campaignView.inc.html(상세: 캠페인 상세보기 · 캠페인 신청자 · 선정된 리뷰어 · 상태변경 히스토리)
  대행사 추가분(.add 점선): 업체·담당자 줄 · 진행 단계 칩 · 걸린 이슈 · 복제 · 보고서 탭 · 담당자 거르기 · 급한 순 정렬
  캠페인 상세 열기·탭 = 주소 #c-<id>[-탭] + CSS :target (대시보드·일정·업체에서 그 탭으로 바로 연결)
  상태 탭 · 채널/유형 · 정렬(order) · 썸네일형/목록형 · 이미지 빼고 보기 = 라디오/체크박스 + CSS. 검색·담당자·선정 표시만 js/campaigns.js.
  실행: python -I build/gen_campaigns.py  →  mvp/campaigns.html · mvp/campaign_new.html
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import camp_new  # noqa: E402
import gen_reports as R  # noqa: E402  (보고서 공개 화면 주소 — 꺼짐·만료면 그 상태 화면)
import ops_kit as K  # noqa: E402

P, G = D.P, D.G
esc = P.esc
TABS = [("ov", "캠페인 상세보기"), ("app", "캠페인 신청자"), ("rev", "선정된 리뷰어"), ("log", "상태변경 히스토리"), ("rep", "보고서")]
# 대시보드 이슈 → 캠페인 상세 탭
ISSUE_TAB = {"apply": "app", "select": "app", "prep": "rev", "review": "rev", "nudge": "rev", "pay": "rev",
             "point": "ov", "late": "app", "owner": "ov"}

# 광고주 캠페인 상태($CAMPAIGN_STEP) — (코드, 이름, 배지 색)
STEPS = [(1, "미승인", "st-orange"), (2, "검토중", "st-orange"), (3, "승인완료", "st-blue"), (4, "모집중", "st-green"),
         (5, "모집완료", "st-gray"), (6, "체험단선정완료", "st-blue"), (7, "체험중", "st-green"), (8, "완료", "st-gray"),
         (21, "숨김", "st-blue"), (22, "반려", "st-red"), (23, "임시저장", "st-gray"), (24, "취소", "st-gray")]
STEP = {k: (n, cls) for k, n, cls in STEPS}
# 대행사 진행 단계(기획서 4장) → 광고주 상태 코드
TO_STEP = {"작성 중": 23, "승인 대기": 2, "모집 중": 4, "선정 중": 5, "체험 중": 7, "배송·체험 중": 7, "원고 작성 중": 7,
           "리뷰 중": 7, "정산 중": 7, "완료": 8, "중단": 24}
PROGRESS = [3, 4, 5, 6, 7, 8]          # 상세 위 진행 막대(광고주는 모든 상태를 › 로 잇지만 정상 흐름만 보임)


def step_of(c):
    k = TO_STEP[c["state"]]
    if k == 7 and c["dts"] and c["dts"]["exp"] > 0:
        k = 6                              # 선정은 끝났고 체험 시작 전 = 체험단선정완료
    return k


def region(b):
    return b["name"].split()[0]


def code(c):
    return 10200 + D.CAMPS.index(c)        # 캠페인 코드(시안 — 화면 안에서만 고유)


def reg_off(c):
    """등록일(오늘 기준 일수) — 최신순/과거순 정렬"""
    if not c["dts"]:
        return -random.Random(c["id"]).randint(0, 3)
    return c["dts"]["rec"] - 7


def step_badge(c):
    n, cls = STEP[step_of(c)]
    return f'<span class="st {cls}">{n}</span>'


def stage_chip(c):
    """대행사 진행 단계(광고주 상태보다 잘게) — 대시보드 이슈와 같은 말"""
    late = '<span class="st st-red">마감 지남</span>' if c["late"] else ""
    return f'<span class="stage add">{c["state"]}</span>{late}'


def owner_html(b):
    return (f'<span class="who"><i>{b["owner"][1][0]}</i>{b["owner"][1]}</span>' if b["owner"]
            else '<span class="who none">미담당</span>')


def offer(c):
    """제공내용(리뷰어에게 보이는 줄)"""
    # 실서버 등록 칸 예시("5만원 상당 자유 체험권") 꼴 + 포인트 지급 "1인당 ___ P"
    worth = {5000: "3만원", 10000: "5만원", 15000: "7만원", 30000: "10만원"}[c["reward"]]
    return {"v": f'{worth} 상당 자유 체험권 · 1인당 {c["reward"]:,}P',
            "s": f'{worth} 상당 제품 배송 · 1인당 {c["reward"]:,}P', "p": f'원고료 1인당 {c["reward"]:,}P · 보도자료 제공'}[c["ty"]]


def dday(c):
    nd = D.next_due(c)
    if not nd:
        return ""
    k, off = nd
    lab = P.EXP_LABEL[c["ty"]] if k == "exp" else dict(P.KIND)[k]
    return f'<span class="dd {G.due_class(off)}" title="{lab} {P.md(off)}">{G.due_label(off)}</span>'


# ════════════════════════ 리스트(카드) ════════════════════════
def issue_chip(c):
    n_iss = sum(n for n, _d in c["iss"].values())
    if not n_iss:
        return ""
    hot = any(d <= 0 for _n, d in c["iss"].values())
    first = next(iter(c["iss"]))
    return (f'<a class="ichip add {"is-hot" if hot else "is-later"}" href="#c-{c["id"]}-{ISSUE_TAB[first]}" '
            f'title="걸린 이슈 — 대시보드와 같은 숫자">이슈 {n_iss}</a>')


def card_btns(c):
    g = c["group"]
    rr = (f'<button type="button" class="btn sm" popovertarget="pop-rr">추가모집 요청</button>' if g in D.ACTIVE
          else '<button type="button" class="btn sm" disabled>추가모집 요청</button>')
    ask = f'1:1 문의 — [{code(c)}] {c["name"]} 문의로 시작합니다'
    return (f'<a class="btn sm primary" href="#c-{c["id"]}">캠페인보기</a>'
            f'{K.btn("문의", ask)}'
            f'{rr}{K.btn("공유", "공유 링크를 복사했습니다")}'
            f'<button type="button" class="btn sm" popovertarget="pop-edit">캠페인수정</button>'
            f'<a class="btn sm add" href="campaign_new.html#copy={c["id"]}" title="대행사 추가 — 같은 업체 다음 회차 · 다른 업체 1회차">복제</a>')


def card(c, i_new, i_due):
    b = c["b"]
    sid = b["owner"][0] if b["owner"] else "un"
    k = step_of(c)
    n, _cls = STEP[k]
    rec = (f'신청 <b>{c["applied"]}</b> / 모집 <b>{c["n"]}</b>' if c["group"] != "draft" else f'신청 0 / 모집 {c["n"]}')
    return (f'<article class="ccard crow k{k} t-{c["ty"]} ch-{c["ch"]}" data-owner="{sid}" data-biz="{b["id"]}" '
            f'data-name="{esc(b["name"])} {esc(c["name"])} {code(c)}" style="--o:{i_new};--d:{i_due}">'
            f'<a class="thumb th-{c["ty"]}" href="#c-{c["id"]}"><span class="th-st">{step_badge(c)}{dday(c)}</span>'
            f'<span class="th-ty">{G.TYPE_NAME[c["ty"]]}</span></a>'
            f'<div class="cbody"><p class="tags"><span class="tg tg-ty">{G.TYPE_NAME[c["ty"]]}</span>'
            f'<span class="tg">{P.guess_ind(b["name"])}</span><span class="tg">{c["ch"]}</span><span class="tg">#{code(c)}</span>'
            f'{" <span class=tg-rr>추가모집</span>" if c["round"] > 1 and c["id"].endswith("x0") else ""}</p>'
            f'<h3><a href="#c-{c["id"]}">[{region(b)}] {esc(c["name"])}</a> <small class="rnd">{c["round"]}회차</small></h3>'
            f'<p class="offer">{esc(offer(c))}</p>'
            f'<p class="cmeta">{rec} {stage_chip(c)} {issue_chip(c)}</p>'
            f'<p class="cbiz col-biz add">{esc(b["name"])} · {owner_html(b)}</p>'
            f'<div class="cbtns">{card_btns(c)}</div></div></article>')


def list_style():
    """상태 탭 · 채널 · 유형 · 정렬 규칙 — 상태 코드가 12개라 생성해서 넣는다"""
    st = "".join(f'#cs-{k}:checked ~ .cgrid .ccard:not(.k{k}){{display:none}}' for k, _n, _c in STEPS)
    st += ",".join(f'#cs-{k}:checked ~ .stabs label[for=cs-{k}]' for k in ["all"] + [k for k, _n, _c in STEPS])
    st += "{color:var(--c-14);border-bottom-color:var(--ag-main)}"
    for ch in sorted({c["ch"] for c in D.CAMPS}):
        st += f'.camp-page:has(#cc-{ch}:not(:checked)) .ccard.ch-{ch}{{display:none}}'
    for t in G.TYPE_NAME:
        st += f'.camp-page:has(#ct-{t}:not(:checked)) .ccard.t-{t}{{display:none}}'
    return f'<style>/* [2026-11-10 v0.8] 생성된 거르기 규칙 — gen_campaigns.list_style() */{st}</style>'


def drop(name, label, items):
    """체크 상자 드롭다운(광고주 '채널전체'·'유형전체') — <details> 로 열고 닫기"""
    cks = "".join(f'<label><input type="checkbox" id="{name}-{k}" checked> {v}</label>' for k, v in items)
    return f'<details class="ckdrop"><summary>{label}</summary><div class="ckd-b">{cks}</div></details>'


def list_view():
    cnt = {k: sum(1 for c in D.CAMPS if step_of(c) == k) for k, _n, _c in STEPS}
    radios = (f'<input type="radio" name="cs" id="cs-all" class="vr" checked>'
              + "".join(f'<input type="radio" name="cs" id="cs-{k}" class="vr">' for k, _n, _c in STEPS))
    stabs = (f'<label for="cs-all">전체 <b>{len(D.CAMPS)}</b></label>'
             + "".join(f'<label for="cs-{k}">{n} <b>{cnt[k]}</b></label>' for k, n, _c in STEPS))
    chans = sorted({c["ch"] for c in D.CAMPS})
    owners = '<option value="">담당자 전체</option><option value="un">미담당</option>' + "".join(
        f'<option value="{sid}">{name} ({t})</option>' for sid, name, _l, t in G.STAFF)
    by_new = sorted(D.CAMPS, key=lambda c: -reg_off(c))
    by_due = sorted(D.CAMPS, key=lambda c: (D.next_due(c) or ("", 999))[1])
    i_new = {c["id"]: i for i, c in enumerate(by_new)}
    i_due = {c["id"]: i for i, c in enumerate(by_due)}
    cards = "".join(card(c, i_new[c["id"]], i_due[c["id"]]) for c in by_new)
    return f'''<div class="clist">
	{K.head("캠페인 리스트", "광고주 캠페인 리스트와 같은 화면 — 업체 범위를 고르면 그 업체 광고주 화면과 같아집니다",
            '<label class="search"><span class="sr">캠페인 찾기</span><input type="search" class="js-csearch" placeholder="캠페인 찾기"></label>'
            '<a class="btn primary" href="campaign_new.html">+ 새 캠페인 등록</a>')}
	{K.camp_tabs("camp")}
	<input type="radio" name="so" id="so-new" class="vr" checked><input type="radio" name="so" id="so-old" class="vr"><input type="radio" name="so" id="so-due" class="vr">
	<input type="radio" name="vw" id="vw-grid" class="vr" checked><input type="radio" name="vw" id="vw-list" class="vr"><input type="checkbox" id="noimg" class="vr">
	{radios}
	<nav class="stabs" aria-label="캠페인 상태">{stabs}</nav>
	<div class="fbar">
		{drop("cc", "채널전체", [(c, c) for c in chans])}
		{drop("ct", "유형전체", list(G.TYPE_NAME.items()))}
		<span class="seg sm sorts"><label for="so-new">최신순</label><label for="so-old">과거순</label><label for="so-due" class="add">기한 급한 순</label></span>
		<select class="js-cown add" aria-label="담당자">{owners}</select>
		<span class="sp"></span>
		<label class="noimg-l" for="noimg">이미지 빼고 보기</label>
		<span class="seg sm views"><label for="vw-grid" title="썸네일형">▦</label><label for="vw-list" title="목록형">☰</label></span>
	</div>
	<div class="cgrid">{cards}</div>
	<p class="empty js-cempty" hidden>조건에 맞는 캠페인이 없습니다</p>
</div>'''


# ════════════════════════ 상세: 캠페인 상세보기 ════════════════════════
def progress(c):
    now = step_of(c)
    if now not in PROGRESS:
        return f'<p class="cprog off">{step_badge(c)} <span class="muted">진행 막대는 승인 뒤부터 보입니다</span></p>'
    d = c["dts"] or {}
    sub = {3: f'모집마감 {G.due_label(d.get("rec", 0))}', 4: f'발표일 {P.md(d.get("sel", 0))}',
           5: f'체험시작 {P.md(d.get("exp", 0))}', 6: f'체험시작 {P.md(d.get("exp", 0))}',
           7: f'리뷰마감 {P.md(d.get("rev", 0))}', 8: "완료"}
    lis = "".join(f'<li class="{"now" if k == now else "past" if PROGRESS.index(k) < PROGRESS.index(now) else ""}">'
                  f'<b>{STEP[k][0]}</b>{f"<small>{sub[k]}</small>" if k == now else ""}</li>' for k in PROGRESS)
    return f'<ol class="cprog">{lis}</ol>'


def tab_ov(c):
    b, ty = c["b"], c["ty"]
    x = P.extra(b)
    # 안내문 · 미션 = 실서버 등록 화면 기본 문구(campaignCreate.inc.html L115-139) · 리뷰 미션 칸($CHARLEN · $IMGCNT)
    place = {"v": ("방문/예약", f'[{x["reg"]}] · 리뷰어와 일정협의 · 체험시간 주중 13:00 ~ 18:00<br>'
                               '★방문 2~3일전 반드시 예약 문의 후 방문 부탁 드립니다.<br>예약 문의가 없을 시 체험이 불가능 할 수 있으니 유의 바랍니다.<br>★당일 체험 불가'),
             "s": ("배송안내", "택배, 순차발송 · 배송정보는 선정 후 확인"),
             "p": ("전달 자료", "보도자료 · 이미지 · 가이드라인 — 선정된 리뷰어 탭 '리뷰어에게 전달할 자료'")}[ty]
    ch_guide = {"인스타": "표시광고법에 따라 #협찬 해시태그를 맨앞에 표기해주세요.", "릴스": "표시광고법에 따라 #협찬 해시태그를 맨앞에 표기해주세요.",
                "쇼츠": "표시광고법에 따라 영상 설명 맨 앞에 #협찬 을 표기해주세요.",
                "구매평": "구매평에 지정한 검색 키워드를 포함해주세요. 대가를 받아 작성한 후기임을 함께 밝혀주세요."
                }.get(c["ch"], "위의 키워드 중 제목, 본문, #태그에 아래와 같이 키워드를 기재해주세요.")
    r = random.Random("mis-" + c["id"])
    mission = f'키워드 필수 · {"지도 필수 · " if ty == "v" else ""}글자 수 {r.choice([800, 1000, 1200, 1500])}자 이상 · 이미지 {r.choice([5, 10, 15])}개 이상'
    body = (f'<section><h3 class="sec-t">제공내용</h3><p>{esc(offer(c))}</p></section>'
            f'<section><h3 class="sec-t">{place[0]}</h3><p>{place[1]}</p></section>'
            f'<section><h3 class="sec-t">채널별 키워드</h3><p>{c["ch"]} · #{region(b)}{P.guess_ind(b["name"])} #{esc(b["name"].split()[-1])}<br>'
            f'<span class="muted">{ch_guide}</span></p></section>'
            f'<section><h3 class="sec-t">가이드라인/요청사항</h3><p>{mission}<br>● 위치 정보(지도 첨부), 운영 시간을 반드시 함께 작성해 주세요.</p></section>'
            '<section><h3 class="sec-t">NOTICE</h3><p class="muted">리뷰 마감일까지 미등록 시 리뷰 미제출 패널티(3점 · 30일 신청 제한) · 유예 7일</p></section>')
    if c["dts"]:
        tl = "".join(f'<li class="tl k-{k}{" past" if c["dts"][k] < 0 else ""}{" now" if c["dts"][k] == 0 else ""}"><i></i>'
                     f'<b>{P.EXP_LABEL[ty] if k == "exp" else lab}</b><span>{P.mdw(c["dts"][k])}</span></li>' for k, lab in P.KIND)
        sched = f'<ol class="timeline">{tl}</ol>'
    else:
        sched = '<p class="muted">임시저장 — 일정을 아직 정하지 않았습니다.</p>'
    side = (f'<dl class="kv2"><dt>유형 · 채널</dt><dd>{P.ty_badges(c["name"])}</dd><dt>모집</dt><dd>{c["n"]}명</dd>'
            f'<dt>1인당 지급</dt><dd>{c["reward"]:,}P</dd><dt>예치</dt><dd>{c["deposit"]:,}P '
            f'<small class="muted">(통포인트에서 · 수수료 {int(D.FEE * 100)}%)</small></dd></dl>{sched}')
    chips = "".join(f'<a class="ichip {G.due_class(d)}" href="dashboard.html#open={b["id"]}-{k}">{G.ISSUE_NAME[k]} {n}<small>{G.due_label(d)}</small></a>'
                    for k, (n, d) in c["iss"].items()) or '<span class="muted">걸린 이슈가 없습니다</span>'
    return (f'<div class="ov2"><div class="ov-main">{body}</div><aside class="ov-side card">{side}</aside></div>'
            f'<section class="card add"><h3 class="sec-t">걸린 이슈 {K.add_tag()} <small>처리는 대시보드에서 · 같은 숫자</small></h3><div class="ichips">{chips}</div></section>')


# ════════════════════════ 상세: 캠페인 신청자 ════════════════════════
def reviewer_cell(a):
    bi, h = a["bi"], a["hist"]
    r = random.Random(a["nick"])
    meta = f'{r.choice(["서울", "경기", "인천", "부산"])} · {r.choice([20, 30, 40])}대 · {r.choice(["여", "남"])}'
    grade = (f'<span class="bgrade g-{ {"최적화": "a", "준최적화": "b"}.get(bi["grade"], "c") }">{bi["grade"]}</span> {bi["score"]}'
             if bi else '<span class="muted">지수 없음</span>')
    ours = (f'<span class="add chip">우리 대행사 {h["ours"]}회 · 평점 {h["rating"]}</span>' if h and h["ours"] else "")
    return (f'<b>{a["nick"]}</b> <span class="muted">| {meta} |</span> {grade} {ours}'
            f'<br><a href="#" class="blog-open js-blog">blog.naver.com/{a["nick"]} ↗</a>')


def app_act(c, a, can):
    if a["st"] == "cancel":
        return ""
    if a["st"] == "sel":
        if c["group"] in ("rec", "sel"):
            return '<span class="st st-blue">선정대기</span> <button type="button" class="btn sm js-unpick">해제</button>'
        return '<span class="st st-green">선정완료</span> ' + K.btn("패널티", pop="pop-pen") + K.btn("취소", "선정을 취소했습니다 · 추가 비용 없음")
    if can:
        need = not a["bi"] and not a["hist"]
        lock = ' disabled title="블로그를 먼저 확인하세요(대행사 규칙)"' if need else ""
        return f'<button type="button" class="btn sm primary js-pick"{lock}>선정</button>'
    return '<span class="muted">미선정</span>'


def tab_app(c):
    if c["group"] == "draft":
        return '<p class="empty-tab">신청자가 없습니다.</p>'
    can = c["group"] in ("rec", "sel")
    wait = sum(1 for a in c["rows"] if a["st"] == "sel") if can else 0
    done = c["sel"] if not can else 0
    rows = []
    for i, a in enumerate(c["rows"], 1):
        part = f'🚩 {a["hist"]["part"]}회' if a["hist"] else "-"
        rows.append(f'<tr class="arow a-{a["st"]}{" need-check" if not a["bi"] and not a["hist"] else ""}"><td class="num">{i}</td>'
                    f'<td><span class="ava">{a["nick"][0]}</span></td><td>{reviewer_cell(a)}</td>'
                    f'<td class="muted">"{a["memo"]}"</td><td>{part}</td><td class="js-ast">{app_act(c, a, can)}</td></tr>')
        if a["st"] == "cancel":
            rows.append(f'<tr class="creq"><td colspan="6"><b>선정취소 요청</b> <span class="muted">11/8 · 일정이 맞지 않아요</span> '
                        f'<span class="muted">취소해도 추가 비용은 없습니다 · 비는 자리는 신청자 중에서 다시 선정하세요</span> '
                        f'{K.btn("선정취소", "선정을 취소했습니다")}{K.btn("요청 거절", "요청을 거절했습니다")}{K.btn("패널티", pop="pop-pen")}</td></tr>')
    more = (f'<p class="muted small">신청 {c["applied"]}명 중 {D.SHOW_APPS}명만 그려 둠(시안) — 실제는 페이지 넘김</p>' if c["applied"] > D.SHOW_APPS else "")
    confirm = (f'<div class="cbar">선정대기 <b class="js-wait">{wait}</b>명이 있습니다. 최종 확인(발표) 시 신청자에게 알림이 발송되고 사용자 화면에 노출됩니다. '
               f'{K.btn("선정 확정/발표", "선정을 발표했습니다 · 알림 발송", "btn sm primary")}</div>' if can else "")
    left = max(0, c["n"] - (wait if can else done))
    return (f'<p class="note">리뷰어의 정보를 꼼꼼히 확인하신 후 캠페인 진행에 적합한 리뷰어를 선정해주세요. 선정되지 않은 리뷰어의 정보는 선정 완료 또는 캠페인 완료 후 삭제됩니다.</p>'
            f'<p class="tab-sum">모집 <b>{c["n"]}</b> | 신청 <b>{c["applied"]}</b> | 선정대기 <b class="js-wait">{wait}</b> | 선정확정 <b>{done}</b> | 남은 자리 <b>{left}</b> '
            f'<label class="small"><input type="checkbox"> 예전에 취소된 줄까지 보기</label></p>{confirm}'
            f'<table class="otable atable"><thead><tr><th class="num">번호</th><th>사진</th><th>리뷰어</th><th>신청메세지</th><th>참여이력</th><th>선정</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>{more}'
            f'<p class="note add">대행사 규칙: 블로그지수·참여이력이 둘 다 없는 첫 참여 리뷰어는 블로그를 열어 본 뒤 선정할 수 있습니다.</p>')


# ════════════════════════ 상세: 선정된 리뷰어 ════════════════════════
REV = {"pend": ("st-purple", "검수대기"), "ok": ("st-green", "승인"), "fix": ("st-red", "반려"), "unreg": ("st-gray", "미제출")}
PAY = {"wait": "지급대기", "done": "지급완료", "noacc": "확인 필요"}


def rev_cell(c, v):
    cls, lab = REV[v["st"]]
    b = c["b"]
    if v["st"] == "pend":
        act = f'<a class="btn sm primary" href="inspect.html?biz={b["id"]}">검수</a>'
    elif v["st"] == "fix":
        act = K.btn("승인", "승인했습니다") + K.btn("재검수 요청", "재검수를 요청했습니다")
    elif v["st"] == "ok":
        act = K.btn("재검수 요청", "재검수를 요청했습니다")
    else:
        act = ""
    link = "" if v["st"] == "unreg" else ' <a href="#" class="ext">리뷰 보기 ↗</a>'
    return f'<span class="st {cls}">{lab}</span>{link} <div class="acts">{act}</div>'


def tab_rev(c):
    if c["group"] in ("draft", "rec"):
        return '<p class="empty-tab">선정된 리뷰어가 없습니다.</p>'
    revs = c["revs"] or [{"nick": a["nick"], "ch": c["ch"], "st": "unreg", "ago": 0} for a in c["rows"] if a["st"] == "sel"]
    pays = {p["nick"]: p for p in c["pays"]}
    rows = []
    for i, v in enumerate(revs, 1):
        p = pays.get(v["nick"])
        pay = (f'<a href="payout.html?biz={c["bid"]}" class="pst">{PAY[p["st"]]}</a>' if p else '<span class="muted">-</span>')
        ship = '<br><small class="muted">배송정보 · 서울 마포구 ··· (선정 후 3개월 보관)</small>' if c["ty"] == "s" else ""
        rows.append(f'<tr><td class="ck"><input type="checkbox" aria-label="고르기"></td><td class="num">{i}</td>'
                    f'<td><span class="ava">{v["nick"][0]}</span></td><td><b>{v["nick"]}</b> <span class="muted">· {v["ch"]}</span>{ship}</td>'
                    f'<td>🚩 {random.Random(v["nick"]).randint(1, 12)}회</td><td>{rev_cell(c, v)}</td>'
                    f'<td class="add">{pay}</td><td><button type="button" class="btn sm icon js-flash" data-msg="쪽지 창(시안)" aria-label="쪽지">✉</button></td></tr>')
    mat = ('<details class="mats"><summary><b>리뷰어에게 전달할 자료</b> <span class="muted">보도자료·이미지·가이드라인을 올려 두면 선정된 리뷰어가 마이캠페인에서 바로 받아 봅니다. 등록하면 알림이 갑니다.</span></summary>'
           '<div class="fl-row"><input type="text" placeholder="제목 (필수 · 예: 보도자료 및 이미지)"><select><option>선정자 전체에게</option></select>'
           '<input type="text" placeholder="링크 (드라이브·노션 등 · 선택)"><input type="file" multiple>'
           f'{K.btn("자료 등록", "자료를 등록했습니다 · 선정자에게 알림")}</div><p class="muted">아직 올린 자료가 없습니다.</p></details>')
    return (f'{mat}<p class="tab-sum">신청 <b>{c["applied"]}</b> | 선정 <b>{len(revs)}</b> | 모집 <b>{c["n"]}</b></p>'
            f'<div class="obulk"><label><input type="checkbox" class="js-ckall"> 전체선택</label>{K.btn("선택 리뷰어에게 쪽지 보내기", "쪽지 창(시안)")}</div>'
            f'<table class="otable"><thead><tr><th class="ck"></th><th class="num">번호</th><th>사진</th><th>리뷰어</th><th>참여이력</th><th>리뷰</th>'
            f'<th class="add">지급 {K.add_tag()}</th><th>쪽지</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


# ════════════════════════ 상세: 상태변경 히스토리 · 보고서 ════════════════════════
def tab_log(c):
    b = c["b"]
    who = f'대행사 · {b["owner"][1] if b["owner"] else "대표"}'
    d = c["dts"] or {}
    ev = []
    if c["group"] == "draft":
        ev = [("11/8 16:10", "임시저장", who, "작성 중 저장")]
    else:
        ev += [(P.md(d["rec"] - 8) + " 15:20", "검토중", who, "심사 제출"), (P.md(d["rec"] - 7) + " 10:12", "승인완료", "운영자", ""),
               (P.md(d["rec"] - 7) + " 10:12", "모집중", "시스템(자동)", f'예치 {c["deposit"]:,}P')]
        if c["group"] != "rec":
            ev.append((P.md(d["rec"]) + " 23:59", "모집완료", "시스템(자동)", f'신청 {c["applied"]}명'))
        if c["group"] in ("exp", "rev", "pay", "end"):
            ev.append((P.md(d["sel"]) + " 14:30", "체험단선정완료", who, f'선정 {c["sel"]}명 발표'))
            ev.append((P.md(d["exp"]) + " 00:00", "체험중", "시스템(자동)", ""))
        if c["state"] == "중단":
            ev.append((P.md(d["exp"]) + " 11:20", "취소", "대행사 · 대표", "업체 요청 · 남은 예치금 통포인트 복귀"))
        elif c["group"] == "end":
            ev.append((P.md(d["rev"] + 3) + " 18:00", "완료", "시스템(자동)", ""))
    trs = "".join(f'<tr><td class="muted">{t}</td><td>{s}</td><td>{w}</td><td>{esc(x) or "-"}</td></tr>' for t, s, w, x in reversed(ev))
    return (f'<table class="otable"><thead><tr><th>일시</th><th>상태</th><th>처리</th><th>사유</th></tr></thead><tbody>{trs}</tbody></table>'
            '<p class="note add">대행사 추가: 처리에 "대행사 · 직원 이름"이 남습니다(광고주는 "광고주(본인)").</p>')


def pub_link(b):
    rp = next((x for x in R.REPORTS if x["id"] == f'rp-{b["id"]}-11'), None)
    return (f'<a class="btn ghost" href="{R.pub_href(rp)}" target="_blank" rel="noopener">업체 고객이 보는 화면 ↗</a>' if rp else "")


def tab_rep(c):
    b = c["b"]
    ok = [v for v in c["revs"] if v["st"] == "ok"]
    links = "".join(f'<li><b>{v["nick"]}</b> <a href="#" class="ext">{v["ch"]} 리뷰 ↗</a></li>' for v in ok) \
        or '<li class="muted">승인된 리뷰가 아직 없습니다</li>'
    return (f'<p class="tab-sum">{K.add_tag("대행사 전용")} 이 캠페인은 <b>{esc(b["name"])} 11월 보고서</b>에 들어갑니다.</p>'
            f'<h3 class="sec-t">보고서에 실리는 리뷰</h3><ul class="replinks">{links}</ul>'
            f'<div class="acts wide"><a class="btn" href="reports.html">보고서 링크 관리 →</a>{pub_link(b)}</div>'
            '<p class="note">보고서는 업체 고객용 — 리워드·포인트·수수료 금액은 나오지 않습니다.</p>')


def tab_badge(c, k):
    n = sum(n for kk, (n, _d) in c["iss"].items() if ISSUE_TAB[kk] == k) if k in ("app", "rev") else 0
    return f' <em>{n}</em>' if n else ""


DL = {"app": "신청자 내려받기", "rev": "결과 내려받기", "log": "상태변경 내려받기"}


def detail(c):
    b, cid = c["b"], c["id"]
    tabbar = "".join(f'<a href="#c-{cid}-{k}" class="ctab ctab-{k}{" add" if k == "rep" else ""}">{lab}{tab_badge(c, k)}</a>' for k, lab in TABS)
    body = {"ov": tab_ov, "app": tab_app, "rev": tab_rev, "log": tab_log, "rep": tab_rep}
    def dl(k):        # 탭별 내려받기(광고주 등급 기능 resultExcel)
        return f'<p class="dl">{K.btn(DL[k], DL[k] + " — 엑셀(시안)")}</p>' if k in DL else ""
    panes = "".join(f'<div class="ctp ctp-{k}" id="c-{cid}-{k}">{dl(k)}{body[k](c)}</div>' for k, _l in TABS)
    watch = (f'<span class="watch" title="같은 캠페인을 다른 직원이 열어 두었습니다"><i></i>{c["watch"]}님이 보고 있습니다</span>' if c["watch"] else "")
    owner = b["owner"][1] if b["owner"] else "미담당"
    gone = c["group"] in ("end",)
    acts = ("" if step_of(c) == 24 else
            K.btn("숨김", "캠페인을 숨겼습니다") + K.btn("캠페인 취소", "시안: 취소는 확인 창을 한 번 더 띄웁니다")) + K.btn("공유", "공유 링크를 복사했습니다")
    acts += ("" if gone else '<button type="button" class="btn sm" popovertarget="pop-rr">추가모집 요청</button>')
    acts += f'<a class="btn sm add" href="campaign_new.html#copy={cid}">복제</a>'
    return (f'<section class="cdetail cg-{c["ty"]}" id="c-{cid}" data-biz="{b["id"]}" aria-label="{esc(c["name"])}">'
            f'<header class="cd-h"><a class="back" href="#">← 캠페인 리스트</a>'
            f'<p class="pane-biz add">{esc(b["name"])} <span>담당 {owner} · 업체 담당자를 따름</span>{watch}</p>'
            f'<h1 class="cd-title">{step_badge(c)}<b>[{region(b)}] {esc(c["name"])}</b><small class="rnd">{c["round"]}회차 · #{code(c)}</small>'
            f'{stage_chip(c)}<span class="cd-acts">{acts}</span></h1>'
            f'{progress(c)}<nav class="ctabs" aria-label="캠페인 탭">{tabbar}</nav></header>'
            f'<div class="cd-b">{panes}</div></section>')


# ════════════════════════ 창(공용 1개씩) ════════════════════════
def pops():
    rr = K.pop("pop-rr", "추가모집 요청",
               '<p>같은 내용으로 리뷰어를 더 모집해 달라고 운영자에게 요청합니다.</p>'
               '<label class="fl">추가 모집인원 *<input type="number" placeholder="예) 5"><small>모자란 인원이 있으면 그 수가 미리 들어갑니다. 바꾸셔도 됩니다.</small></label>'
               '<label class="fl">희망 모집기간<span class="row2"><input type="date"> ~ <input type="date"></span></label>'
               '<label class="fl">희망 발표일<input type="date"></label>'
               '<label class="fl">요청 사유<textarea placeholder="예) 모집인원이 모자라 2명만 선정되었습니다. 같은 조건으로 5명 더 모집하고 싶습니다."></textarea></label>'
               '<p class="help">등록 건수 한도에 포함되지 않습니다 · 예치금은 통포인트에서 묶입니다 <span class="add-tag">대행사</span></p>',
               "요청 보내기", "추가모집을 요청했습니다 · 운영자 확인 후 등록")
    edit = K.pop("pop-edit", "캠페인수정",
                 '<p class="help">모집중·승인완료 캠페인을 고치면 다시 승인을 받습니다. 모집완료 뒤에는 고칠 수 없습니다.</p>'
                 '<div class="radios"><label><input type="radio" name="ed" checked> 캠페인설정</label><label><input type="radio" name="ed"> 기본정보</label>'
                 '<label><input type="radio" name="ed"> 방문 및 예약안내</label><label><input type="radio" name="ed"> 홍보내용</label></div>',
                 "수정 화면 열기", "시안: 등록 단계 화면을 그대로 씁니다")
    # 사유 · 점수 = 실서버 penaltyRule(리뷰어)
    reasons = "".join(f"<option>{n} (+{p}점 · {d})</option>" for n, p, d in
                      [("리뷰 미제출", 3, "30일 신청 제한"), ("부실 리뷰", 2, "14일"), ("방문 미실시", 3, "30일"),
                       ("노쇼 (No-show)", 3, "30일"), ("허위 정보 입력", 5, "영구 제한")])
    pen = K.pop("pop-pen", "패널티 부여", f'<label class="fl">사유<select>{reasons}</select></label>'
                '<label class="fl">내용<textarea placeholder="어떤 문제가 있었는지 적어주세요"></textarea></label>', "부여", "패널티를 부여했습니다")
    return rr + edit + pen


def campaigns_page():
    body = (f'<section class="board camp-page" aria-labelledby="t-camp">{list_view()}'
            f'{"".join(detail(c) for c in D.CAMPS)}{pops()}</section>')
    css = K.CSS + '<link rel="stylesheet" href="css/campaigns.css">' + list_style()
    return P.page("캠페인 리스트", "camp", body, None, css, "ops.js campaigns.js")


if __name__ == "__main__":
    (P.ROOT / "campaigns.html").write_text(campaigns_page(), encoding="utf-8")
    (P.ROOT / "campaign_new.html").write_text(camp_new.page(), encoding="utf-8")
    print(f"written campaigns.html · campaign_new.html · 캠페인 {len(D.CAMPS)}")
