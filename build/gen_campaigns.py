# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 리스트 · 캠페인 상세 — 광고주 사이트 구성 그대로
[2026-11-11 v0.9] 마크업을 광고주 것으로 바꿈(같은 요소 · 같은 class · 같은 순서 · 같은 이름) — css/adv/* 가 그대로 입혀진다
  리스트 = admin/inc/campaign/campaign.inc.html + script/campaign/campaignList.js(카드 마크업 · createList)
  위 탭 = admin/inc/campaign/campaignTabs.inc.html  → adv_camp_tabs()
  상세 = admin/inc/campaign/campaignView.inc.html(+ core/inc/campaign/campaignDetailHead · Body · Aside)
         · campaignApplicants · campaignReviewers · campaignHistory · campaignInquiry · exportBtn
  추가모집 요청 창 = admin/inc/campaign/rerecruitRequest.inc.html · 캠페인수정 메뉴 = admin/index.html .campaign-edit-menu
  대행사 추가분(.add 점선): 업체·담당자 줄 · 진행 단계 칩 · 걸린 이슈 · 복제 · 보고서 탭 · 담당자 거르기 · 급한 순 정렬 · 예치 · 지급
  광고주는 JS 로 여닫는 것을 여기서는 HTML/CSS 로:
    상태 탭 · 채널/유형 · 정렬 · 썸네일형/목록형 · 이미지 빼고 보기 = 라디오/체크박스/select + :has() (css/v9-camp.css + list_style())
    채널/유형 드롭다운 · 추가모집 요청 창 · 캠페인수정 메뉴 = popover
    상세(광고주는 모달) = 화면 안 패널, 열기·탭 = 주소 #c-<id>[-ov|-app|-rev|-log|-inq|-rep] + :target
  검색·담당자·선정 표시만 js/campaigns.js.
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
MS = '<span class="material-symbols-outlined"{a}>{i}</span>'


def ms(icon, hidden=True):
    return MS.format(i=icon, a=' aria-hidden="true"' if hidden else "")


# 상세 탭 — (주소 키, 광고주 data-tab, 이름) · 보고서 = 대행사 추가
TABS = [("ov", "overview", "캠페인 상세보기"), ("app", "applicants", "캠페인 신청자"), ("rev", "reviewers", "선정된 리뷰어"),
        ("log", "history", "상태변경 히스토리"), ("inq", "inquiry", "1:1 문의"), ("rep", "report", "보고서")]
# 대시보드 이슈 → 캠페인 상세 탭
ISSUE_TAB = {"apply": "app", "select": "app", "prep": "rev", "review": "rev", "nudge": "rev", "pay": "rev",
             "point": "ov", "late": "app", "owner": "ov"}

# 광고주 $CAMPAIGN_STEP · $CAMPAIGN_COLOR(core/inc/define.inc.php) — (코드, 이름, 상태뱃지 색)
STEPS = [(1, "미승인", "bg-yellow"), (2, "검토중", "bg-yellow"), (3, "승인완료", "bg-cyan"), (4, "모집중", "bg-green"),
         (5, "모집완료", "bg-gray"), (6, "체험단선정완료", "bg-cyan"), (7, "체험중", "bg-green"), (8, "완료", "bg-gray"),
         (21, "숨김", "bg-teal"), (22, "반려", "bg-red"), (23, "임시저장", "bg-gray"), (24, "취소", "bg-gray")]
STEP = {k: (n, cls) for k, n, cls in STEPS}
# 대행사 진행 단계(기획서 4장) → 광고주 상태 코드
TO_STEP = {"작성 중": 23, "승인 대기": 2, "모집 중": 4, "선정 중": 5, "체험 중": 7, "배송·체험 중": 7, "원고 작성 중": 7,
           "리뷰 중": 7, "정산 중": 7, "완료": 8, "중단": 24}
# 광고주 사이트 상단 탭(campaignTabs.inc.html $cmpTabList) — 우리 화면 주소로
ADV_TABS = [("camp", "캠페인 리스트", "campaigns.html"), ("rvw", "리뷰어 관리", "reviewers.html"),
            ("photo", "리뷰 사진 관리", "photos.html"), ("srch", "검색결과 리포트", "search_report.html"),
            ("insp", "리뷰 검수", "inspect.html"), ("video", "영상 제작 요청", "video.html")]


def adv_camp_tabs(active):
    """[2026-11-11 v0.9] 광고주 campaignTabs.inc.html 마크업 그대로(.cmp-top-tabs > .cmp-tab-btn) — 버튼 대신 링크
       리뷰 검수 옆 빨간 숫자 = 검수 대기(99 넘으면 99+) · <style> 도 광고주 조각에 있던 그대로 함께 넣는다"""
    n = G.COUNTS.get("review", 0)
    cnt = f'<span class="cmp-tab-cnt">{n if n < 100 else "99+"}</span>' if n > 0 else ""
    btns = "".join(f'<a class="cmp-tab-btn{" active" if k == active else ""}" href="{href}"'
                   f'{" aria-current=page" if k == active else ""}>{lab}{cnt if k == "insp" else ""}</a>'
                   for k, lab, href in ADV_TABS)
    style = ('<style>/* 광고주 campaignTabs.inc.html 의 <style> 그대로 + a 로 바꾼 만큼만 [2026-11-11 v0.9] */'
             '.cmp-tab-cnt{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;padding:0 5px;'
             'margin-left:6px;border-radius:9px;background:#e74c3c;color:#fff;font-size:11px;font-weight:700;line-height:1;vertical-align:middle}'
             '.cmp-tab-btn.active .cmp-tab-cnt{background:#fff;color:var(--color-main,#7346f3)}'
             'a.cmp-tab-btn{display:inline-block;text-decoration:none}</style>')
    return f'<div class="cmp-top-tabs">{btns}</div>{style}'


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


def dday(off):
    """광고주 dday() — D-3 / D-Day / D+2"""
    return f"D-{off}" if off > 0 else "D-Day" if off == 0 else f"D+{-off}"


def ymdw(off):
    """광고주 dateText(…, "y.m.d.w") — 26.11.12(목)"""
    d = P.d_of(off)
    return f'{d:%y.%m.%d}({P.WD[d.weekday()]})'


def ds(c, k, default=0):
    return (c["dts"] or {}).get(k, default)


def stage_chip(c):
    """대행사 진행 단계(광고주 상태보다 잘게) — 대시보드 이슈와 같은 말"""
    late = '<span class="stage late">마감 지남</span>' if c["late"] else ""
    return f'<span class="stage">{c["state"]}</span>{late}'


def owner_html(b):
    return (f'<span class="who"><i>{b["owner"][1][0]}</i>{b["owner"][1]}</span>' if b["owner"]
            else '<span class="who none">미담당</span>')


def offer(c):
    """제공내용(리뷰어에게 보이는 줄)"""
    # 실서버 등록 칸 예시("5만원 상당 자유 체험권") 꼴 + 포인트 지급 "1인당 ___ P"
    worth = {5000: "3만원", 10000: "5만원", 15000: "7만원", 30000: "10만원"}[c["reward"]]
    return {"v": f'{worth} 상당 자유 체험권 · 1인당 {c["reward"]:,}P',
            "s": f'{worth} 상당 제품 배송 · 1인당 {c["reward"]:,}P', "p": f'원고료 1인당 {c["reward"]:,}P · 보도자료 제공'}[c["ty"]]


def step_func(c, k):
    """광고주 campaign::stepFunc() — 상태뱃지 아래 칸(dday-badge) 글"""
    if not c["dts"]:
        return "모집시작 <span class='dday-text'>미정</span>" if k in (1, 2, 3, 23) else ""
    txt = {1: ("모집시작", dday(ds(c, "rec") - 7)), 2: ("모집시작", dday(ds(c, "rec") - 7)), 3: ("모집시작", dday(ds(c, "rec") - 7)),
           4: ("모집종료", dday(ds(c, "rec"))), 5: ("발표", ymdw(ds(c, "sel"))), 6: ("체험시작", dday(ds(c, "exp"))),
           7: ("체험종료", dday(ds(c, "rev"))), 8: ("체험종료", ymdw(ds(c, "rev"))), 23: ("모집시작", dday(ds(c, "rec") - 7))}
    if k == 21:
        return "<button type='button' class='status-action-btn js-flash' data-msg='숨김을 풀었습니다'>숨김해제</button>"
    if k == 24:
        return ymdw(ds(c, "exp"))              # 취소일(날짜+요일)
    lab, val = txt.get(k, ("", ""))
    return f"{lab} <span class='dday-text'>{val}</span>" if lab else ""


def remain_text(c):
    """광고주 $remainText — 모집 마감까지"""
    if not c["dts"]:
        return "모집 전"
    r = ds(c, "rec")
    return f"{r}일 남음" if r > 0 else "오늘 마감" if r == 0 else "모집 마감"


# ════════════════════════ 리스트(카드) — campaignList.js createList() ════════════════════════
def issue_chip(c):
    n_iss = sum(n for n, _d in c["iss"].values())
    if not n_iss:
        return ""
    hot = any(d <= 0 for _n, d in c["iss"].values())
    first = next(iter(c["iss"]))
    return (f'<a class="ichip {"is-hot" if hot else "is-later"}" href="#c-{c["id"]}-{ISSUE_TAB[first]}" '
            f'title="걸린 이슈 — 대시보드와 같은 숫자">이슈 {n_iss}</a>')


def card_btns(c):
    """카드 하단 버튼(.card-actions > .card-btn) — 캠페인보기 · 문의 · 추가모집 요청 · 공유 · 캠페인수정"""
    def cb(icon, label, attrs, tag="button"):
        inner = f'<span>{ms(icon, False)} {label}</span>'
        if tag == "a":
            return f'<a class="card-btn{attrs[0]}" href="{attrs[1]}">{inner}</a>'
        return f'<button type="button" class="card-btn{attrs[0]}"{attrs[1]}>{inner}</button>'
    ask = esc(f'1:1 문의 — [{code(c)}] {c["name"]} 문의로 시작합니다')
    out = cb("article", "캠페인보기", ("", f'#c-{c["id"]}'), "a")
    out += cb("support_agent", "문의", (" js-flash", f' data-msg="{ask}"'))
    if c["group"] in D.ACTIVE:              # 광고주 rrqState 1 = 요청 가능일 때만 버튼이 생긴다
        out += cb("person_add", "추가모집 요청", ("", ' popovertarget="pop-rr"'))
    out += cb("share", "공유", (" js-flash", ' data-msg="공유 링크를 복사했습니다"'))
    out += cb("edit", "캠페인수정", ("", ' popovertarget="pop-edit"'))
    # [2026-11-11] 대행사 [복제]는 카드에서 뺌(광고주 카드 버튼 5개 그대로 — 6개면 글자가 접힘). 상세 머리 버튼에만 둔다
    return out


def card(c, i_new, i_due):
    b = c["b"]
    sid = b["owner"][0] if b["owner"] else "un"
    k = step_of(c)
    n, color = STEP[k]
    new = " <span class='tag-new'>NEW</span>" if reg_off(c) >= -1 else ""
    rr = ('<span class="tag-sns bg-navy" title="운영자가 추가로 올려 드린 캠페인입니다. 등록 건수 한도에는 포함되지 않습니다.">추가모집</span>'
          if c["round"] > 1 and c["id"].endswith("x0") else "")
    d = c["dts"] or {}
    dates = (f'<div class="status-text-list" style="display: none;"><p>모집시작{ymdw(d.get("rec", 0) - 7)}</p>'
             f'<p>모집마감{ymdw(d.get("rec", 0))}</p><p class="red">리뷰마감{ymdw(d.get("rev", 0))}</p></div>' if d else "")
    return (f'<div class="cmp-card k{k} t-{c["ty"]} ch-{c["ch"]}" data-owner="{sid}" data-biz="{b["id"]}" '
            f'data-name="{esc(b["name"])} {esc(c["name"])} {code(c)}" style="--o:{i_new};--d:{i_due}">'
            f'<div class="card-thumb th-{c["ty"]}"><div class="card-overlay card-overlay-center">'
            f'<a class="card-badge-group" href="#c-{c["id"]}"><div class="status-badge {color}">{n}</div>'
            f'<div class="dday-badge">{step_func(c, k)}</div></a>{dates}</div></div>'
            f'<div class="card-content"><div class="card-tags"><span class="tag-sns bg-green">{G.TYPE_NAME[c["ty"]]}</span>'
            f'<span class="tag-text">{P.guess_ind(b["name"])}</span><span class="tag-code">#{code(c)}</span>{rr}</div>'
            f'<div class="card-title">[{region(b)}] {esc(c["name"])}</div>'
            f'<div class="card-desc">{esc(offer(c))}</div>'
            f'<div class="card-agency col-biz add">{esc(b["name"])} · {owner_html(b)} {stage_chip(c)} {issue_chip(c)} '
            f'<span class="rnd">{c["round"]}회차</span></div>'
            f'<div class="card-stats"><span>신청 <strong>{c["applied"]}</strong> / 모집 {c["n"]}{new}</span></div></div>'
            f'<div class="card-actions">{card_btns(c)}</div></div>')


def list_style():
    """상태 탭 · 채널 · 유형 거르기 규칙 — 상태 코드가 12개라 생성해서 넣는다"""
    st = "".join(f'.camp-page:has(#cs-{k}:checked) .cmp-card:not(.k{k}){{display:none}}' for k, _n, _c in STEPS)
    st += ",".join(f'.camp-page:has(#cs-{k}:checked) .status-tab[for=cs-{k}]' for k in ["all"] + [k for k, _n, _c in STEPS])
    st += "{background:var(--color-main);color:#fff;font-weight:600}"
    for ch in sorted({c["ch"] for c in D.CAMPS}):
        st += f'.camp-page:has(#cc-{ch}:not(:checked)) .cmp-card.ch-{ch}{{display:none}}'
    for t in G.TYPE_NAME:
        st += f'.camp-page:has(#ct-{t}:not(:checked)) .cmp-card.t-{t}{{display:none}}'
    return f'<style>/* [2026-11-11 v0.9] 생성된 거르기 규칙 — gen_campaigns.list_style() */{st}</style>'


def drop(name, label, items):
    """광고주 .custom-dropdown(채널전체 · 유형전체) — 패널은 popover(버튼 아래에 붙임: css/v9-camp.css anchor)"""
    cks = "".join(f'<label class="custom-checkbox"><input type="checkbox" id="{name}-{k}" value="{k}" checked>'
                  f'<span class="checkmark"></span><span class="chk-label">{v}</span></label>' for k, v in items)
    return (f'<div class="custom-dropdown"><button type="button" class="cmp-select dropdown-btn dd-{name}" popovertarget="dd-{name}">{label}</button>'
            f'<div class="dropdown-panel" id="dd-{name}" popover><div class="dropdown-list">{cks}</div>'
            f'<div class="dropdown-actions"><button type="button" class="btn-dropdown-close" popovertarget="dd-{name}" '
            f'popovertargetaction="hide">닫기</button></div></div></div>')


def list_view():
    cnt = {k: sum(1 for c in D.CAMPS if step_of(c) == k) for k, _n, _c in STEPS}
    radios = (f'<input type="radio" name="cs" id="cs-all" class="vr" checked>'
              + "".join(f'<input type="radio" name="cs" id="cs-{k}" class="vr">' for k, _n, _c in STEPS))
    stabs = (f'<label class="status-tab" for="cs-all">전체 <span class="count">{len(D.CAMPS)}</span></label>'
             + "".join(f'<label class="status-tab" for="cs-{k}">{n} <span class="count">{cnt[k]}</span></label>' for k, n, _c in STEPS))
    chans = sorted({c["ch"] for c in D.CAMPS})
    owners = '<option value="">담당자 전체</option><option value="un">미담당</option>' + "".join(
        f'<option value="{sid}">{name} ({t})</option>' for sid, name, _l, t in G.STAFF)
    by_new = sorted(D.CAMPS, key=lambda c: -reg_off(c))
    by_due = sorted(D.CAMPS, key=lambda c: (D.next_due(c) or ("", 999))[1])
    i_new = {c["id"]: i for i, c in enumerate(by_new)}
    i_due = {c["id"]: i for i, c in enumerate(by_due)}
    cards = "".join(card(c, i_new[c["id"]], i_due[c["id"]]) for c in by_new)
    return f'''{radios}<input type="radio" name="vw" id="vw-grid" class="vr" checked><input type="radio" name="vw" id="vw-list" class="vr">
	<div class="cmp-page-card clist">
		<div class="cmp-page-header">
			<h2 class="cmp-page-title">캠페인 리스트</h2>
			<div class="cmp-header-actions">
				<div class="cmp-search-box">
					<input type="text" placeholder="캠페인 찾기" class="cmp-search-input js-csearch" id="searchText" aria-label="캠페인 찾기">
					<button type="button" class="cmp-search-btn">검색</button>
				</div>
				<a class="btn-new-campaign" href="campaign_new.html">{ms("add", False)}<span>새 캠페인 등록</span></a>
			</div>
		</div>
		<div class="cmp-filters-wrap">
			<div class="cmp-filter-controls">
				<div class="filter-left cc-flex-wrap">
					<div class="cmp-status-tabs" id="statusTab">{stabs}</div>
					<div class="cc-form-group cc-gap-8">
						{drop("cc", "채널전체", [(c, c) for c in chans])}
						{drop("ct", "유형전체", list(G.TYPE_NAME.items()))}
					</div>
				</div>
				<div class="filter-right">
					<select class="cmp-select js-cown add" aria-label="담당자">{owners}</select>
					<select class="cmp-select select-sort" aria-label="정렬">
						<option value="r" selected>최신순</option><option value="p">과거순</option><option value="d">기한 급한 순 (대행사)</option>
					</select>
					<label class="cmp-noimg-chk" id="cmpNoImgWrap" title="한 줄씩 보기에서 썸네일을 감춰 한 화면에 더 많이 봅니다">
						<input type="checkbox" id="cmpNoImg">
						이미지 빼고 보기
					</label>
					<div class="cmp-view-toggles">
						<label class="view-toggle-btn" for="vw-grid" aria-label="썸네일형">{ms("grid_view", False)}</label>
						<label class="view-toggle-btn" for="vw-list" aria-label="목록형">{ms("view_list", False)}</label>
					</div>
				</div>
			</div>
		</div>
		<div class="cmp-list-container cmp-grid-view" id="listBaseLayer">{cards}</div>
		<div class="cmp-empty js-cempty" hidden>해당 조건의 캠페인이 없습니다.</div>
	</div>'''


# ════════════════════════ 상세: 머리(campaignView.inc.html · campaignDetailHead.inc.php) ════════════════════════
def status_bar(c):
    """광고주 .detail-status-bar — 12단계 전부 › 로 잇고 지금 단계만 노랗게"""
    now = step_of(c)
    d = c["dts"] or {}
    parts = []
    for i, (k, n, _cls) in enumerate(STEPS):
        if k == now:
            sub = {3: ("모집마감", dday(d.get("rec", 0))), 4: ("발표일", dday(d.get("sel", 0))),
                   5: ("체험시작", dday(d.get("exp", 0))), 6: ("체험종료", dday(d.get("rev", 0)))}.get(k) if d else None
            subs = f'<span class="status-active-sub">{sub[0]} <b>{sub[1]}</b></span>' if sub else ""
            if c["ty"] == "s" and k in (4, 5) and d:
                subs += f'<span class="status-active-sub">배송시작 <b>{ymdw(d["exp"])}</b></span>'
            parts.append(f'<div class="status-step-active"><span class="status-active-label">{n}</span>{subs}</div>')
        else:
            parts.append(f'<span class="status-step">{n}</span>')
        if i < len(STEPS) - 1:
            parts.append(f'<span class="material-symbols-outlined status-arrow" aria-hidden="true">chevron_right</span>')
    return f'<div class="detail-status-bar">{"".join(parts)}</div>'


def head_actions(c):
    """$cdHeadActions — 숨김 · 캠페인 취소 · 공유 (+ 대행사 추가모집 요청 · 복제)"""
    k = step_of(c)
    out = ""
    if k != 24:
        out += (f'<button type="button" class="detail-action-btn js-flash" data-msg="캠페인을 숨겼습니다">{ms("visibility_off")}<span>숨김</span></button>'
                f'<button type="button" class="detail-action-btn js-flash" data-msg="시안: 취소는 확인 창을 한 번 더 띄웁니다">{ms("cancel")}<span>캠페인 취소</span></button>')
    out += (f'<button type="button" class="cs-share-btn js-flash" data-msg="공유 링크를 복사했습니다" aria-label="캠페인 공유">'
            f'{ms("share")}<span class="cs-share-btn__text">공유</span></button>')
    if c["group"] != "end":
        out += f'<button type="button" class="detail-action-btn add" popovertarget="pop-rr">{ms("person_add")}<span>추가모집 요청</span></button>'
    out += f'<a class="detail-action-btn add" href="campaign_new.html#copy={c["id"]}">{ms("content_copy")}<span>복제</span></a>'
    return out


def detail_head(c):
    b = c["b"]
    d = c["dts"] or {}
    dd = dday(d["rec"]) if d else "미정"
    return (f'<div class="cd-title-section"><div class="cd-title-row"><div class="cd-title-left">'
            f'<div class="cd-deadline-wrap"><span class="cd-deadline-label">모집마감</span><span class="badge-dday">{dd}</span></div>'
            f'<h1 class="cd-title">[{region(b)}] {esc(c["name"])}</h1></div>'
            f'<div class="cd-title-actions">{head_actions(c)}</div></div>'
            f'<div class="cd-meta-row"><div class="campaign-card__meta"><span class="campaign-card__category">{c["ch"]}</span>'
            f'<span class="badge badge--visit">{G.TYPE_NAME[c["ty"]]}</span>'
            f'<span class="campaign-card__category">{P.guess_ind(b["name"])}</span><span class="campaign-card__code">{code(c)}</span></div>'
            f'<span class="cd-divider"></span>'
            f'<span class="cd-stats">신청 <strong>{c["applied"]:,}</strong> / <span class="cd-stats--gray">모집 <strong>{c["n"]}</strong></span></span></div></div>')


# ════════════════════════ 상세: 캠페인 상세보기(campaignDetailBody · Aside) ════════════════════════
def section(label, body, extra=""):
    return f'<div class="cd-section{extra}"><div class="cd-section__label">{label}</div><div class="cd-section__body">{body}</div></div>'


def chips(items):
    return '<div class="cd-keyword-chips">' + "".join(f'<span class="cd-keyword">{esc(v)}</span>' for v in items) + '</div>'


def detail_body(c):
    b, ty = c["b"], c["ty"]
    x = P.extra(b)
    r = random.Random("mis-" + c["id"])
    out = section("제공내용", f'<p class="cd-section__headline">총 <span class="color-orange">{c["n"]}</span>명 모집</p>'
                          f'<p class="cd-section__text">{esc(offer(c))}</p>')
    if ty == "v":
        # 안내문 = 실서버 등록 화면 기본 문구(campaignCreate.inc.html L115-139)
        out += section("방문 및 예약",
                       '<p class="cd-section__text">체험 시간: 주중 13:00 ~ 18:00<br />휴무일: 매주 월요일</p>'
                       '<div class="cd-alert-box"><div class="cd-alert-box__header">'
                       '<svg width="20" height="22" viewBox="0 0 20 22" fill="none" aria-hidden="true"><path d="M10 1L13 7.5L20 8.5L15 13L16.18 20L10 16.77L3.82 20L5 13L0 8.5L7 7.5L10 1Z" fill="white" /></svg>'
                       '<span>방문일정은 반드시 협의 후 진행합니다.</span></div>'
                       '<div class="cd-alert-box__body">★방문 2~3일전 반드시 예약 문의 후 방문 부탁 드립니다.<br>'
                       '예약 문의가 없을 시 체험이 불가능 할 수 있으니 유의 바랍니다.<br>★당일 체험 불가</div></div>'
                       f'<div class="cd-location-row"><p class="cd-section__text">방문 위치: {esc(x["reg"])}</p></div>')
    elif ty == "s":
        out += section("배송안내", '<p class="cd-section__text">배송 방식: 택배, 순차발송<br />'
                                f'배송 시작일: {ymdw(ds(c, "exp"))}</p>')
    kw = [f'{region(b)}{P.guess_ind(b["name"])}', b["name"].split()[-1]]
    if c["ch"] == "구매평":
        out += section("구매평 키워드", '<p class="cd-section__text color-pink">구매평은 아래 검색 키워드를 반드시 포함해야합니다.</p>'
                                    '<p class="cd-section__text cd-section__text--sub cd-strong">검색 키워드</p>' + chips(kw))
    elif c["ch"] in ("인스타", "릴스"):
        out += (f'<div class="cd-section"><div class="cd-section__label cd-section__label--icon">{c["ch"]} 해시태그</div>'
                f'<div class="cd-section__body"><p class="cd-section__text color-pink">{c["ch"]} 리뷰에는 아래 해시태그를 반드시 포함해야합니다.</p>'
                f'{chips(["#" + v for v in ["협찬"] + kw])}</div></div>')
    elif c["ch"] == "쇼츠":
        out += (f'<div class="cd-section"><div class="cd-section__label cd-section__label--icon">유튜브 키워드</div>'
                f'<div class="cd-section__body"><p class="cd-section__text color-pink">유튜브·쇼츠는 아래 해시태그와 검색 키워드를 반드시 포함해야합니다.</p>'
                f'<p class="cd-section__text cd-section__text--sub cd-strong">해시태그</p>{chips(["#" + v for v in kw])}</div></div>')
    else:
        out += (f'<div class="cd-section"><div class="cd-section__label cd-section__label--icon">{c["ch"]} 키워드</div>'
                f'<div class="cd-section__body"><p class="cd-section__text color-pink">네이버 {c["ch"]} 리뷰에는 아래 키워드를 반드시 포함해야합니다.</p>'
                f'{chips(kw)}</div></div>')
    # 미션 항목 = 실서버 리뷰 미션 칸($CHARLEN · $IMGCNT)
    mission = ["키워드 필수"] + (["지도 필수"] if ty == "v" else []) + \
              [f'글자 수 {r.choice([800, 1000, 1200, 1500])}자 이상', f'이미지 {r.choice([5, 10, 15])}개 이상']
    out += section("가이드라인/요청사항", chips(mission) +
                   '<div class="cd-section__text">● 위치 정보(지도 첨부), 운영 시간을 반드시 함께 작성해 주세요.</div>')
    out += section("NOTICE", '<div class="cd-notice"><p class="cd-notice__title">리뷰 미제출 안내</p>'
                             '<div class="cd-notice__text">리뷰 마감일까지 미등록 시 리뷰 미제출 패널티(3점 · 30일 신청 제한) · 유예 7일</div></div>',
                   " cd-section--notice")
    return f'<div class="cd-sections">{out}</div>'


def sched_row(label, value, active=False, left=""):
    a = " cd-schedule__row--active" if active else ""
    m = (lambda s: f' {s}--active' if active else "")
    lf = ""
    if left:
        lc = " cd-schedule__left--today" if left == "오늘 마감" else " cd-schedule__left--soon" if "후 시작" in left else ""
        lf = f'<span class="cd-schedule__left{lc}">{left}</span>'
    return (f'<div class="cd-schedule__row{a}"><span class="cd-schedule__bullet{m("cd-schedule__bullet")}"></span>'
            f'<span class="cd-schedule__label{m("cd-schedule__label")}">{label}</span>'
            f'<span class="cd-schedule__value{m("cd-schedule__value")}">{value}</span>{lf}</div>')


def detail_aside(c):
    b = c["b"]
    d = c["dts"]
    dd = dday(d["rec"]) if d else "미정"
    card_ = (f'<div class="cd-sidebar-card"><div class="cd-sidebar-card__badges"><span class="badge-dday">{dd}</span>'
             f'<span class="campaign-card__category">{c["ch"]}</span><span class="badge badge--visit">{G.TYPE_NAME[c["ty"]]}</span>'
             f'<span class="campaign-card__category">{P.guess_ind(b["name"])}</span><span class="campaign-card__category">{code(c)}</span></div>'
             f'<h2 class="cd-sidebar-card__title">[{region(b)}] {esc(c["name"])}</h2>'
             f'<p class="cd-sidebar-card__desc">{esc(offer(c))}</p>'
             f'<p class="cd-sidebar-card__reward">원고료 <strong>{c["reward"]:,}</strong> 포인트</p></div>')
    if d:
        now = "rec" if d["rec"] >= 0 else "sel" if d["sel"] >= 0 else "exp" if d["exp"] >= 0 else "rev"
        left = remain_text(c) if d["rec"] >= 0 else ""
        rows = sched_row("모집기간", f'{ymdw(d["rec"] - 7)} ~ {ymdw(d["rec"])}', now == "rec", left)
        rows += sched_row("선정자 발표", ymdw(d["sel"]), now == "sel")
        if c["ty"] == "s":
            rows += sched_row("배송시작", ymdw(d["exp"]), now == "exp")
            rows += sched_row("리뷰등록기간", f'{ymdw(d["exp"])} ~ {ymdw(d["rev"])}', now == "rev")
        else:
            rows += sched_row("체험기간", f'{ymdw(d["exp"])} ~ {ymdw(d["rev"])}', now in ("exp", "rev"))
            rows += sched_row("리뷰등록기간", f'~ {ymdw(d["rev"])}')
    else:
        rows = sched_row("모집기간", "미정")
    sched = f'<div class="cd-schedule">{rows}</div>'
    rt = remain_text(c)
    stats = (f'<div class="cd-apply-stats"><div class="cd-apply-stats__left"><span class="cd-apply-stats__applications">신청 '
             f'<strong>{c["applied"]:,}</strong> / <span class="cd-apply-stats__slots">모집 <strong>{c["n"]}</strong></span></span>'
             f'<span class="cd-apply-stats__divider"></span><span class="cd-apply-stats__remaining'
             f'{" cd-apply-stats__remaining--today" if rt == "오늘 마감" else ""}">{rt}</span></div></div>')
    dep = (f'<div class="cd-sidebar-card add"><p class="cd-sidebar-card__reward">예치 <strong>{c["deposit"]:,}</strong> 포인트</p>'
           f'<p class="cd-sidebar-card__desc">포인트에서 묶임 · 수수료 {int(D.FEE * 100)}% 포함 (대행사)</p></div>')
    return f'<aside class="cd-sidebar"><div class="cd-sidebar__inner">{card_}{sched}{stats}{dep}</div></aside>'


def issues_box(c):
    b = c["b"]
    chips_ = "".join(f'<a class="ichip {G.due_class(d)}" href="dashboard.html#open={b["id"]}-{k}">{G.ISSUE_NAME[k]} {n}<small>{G.due_label(d)}</small></a>'
                     for k, (n, d) in c["iss"].items()) or '<span class="cv-history-empty">걸린 이슈가 없습니다</span>'
    return (f'<div class="cv-history-box add"><div class="cv-history-box__label">걸린 이슈 {K.add_tag()} '
            f'<small>처리는 대시보드에서 · 같은 숫자</small></div><div class="ichips">{chips_}</div></div>')


def tab_ov(c):
    return (f'<div class="detail-main">{detail_body(c)}{issues_box(c)}</div>{detail_aside(c)}')


# ════════════════════════ 상세: 캠페인 신청자(campaignApplicants.inc.html) ════════════════════════
def export_bar(kind):
    """exportBtn.inc.php — 탭마다 그 탭이 보여주는 것을 받는다"""
    lab = {"apply": "신청자", "result": "결과", "history": "상태변경"}[kind]
    return (f'<div class="cv-export-bar"><a class="detail-action-btn js-flash" href="#" data-msg="{lab} 내려받기 — CSV(시안)">'
            f'{ms("download")}<span>{lab} 내려받기</span></a></div>')


def app_action(c, a, can):
    if a["st"] == "sel":
        if c["group"] in ("rec", "sel"):
            return (f'<div class="applicants-action-wait">{ms("schedule")}<span>선정대기</span></div>'
                    '<button type="button" class="btn-applicant-cancel js-unpick">해제</button>')
        return (f'<div class="applicants-action-done">{ms("check_circle")}<span>선정완료</span></div>'
                '<button type="button" class="btn-applicant-penalty" popovertarget="pop-pen">패널티</button>'
                '<button type="button" class="btn-applicant-cancel js-flash" data-msg="선정을 취소했습니다 · 추가 비용 없음">취소</button>')
    if a["st"] == "cancel":
        return (f'<div class="applicants-action-done">{ms("check_circle")}<span>선정완료</span></div>'
                '<button type="button" class="btn-applicant-penalty" popovertarget="pop-pen">패널티</button>'
                '<button type="button" class="btn-applicant-cancel btn-applicant-cancel--asked js-flash" data-msg="선정을 취소했습니다">취소</button>')
    if can:
        need = not a["bi"] and not a["hist"]
        lock = ' disabled title="블로그를 먼저 확인하세요(대행사 규칙)"' if need else ""
        return f'<button type="button" class="btn-applicant-select js-pick"{lock}>선정</button>'
    return "-"


def applicant_row(c, i, a, can):
    bi, h = a["bi"], a["hist"]
    r = random.Random(a["nick"])
    meta = f'{r.choice(["서울 마포구", "경기 성남시", "인천 연수구", "부산 해운대구"])} {r.choice([24, 31, 38, 45])}세 {r.choice(["여", "남"])}'
    grade = ""
    if bi:
        cls = {"최적화": "badge--success", "준최적화": "badge--info"}.get(bi["grade"], "badge--gray")
        grade = (f'<span class="applicants-divider">|</span><span class="applicants-bi">'
                 f'<span class="badge {cls}">{bi["grade"]}</span> <strong>{bi["score"]}</strong></span>')
    ours = (f'<div class="applicants-match-line add"><span class="applicants-match applicants-match--yes">{ms("check_circle")}'
            f'우리 대행사 {h["ours"]}회 · 평점 {h["rating"]}</span></div>' if h and h["ours"] else "")
    rcls = " applicants-row-waiting" if a["st"] == "sel" and can else " applicants-row-selected" if a["st"] in ("sel", "cancel") else ""
    part = (f'<span class="applicants-history-badge">{ms("flag")}{h["part"]}회</span>' if h else "-")
    row = (f'<tr class="applicants-row{rcls}{" need-check" if not bi and not h else ""}">'
           f'<td class="applicants-num" data-label="번호">{i}</td>'
           f'<td class="applicants-photo" data-label="사진"><div class="applicants-photo-inner">'
           f'<div class="applicants-avatar applicants-avatar--text" aria-hidden="true">{a["nick"][0]}</div></div></td>'
           f'<td class="applicants-reviewer" data-label="리뷰어"><div class="applicants-info-line"><b>{a["nick"]}</b> '
           f'<span class="applicants-divider">|</span> {meta}{grade}</div>{ours}'
           f'<div class="applicants-blog-line"><a href="#" class="applicants-blog-url js-blog">https://blog.naver.com/{a["nick"]}</a>'
           f'<span class="material-symbols-outlined applicants-icon-link" aria-hidden="true">open_in_new</span></div></td>'
           f'<td class="applicants-message-cell" data-label="신청메세지">{esc(a["memo"])}</td>'
           f'<td class="applicants-history" data-label="참여이력">{part}</td>'
           f'<td class="applicants-action js-ast" data-label="선정">{app_action(c, a, can)}</td></tr>')
    if a["st"] == "cancel":
        row += ('<tr class="applicants-row-cancelreq"><td colspan="6"><div class="rev-cancelreq">'
                '<span class="rev-cancelreq__badge">선정취소 요청</span><span class="rev-cancelreq__date">11.08</span>'
                '<span class="rev-cancelreq__why">일정이 맞지 않아요</span>'
                '<span class="rev-cancelreq__free">취소해도 추가 비용은 없습니다 · 비는 자리는 신청자 중에서 다시 선정하세요</span>'
                '<span class="rev-cancelreq__btns"><button type="button" class="rev-cancelreq__do js-flash" data-msg="선정을 취소했습니다">선정취소</button>'
                '<button type="button" class="rev-cancelreq__no js-flash" data-msg="요청을 거절했습니다">요청 거절</button>'
                '<button type="button" class="rev-cancelreq__no" popovertarget="pop-pen">패널티</button></span></div></td></tr>')
    return row


def tab_app(c):
    can = c["group"] in ("rec", "sel")
    wait = sum(1 for a in c["rows"] if a["st"] == "sel") if can else 0
    done = c["sel"] if not can else 0
    left = max(0, c["n"] - (wait if can else done))
    rows = "".join(applicant_row(c, i, a, can) for i, a in enumerate(c["rows"], 1)) or \
        '<tr><td colspan="6" style="text-align:center;padding:40px 0;color:#0e0e0e;">신청자가 없습니다.</td></tr>'
    confirm = (f'<div class="applicants-confirm-bar js-cbar"{"" if wait else " hidden"}><p class="applicants-confirm-text">선정대기 <b class="js-wait">{wait}</b>명이 있습니다. '
               '최종 확인(발표) 시 신청자에게 알림이 발송되고 사용자 화면에 노출됩니다.</p>'
               '<button type="button" class="btn-applicant-confirm js-flash" data-msg="선정을 발표했습니다 · 알림 발송">선정 확정/발표</button></div>'
               if can else "")
    more = (f'<p class="applicants-notice add"><span>신청 {c["applied"]}명 중 {D.SHOW_APPS}명만 그려 둠(시안) — 실제는 페이지 넘김</span></p>'
            if c["applied"] > D.SHOW_APPS else "")
    return (f'{export_bar("apply")}<div class="applicants-notice"><p>리뷰어의 정보를 <span class="applicants-notice-highlight">꼼꼼히</span> '
            '확인하신 후 캠페인 진행에 적합한 리뷰어를 선정해주세요.<br>선정되지 않은 리뷰어의 정보는 선정 완료 또는 '
            '<span class="applicants-notice-highlight">캠페인 완료</span> 후 삭제됩니다.</p></div>'
            f'<div class="applicants-summary"><span class="applicants-summary-item">모집 {c["n"]}</span>'
            '<span class="applicants-summary-divider" aria-hidden="true"></span>'
            f'<span class="applicants-summary-item">신청 {c["applied"]:,}</span><span class="applicants-summary-divider" aria-hidden="true"></span>'
            f'<span class="applicants-summary-item">선정대기 <span class="js-wait">{wait}</span></span><span class="applicants-summary-divider" aria-hidden="true"></span>'
            f'<span class="applicants-summary-item">선정확정 {done}</span><span class="applicants-summary-divider" aria-hidden="true"></span>'
            f'<span class="applicants-summary-item">남은 자리 {left}</span>'
            '<label class="applicants-canceled-toggle">'
            '<input type="checkbox"><span>예전에 취소된 줄까지 보기</span></label></div>'
            f'{confirm}<div class="applicants-table-wrap"><table class="applicants-table" role="grid"><thead><tr>'
            '<th scope="col">번호</th><th scope="col">사진</th><th scope="col">리뷰어</th><th scope="col">신청메세지</th>'
            f'<th scope="col">참여이력</th><th scope="col">선정</th></tr></thead><tbody>{rows}</tbody></table></div>{more}'
            + ('<div class="applicants-notice add"><p>대행사 규칙: 블로그지수·참여이력이 둘 다 없는 첫 참여 리뷰어는 블로그를 열어 본 뒤 선정할 수 있습니다.</p></div>'
               if can and any(not a["bi"] and not a["hist"] for a in c["rows"]) else ""))


# ════════════════════════ 상세: 선정된 리뷰어(campaignReviewers.inc.html) ════════════════════════
REV = {"pend": ("badge--warning", "검수대기"), "ok": ("badge--success", "승인"), "fix": ("badge--danger", "반려"),
       "unreg": ("badge--gray", "미제출")}           # review::reviewStateBadge()
PAY = {"wait": "지급대기", "done": "지급완료", "noacc": "확인 필요"}


def review_cell(c, v):
    cls, lab = REV[v["st"]]
    out = f'<span class="badge {cls}">{lab}</span>'
    if v["st"] != "unreg":
        out += ('<a href="#" class="applicants-blog-url rv-go">리뷰 보기'
                '<span class="material-symbols-outlined applicants-icon-link" aria-hidden="true">open_in_new</span></a>')
    if v["st"] == "pend":
        out += (f'<div class="rv-acts"><a class="btn btn-primary" '
                f'href="inspect.html?biz={c["bid"]}">검수</a></div>')
    elif v["st"] in ("ok", "fix"):
        ok = ('<button type="button" class="btn btn-primary js-flash" data-msg="승인했습니다">승인</button>' if v["st"] == "fix" else "")
        out += (f'<div class="rv-acts">{ok}<button type="button" class="btn js-flash" data-msg="재검수를 요청했습니다">재검수 요청</button></div>')
    return out


def tab_rev(c):
    revs = c["revs"] or [{"nick": a["nick"], "ch": c["ch"], "st": "unreg", "ago": 0}
                         for a in c["rows"] if a["st"] in ("sel", "cancel") and c["group"] not in ("draft", "rec", "sel")]
    pays = {p["nick"]: p for p in c["pays"]}
    rows = []
    for i, v in enumerate(revs, 1):
        p = pays.get(v["nick"])
        pay = (f'<a href="payout.html?biz={c["bid"]}" class="applicants-blog-url">{PAY[p["st"]]}</a>' if p else '<span style="color:#bbb;">-</span>')
        ship = (f'<div class="rv-delivery">{ms("local_shipping")}<span class="rv-delivery__label">배송정보</span>'
                '<span class="rv-delivery__text">서울 마포구 ··· (선정 후 3개월 보관)</span></div>' if c["ty"] == "s" else "")
        rows.append(f'<tr class="rv-row"><td class="rv-col-check" data-label="선택"><input type="checkbox" class="rv-check" aria-label="고르기"></td>'
                    f'<td class="rv-col-num" data-label="번호">{i}</td>'
                    f'<td class="rv-col-photo" data-label="사진"><div class="applicants-avatar applicants-avatar--text" aria-hidden="true">{v["nick"][0]}</div></td>'
                    f'<td class="rv-reviewer" data-label="리뷰어"><div class="applicants-info-line"><b>{v["nick"]}</b> '
                    f'<span class="applicants-divider">|</span> {v["ch"]}</div>'
                    f'<div class="applicants-blog-line"><a href="#" class="applicants-blog-url">https://blog.naver.com/{v["nick"]}</a>'
                    f'<span class="material-symbols-outlined applicants-icon-link" aria-hidden="true">open_in_new</span></div>{ship}</td>'
                    f'<td class="rv-history" data-label="참여이력"><span class="applicants-history-badge">{ms("flag")}'
                    f'{random.Random(v["nick"]).randint(1, 12)}회</span></td>'
                    f'<td class="rv-review" data-label="리뷰">{review_cell(c, v)}</td>'
                    f'<td class="rv-pay add" data-label="지급">{pay}</td>'
                    f'<td class="rv-col-msg" data-label="쪽지"><button type="button" class="reviewers-message-btn js-flash" data-msg="쪽지 창(시안)" '
                    f'aria-label="쪽지 보내기">{ms("mail", False)}</button></td></tr>')
    body = "".join(rows) or '<tr><td colspan="8" style="text-align:center;padding:40px 0;color:#999;">선정된 리뷰어가 없습니다.</td></tr>'
    mats = ('<div class="cm-box"><div class="cm-box__head"><h4 class="cm-box__title">리뷰어에게 전달할 자료</h4>'
            '<p class="cm-box__desc">보도자료·이미지·가이드라인을 올려 두면 선정된 리뷰어가 마이캠페인에서 바로 받아 봅니다. 등록하면 알림이 갑니다.</p></div>'
            '<p class="cm-empty">아직 올린 자료가 없습니다.</p>'
            '<div class="cm-form"><div class="cm-form__row"><input type="text" class="cm-input" maxlength="100" placeholder="제목 (필수 · 예: 보도자료 및 이미지)">'
            '<select class="cm-input cm-input--sel"><option value="0">선정자 전체에게</option></select></div>'
            '<textarea class="cm-input cm-textarea" rows="3" placeholder="설명·요청사항 (무엇을 어떻게 써 달라는 안내가 자료보다 중요할 때가 많습니다)"></textarea>'
            '<div class="cm-form__row"><input type="text" class="cm-input" maxlength="400" placeholder="링크 (드라이브·노션 등 · 선택)">'
            '<input type="file" class="cm-file" multiple></div>'
            '<div class="cm-form__foot"><button type="button" class="cm-save-btn js-flash" data-msg="자료를 등록했습니다 · 선정자에게 알림">자료 등록</button></div></div></div>')
    return (f'{export_bar("result")}{mats}<div class="reviewers-summary"><span class="reviewers-summary-item">신청 {c["applied"]:,}</span>'
            f'<span class="reviewers-summary-divider" aria-hidden="true"></span><span class="reviewers-summary-item">선정 {len(revs)}</span>'
            f'<span class="reviewers-summary-divider" aria-hidden="true"></span><span class="reviewers-summary-item reviewers-summary-muted">모집 {c["n"]}</span></div>'
            '<div class="rv-bulk-bar"><label class="rv-bulk-all"><input type="checkbox" class="rv-check-all"><span>전체선택</span></label>'
            '<span class="rv-bulk-count"><b class="rv-bulk-num">0</b>명 선택됨</span>'
            f'<button type="button" class="rv-bulk-send js-flash" data-msg="쪽지 창(시안)">{ms("mail", False)}선택 리뷰어에게 쪽지 보내기</button></div>'
            '<div class="reviewers-table-wrap"><table class="rv-table" role="grid"><thead><tr>'
            '<th scope="col" class="rv-col-check"><span class="sr-only">선택</span></th><th scope="col" class="rv-col-num">번호</th>'
            '<th scope="col" class="rv-col-photo">사진</th><th scope="col">리뷰어</th><th scope="col">참여이력</th><th scope="col">리뷰</th>'
            f'<th scope="col" class="add">지급 {K.add_tag()}</th><th scope="col" class="rv-col-msg">쪽지</th></tr></thead><tbody>{body}</tbody></table></div>')


# ════════════════════════ 상세: 상태변경 히스토리 · 1:1 문의 · 보고서 ════════════════════════
def tab_log(c):
    b = c["b"]
    who = f'대행사 · {b["owner"][1] if b["owner"] else "대표"}'
    d = c["dts"] or {}
    ev = []
    if c["group"] == "draft":
        ev = [(P.md(0) + " 16:10", "임시저장", who, "")]
    else:
        ev += [(P.md(d["rec"] - 8) + " 15:20", "검토중", who, "심사 제출"), (P.md(d["rec"] - 7) + " 10:12", "승인완료", "운영자", ""),
               (P.md(d["rec"] - 7) + " 10:12", "모집중", "시스템(자동)", f'예치 {c["deposit"]:,}P')]
        if c["group"] != "rec":
            ev.append((P.md(d["rec"]) + " 23:59", "모집완료", "시스템(자동)", f'신청 {c["applied"]}명'))
        if c["group"] in ("exp", "rev", "pay", "end"):
            ev.append((P.md(d["sel"]) + " 14:30", "체험단선정완료", who, f'선정 {c["sel"]}명 발표'))
            ev.append((P.md(d["exp"]) + " 00:00", "체험중", "시스템(자동)", ""))
        if c["state"] == "중단":
            ev.append((P.md(d["exp"]) + " 11:20", "취소", "대행사 · 대표", "업체 요청 · 남은 예치금 포인트 복귀"))
        elif c["group"] == "end":
            ev.append((P.md(d["rev"] + 3) + " 18:00", "완료", "시스템(자동)", ""))

    def when(t):
        md, hm = t.split()
        m, dd_ = md.split("/")
        return f"2026.{int(m):02d}.{int(dd_):02d} {hm}"
    trs = "".join(f'<tr><td class="cv-history__date">{when(t)}</td><td class="cv-history__step">{s}</td>'
                  f'<td class="cv-history__actor">{w}</td><td class="cv-history__memo{"" if x else " cv-history__memo--empty"}">{esc(x) or "-"}</td></tr>'
                  for t, s, w, x in reversed(ev))
    return (f'{export_bar("history")}<div class="cv-history-box"><div class="cv-history-box__label">상태변경 히스토리</div>'
            f'<div class="cv-history-scroll"><table class="cv-history"><thead><tr><th>일시</th><th>상태</th><th>처리</th><th>사유</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div></div>'
            '<div class="applicants-notice add"><p>대행사 추가: 처리에 "대행사 · 직원 이름"이 남습니다(광고주는 "광고주(본인)").</p></div>')


def tab_inq(c):
    return ('<div class="cv-history-box"><div class="cv-history-box__label" style="display:flex;align-items:center;justify-content:space-between;gap:10px;">'
            '<span>이 캠페인에 관한 1:1 문의 <span style="color:#8e8e93;font-weight:400;">(0)</span></span>'
            f'<button type="button" class="detail-action-btn js-flash" data-msg="1:1 문의 — [{code(c)}] {esc(c["name"])} 문의로 시작합니다">'
            f'{ms("support_agent")}<span>문의하기</span></button></div>'
            '<p class="cv-history-empty">이 캠페인에 관해 등록한 문의가 없습니다.</p></div>')


def pub_link(b):
    rp = next((x for x in R.REPORTS if x["id"] == f'rp-{b["id"]}-11'), None)
    return (f'<a class="detail-action-btn" href="{R.pub_href(rp)}" target="_blank" rel="noopener">{ms("open_in_new")}'
            '<span>업체 고객이 보는 화면</span></a>' if rp else "")


def tab_rep(c):
    b = c["b"]
    ok = [v for v in c["revs"] if v["st"] == "ok"]
    links = "".join(f'<tr><td class="cv-history__step">{v["nick"]}</td><td class="cv-history__actor">{v["ch"]}</td>'
                    f'<td><a href="#" class="applicants-blog-url">리뷰 보기</a></td></tr>' for v in ok) \
        or '<tr><td colspan="3" class="cv-history__memo--empty">승인된 리뷰가 아직 없습니다</td></tr>'
    return (f'<div class="cv-history-box add"><div class="cv-history-box__label" style="display:flex;align-items:center;justify-content:space-between;gap:10px;">'
            f'<span>{K.add_tag("대행사 전용")} 이 캠페인은 <b>{esc(b["name"])} 11월 보고서</b>에 들어갑니다</span>'
            f'<span style="display:flex;gap:6px;"><a class="detail-action-btn" href="reports.html">{ms("link")}<span>보고서 링크 관리</span></a>{pub_link(b)}</span></div>'
            f'<div class="cv-history-scroll"><table class="cv-history"><thead><tr><th>리뷰어</th><th>채널</th><th>리뷰</th></tr></thead>'
            f'<tbody>{links}</tbody></table></div>'
            '<p class="cv-history-empty">보고서는 업체 고객용 — 리워드·포인트·수수료 금액은 나오지 않습니다.</p></div>')


def tab_badge(c, k):
    n = sum(n for kk, (n, _d) in c["iss"].items() if ISSUE_TAB[kk] == k) if k in ("app", "rev") else 0
    return f'<span class="cmp-tab-cnt">{n}</span>' if n else ""


def detail(c):
    """광고주 campaignView.inc.html — 모달 대신 화면 안 패널. 패널은 모두 .is-active 를 달고(광고주 배치 규칙을 그대로 받으려고)
       보이고 숨기는 것은 css/v9-camp.css 의 :target 규칙이 정한다"""
    b, cid = c["b"], c["id"]
    tabs = "".join(f'<a href="#c-{cid}-{k}" class="detail-tab{" add" if k == "rep" else ""}" data-tab="{dt}" role="tab" '
                   f'aria-controls="c-{cid}-{k}">{lab}{tab_badge(c, k)}</a>' for k, dt, lab in TABS)
    body = {"ov": tab_ov, "app": tab_app, "rev": tab_rev, "log": tab_log, "inq": tab_inq, "rep": tab_rep}
    panels = "".join(f'<div class="detail-panel detail-panel-{dt} is-active{" add" if k == "rep" else ""}" id="c-{cid}-{k}" '
                     f'data-panel="{dt}" role="tabpanel">{body[k](c)}</div>' for k, dt, _l in TABS)
    watch = (f'<span class="watch" title="같은 캠페인을 다른 직원이 열어 두었습니다"><i></i>{c["watch"]}님이 보고 있습니다</span>' if c["watch"] else "")
    owner = b["owner"][1] if b["owner"] else "미담당"
    agency = (f'<p class="cd-agency col-biz add">{esc(b["name"])} · 담당 {owner} (업체 담당자를 따름) · {c["round"]}회차 · '
              f'{stage_chip(c)}{watch}</p>')
    return (f'<section class="cdetail cmp-page-card" id="c-{cid}" data-biz="{b["id"]}" aria-label="{esc(c["name"])}">'
            f'<a class="modal-close" href="#" aria-label="닫기">{ms("close", False)}</a>{agency}'
            f'{status_bar(c)}<div class="detail-body-wrap"><div class="detail-tabs" role="tablist">{tabs}</div>'
            f'<div class="detail-card"><div class="detail-side-mobile-bar" aria-label="상세 요약">'
            f'<span class="detail-side-mobile-stats">신청 {c["applied"]:,} / 모집 {c["n"]}</span><span class="detail-stat-divider"></span>'
            f'<span class="detail-side-mobile-days">{remain_text(c)}</span></div>'
            f'{detail_head(c)}<div class="detail-content">{panels}</div></div></div></section>')


# ════════════════════════ 창(공용 1개씩) ════════════════════════
def rrq_modal():
    """rerecruitRequest.inc.html 그대로 — 여닫기만 popover(광고주는 modal.open('rrqModal'))"""
    dt = lambda n: f'{P.d_of(n):%Y-%m-%d}'   # 광고주 _rrqDay(n) — 기준일 + n (모집 +1~+7 · 발표 +8 · 체험 +9~+16)
    close = 'popovertarget="pop-rr" popovertargetaction="hide"'
    return f'''<div class="modal-wrap rrq-modal" id="pop-rr" popover aria-label="추가모집 요청">
	<button type="button" class="modal-dim" {close} aria-label="닫기"></button>
	<div class="modal-content rrq-content">
		<div class="modal-header"><h3 class="modal-title">추가모집 요청</h3>
			<button type="button" class="btn-close" {close}>{ms("close", False)}</button></div>
		<div class="modal-body">
			<p style="margin:0 0 16px;font-size:13.5px;line-height:1.8;color:#0e0e0e;">같은 내용으로 <strong>리뷰어를 더 모집</strong>해 달라고 운영자에게 요청합니다.</p>
			<div class="pm-form-group" style="margin-bottom:14px;"><label>추가 모집인원 <span style="color:#e53e3e;">*</span></label>
				<input type="number" class="pm-input" min="1" step="1" placeholder="예) 5" style="max-width:180px;">
				<span style="font-size:12px;color:#0e0e0e;">모자란 인원이 있으면 그 수가 미리 들어갑니다. 바꾸셔도 됩니다.</span></div>
			<div class="pm-form-group" style="margin-bottom:14px;"><label>희망 모집기간</label>
				<div class="rrq-range"><input type="date" class="pm-input" value="{dt(1)}"><span style="color:#0e0e0e;">~</span><input type="date" class="pm-input" value="{dt(7)}"></div></div>
			<div class="pm-form-grid" style="margin-bottom:14px;"><div class="pm-form-group"><label>희망 발표일</label><input type="date" class="pm-input" value="{dt(8)}"></div></div>
			<div class="pm-form-group" style="margin-bottom:14px;"><label>희망 체험기간</label>
				<div class="rrq-range"><input type="date" class="pm-input" value="{dt(9)}"><span style="color:#0e0e0e;">~</span><input type="date" class="pm-input" value="{dt(16)}"></div></div>
			<div class="pm-form-group"><label>요청 사유</label>
				<textarea class="pm-input" rows="3" maxlength="500" placeholder="예) 모집인원이 모자라 2명만 선정되었습니다. 같은 조건으로 5명 더 모집하고 싶습니다." style="width:100%;resize:vertical;"></textarea></div>
			<div style="margin-top:16px;padding:12px 14px;background:#f7f7fa;border-radius:8px;font-size:12.5px;line-height:1.8;color:#0e0e0e;">
				· 일정은 기본값이 채워져 있습니다. <strong>원하시는 날짜로 고쳐 주세요.</strong> 지우면 그 칸은 운영자가 정합니다.<br>
				· 요청하시면 바로 등록되는 것이 아니라, <strong>운영자가 확인한 뒤</strong> 같은 내용으로 올려 드립니다.<br>
				· 이렇게 등록된 캠페인은 <strong style="color:#3a3a3c;">등록 건수 한도에 포함되지 않습니다.</strong><br>
				· 포인트를 지급하는 캠페인이면 추가 인원만큼 <strong>보증금이 묶입니다.</strong> 포인트 잔액을 미리 확인해 주세요.<br>
				· 같은 캠페인에 처리 대기 중인 요청이 있으면 다시 요청할 수 없습니다.
				<span class="add">· 대행사: 보증금은 포인트에서 묶입니다.</span>
			</div>
		</div>
		<div class="modal-footer">
			<button type="button" class="btn btn-primary js-flash" data-msg="추가모집을 요청했습니다 · 운영자 확인 후 등록">요청 보내기</button>
			<button type="button" class="btn btn-outline" {close}>취소</button>
		</div>
	</div>
</div>'''


def edit_menu():
    """admin/index.html .campaign-edit-menu — 광고주는 버튼 옆에 띄우는 메뉴(여기는 popover)"""
    items = ["캠페인설정", "기본정보", "방문 및 예약안내", "홍보내용"]
    lis = "".join(f'<li class="js-flash" data-msg="시안: 등록 단계 화면({x})을 그대로 씁니다 · 모집중·승인완료는 다시 승인을 받습니다">{x}</li>' for x in items)
    return f'<div class="edit-context-menu campaign-edit-menu" id="pop-edit" popover aria-label="캠페인수정"><ul>{lis}</ul></div>'


def pops():
    # 패널티 — 광고주는 prompt() 한 줄. 여기는 실서버 penaltyRule(리뷰어) 사유·점수를 고르는 창(대행사)
    reasons = "".join(f"<option>{n} (+{p}점 · {d})</option>" for n, p, d in
                      [("리뷰 미제출", 3, "30일 신청 제한"), ("부실 리뷰", 2, "14일"), ("방문 미실시", 3, "30일"),
                       ("노쇼 (No-show)", 3, "30일"), ("허위 정보 입력", 5, "영구 제한")])
    pen = K.pop("pop-pen", "패널티 부여", f'<label class="fl">사유<select>{reasons}</select></label>'
                '<label class="fl">내용<textarea placeholder="어떤 문제가 있었는지 적어주세요"></textarea></label>', "부여", "패널티를 부여했습니다")
    return rrq_modal() + edit_menu() + pen


def campaigns_page():
    body = (f'<div class="cmp-layout camp-page" aria-label="캠페인 리스트">{adv_camp_tabs("camp")}{list_view()}'
            f'{"".join(detail(c) for c in D.CAMPS)}{pops()}</div>')
    css = (K.CSS + '<link rel="stylesheet" href="css/campaigns.css"><link rel="stylesheet" href="css/v9-camp.css">' + list_style())
    return P.page("캠페인 리스트", "camp", body, None, css, "ops.js campaigns.js")


if __name__ == "__main__":
    (P.ROOT / "campaigns.html").write_text(campaigns_page(), encoding="utf-8")
    (P.ROOT / "campaign_new.html").write_text(camp_new.page(), encoding="utf-8")
    print(f"written campaigns.html · campaign_new.html · 캠페인 {len(D.CAMPS)}")
