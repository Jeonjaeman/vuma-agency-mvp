# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 운영 — 리뷰어 관리 · 리뷰 검수 · 포인트 지급 확인 (광고주 화면 그대로 + 대행사 추가분)
[2026-11-11 v0.9] 본문 마크업을 광고주 것 그대로 옮김(같은 요소 · 같은 class · 같은 순서 · 같은 글자)
  리뷰어 관리  = U:\\admin\\inc\\reviewer.inc.html (+ 참여 이력 = inc\\view\\reviewerHistory.inc.html)
  리뷰 검수    = U:\\admin\\inc\\reviewInspect.inc.html + reviewInspectModal.inc.html (창 내용 = script\\reviewInspect.js 가 채우던 것)
  지급 확인    = U:\\admin\\inc\\payoutCheck.inc.html
  광고주는 탭·창·거르기를 JS(서버 왕복)로 바꿈 → 여기서는 radio/checkbox + :has() · popover 속성(css/bridge/ops.css)
  업체 범위: 줄마다 data-biz(여러 업체 = data-bizs) → js/scope.js 가 다른 업체 줄을 숨김. 업체·담당자 칸 = .col-biz.add
  관심·차단 리뷰어 = 대행사 공용(Q14 안) → 업체 범위와 상관없이 보임
  실행: python -I build/gen_ops.py  →  reviewers.html · inspect.html · payout.html
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402
import gen_campaigns as C  # noqa: E402  (캠페인 코드 · 광고주 상태)
import gen_settle as S  # noqa: E402  (지급 묶음 — 대행사 추가분)

P = D.P
esc = K.esc
COMPANY = "애니라인 마케팅"           # 광고주 화면의 $_SESSION['COMPANY'] 자리 = 대행사 이름
CSS = K.CSS + '<link rel="stylesheet" href="css/bridge/ops.css">'


def ymd(off, short=True):
    """광고주 date("y.m.d") / date("Y.m.d")"""
    d = P.d_of(off)
    return f'{d.year % 100 if short else d.year:02d}.{d.month:02d}.{d.day:02d}'


def ms(icon, extra=""):
    return f'<span class="material-symbols-outlined"{extra}>{icon}</span>'


def select_rules(scope, sel_id, values, row_sel):
    """select 고른 값으로 줄 거르기 — option:checked 를 :has() 로 읽는다(값마다 규칙 1줄)"""
    return "".join(f'{scope}:has(#{sel_id} option[value="{v}"]:checked) {row_sel}:not(.v-{v}){{display:none}}' for v in values)


def modal(mid, title, body, foot, extra_cls=""):
    """광고주 .modal-wrap 그대로 + popover 속성(열기 = popovertarget, 닫기 = popovertargetaction=hide)"""
    return (f'<div class="modal-wrap{extra_cls}" id="{mid}" popover aria-hidden="true">'
            f'<div class="modal-dim"></div><div class="modal-content">'
            f'<div class="modal-header"><h3 class="modal-title">{title}</h3>'
            f'<button type="button" class="btn-close" popovertarget="{mid}" popovertargetaction="hide" aria-label="닫기">{ms("close")}</button></div>'
            f'<div class="modal-body">{body}</div><div class="modal-footer"{foot[0]}>{foot[1]}</div></div></div>')


def write(fname, title, key, body, js="ops.js", extra=""):
    (K.ROOT / fname).write_text(P.page(title, key, body, None, CSS + extra, js), encoding="utf-8")
    print(f"written {fname} ({(K.ROOT / fname).stat().st_size // 1024} KB)")


# ════════════════════════ 리뷰어 관리 ════════════════════════
def reviewers():
    """리뷰어(닉네임) → 신청·선정·리뷰 기록. 캠페인 더미의 같은 닉네임을 묶는다"""
    out = {}
    for c in D.CAMPS:
        for a in c["rows"]:
            r = out.setdefault(a["nick"], {"nick": a["nick"], "apps": [], "bi": a["bi"], "cancel": []})
            r["apps"].append((c, a))
            if a["st"] == "cancel":
                r["cancel"].append(c)
    for i, r in enumerate(sorted(out.values(), key=lambda x: x["nick"])):
        rr = random.Random("rv-" + r["nick"])
        r["apps"].sort(key=lambda x: x[1]["ago"])
        r.update({"no": i + 1, "reg": rr.choice(["서울 마포", "서울 강남", "경기 성남", "인천 연수", "부산 해운대"]),
                  "age": rr.choice(["20대", "30대", "40대"]), "sex": rr.choice(["여", "남"]), "like": i % 4 == 0, "block": i == 5,
                  "report": i == 9, "pen": rr.choice([0, 0, 0, 3]), "today": rr.randint(20, 900), "total": rr.randint(5000, 400000),
                  "nb": rr.randint(80, 3000), "topic": rr.choice(["맛집", "육아", "뷰티", "여행", "일상"]), "insta": rr.randint(300, 12000),
                  "sel": any(a["st"] == "sel" for _c, a in r["apps"])})
    return sorted(out.values(), key=lambda x: x["no"])


RVS = reviewers()
GRADE = {"최적화": "badge--success", "준최적화": "badge--info"}          # blogIndex::gradeBadge
HSTATE = {"sel": ("ok", "선정"), "wait": ("wait", "신청"), "new": ("wait", "신청"), "no": ("gray", "미선정"), "cancel": ("gray", "선정취소")}
RVLAB = {"ok": "검수완료", "pend": "검수대기", "fix": "반려", "unreg": "미제출"}
HIST = [("camp", "참여 캠페인"), ("note", "주고받은 쪽지"), ("sms", "보낸 문자"), ("mail", "보낸 메일"), ("inquiry", "1:1 문의")]
SEQ = [0]                                  # 카드마다 고유 이름(참여 이력 체크박스)


def hist_row(c, a, biz=True):
    """reviewerHistory.inc.html 참여 캠페인 한 줄 + 업체(대행사 추가 · biz=False 면 묶음 머리에 한 번만)"""
    rv = next((v for v in c["revs"] if v["nick"] == a["nick"]), None)
    cls, lab = ("done", "리뷰완료") if rv and rv["st"] == "ok" else HSTATE.get(a["st"], ("gray", a["st"]))
    review = f'<span class="rev-hist-review">리뷰 {RVLAB[rv["st"]]}</span>' if rv else ""
    attr = f' data-biz="{c["bid"]}"' if biz else ""          # 묶음이면 data-biz 는 묶음 상자에 한 번
    return (f'<div class="rev-hist-row"{attr}><span class="rev-hist-state rev-hist-state--{cls}">{lab}</span>'
            f'<a class="rev-hist-name" href="campaigns.html#c-{c["id"]}">{esc(c["name"])}</a>'
            f'<span class="rev-hist-code">{C.code(c)}</span>{f'<span class="rev-hist-code col-biz add">{esc(c["b"]["name"])}</span>' if biz else ""}'
            f'{review}<span class="rev-hist-date">{ymd(-a["ago"])}</span></div>')


def history(r, full):
    """참여 이력 칸 — 광고주는 단추를 누르면 ajax 로 불러옴 → 여기서는 체크박스 + :has() 로 펼침.
       full=False 면 광고주처럼 5건 + 쪽 이동(시안이라 고정)"""
    SEQ[0] += 1
    n = SEQ[0]
    apps = r["apps"] if full else r["apps"][:5]
    pager = ("" if full or len(r["apps"]) <= 5 else
             f'<div class="rev-hist-pager"><button type="button" class="rev-hist-pager__btn" disabled>이전</button>'
             f'<span class="rev-hist-pager__now">1 / {-(-len(r["apps"]) // 5)}</span>'
             f'<button type="button" class="rev-hist-pager__btn js-flash" data-msg="다음 쪽(시안)">다음</button></div>')
    cnt = {"camp": len(r["apps"]), "note": 2 if r["sel"] else 0, "sms": 0, "mail": 0, "inquiry": 0}
    tabs = "".join(f'<label class="rev-history__toggle{"" if cnt[k] else " is-empty"}"><input type="checkbox" name="rh{n}" value="{k}" hidden>'
                   f'{ms("expand_more")}{lab}<b class="rev-history__cnt">{cnt[k]}</b></label>' for k, lab in HIST)
    empty = {"note": "주고받은 쪽지가 없습니다.", "sms": "보낸 문자가 없습니다.", "mail": "보낸 메일이 없습니다.", "inquiry": "1:1 문의가 없습니다."}
    if full:
        # [2026-11-11 v0.9] 전체 목록은 쪽 나눔 없이 다 그림(한 업체 범위에서도 그 업체 줄이 빠지지 않게) → 업체별로 묶어 머리에 업체 이름 한 번
        groups = {}
        for c, a in apps:
            groups.setdefault(c["bid"], []).append((c, a))
        rows = "".join(f'<div data-biz="{bid}"><div class="rev-hist-biz col-biz add">{esc(g[0][0]["b"]["name"])} <b>{len(g)}</b></div>'
                       f'{"".join(hist_row(c, a, False) for c, a in g)}</div>' for bid, g in groups.items())
    else:
        rows = "".join(hist_row(c, a) for c, a in apps)
    secs = [f'<div class="rev-hist-sec rh-camp"><div class="rev-hist-sec__title">참여 캠페인 <span>{len(r["apps"])}</span></div>'
            f'{rows}{pager}</div>']
    note = ('<div class="rev-hist-note rev-hist-note--out"><div class="rev-hist-note__head"><span class="rev-hist-dir">보냄</span>'
            '<span class="rev-hist-note__title">방문 일정 안내</span><span class="rev-hist-note__read">읽음</span><span class="rev-hist-date">11.06 14:20</span></div>'
            '<div class="rev-hist-note__body">방문 가능하신 날짜를 알려 주세요.</div></div>'
            '<div class="rev-hist-note rev-hist-note--in"><div class="rev-hist-note__head"><span class="rev-hist-dir">받음</span>'
            '<span class="rev-hist-note__title">Re: 방문 일정 안내</span><span class="rev-hist-date">11.07 09:12</span></div>'
            '<div class="rev-hist-note__body">토요일 오후에 방문하겠습니다.</div></div>') if cnt["note"] else f'<div class="rev-history__empty">{empty["note"]}</div>'
    secs.append(f'<div class="rev-hist-sec rh-note"><div class="rev-hist-sec__title">주고받은 쪽지 <span>{cnt["note"]}</span></div>{note}</div>')
    for k, lab in HIST[2:]:
        secs.append(f'<div class="rev-hist-sec rh-{k}"><div class="rev-hist-sec__title">{lab} <span>0</span></div>'
                    f'<div class="rev-history__empty">{empty[k]}</div></div>')
    return (f'<div class="rev-history"><div class="rev-history__tabs">{tabs}</div>'
            f'<div class="rev-history__body">{"".join(secs)}</div></div>')


def rv_actions(r):
    """.rev-actions — 관심 · 차단 · 쪽지 · 문자 · 메일 · 신고 · 1:1 문의 (광고주 아이콘 그대로)"""
    no_why = "선정된 리뷰어에게만 연락할 수 있습니다. 개인정보 보유기간이 지난 분께도 보낼 수 없습니다."
    off = ' disabled style="opacity:.35;cursor:not-allowed;"'
    fav = (f'<button type="button" class="btn-rev-act active js-flash" title="관심 해제" data-msg="관심을 해제했습니다(시안)">{ms("kid_star")}</button>'
           if r["like"] else f'<button type="button" class="btn-rev-act js-flash" title="관심 등록" data-msg="관심 리뷰어로 등록했습니다(시안)">{ms("star_outline")}</button>')
    blk = (f'<button type="button" class="btn-rev-act danger js-flash" title="차단 해제" data-msg="차단을 해제했습니다(시안)">{ms("block")}</button>'
           if r["block"] else f'<button type="button" class="btn-rev-act" title="차단" popovertarget="revBlockModal">{ms("do_not_disturb_on")}</button>')
    if r["sel"]:
        msg = (f'<button type="button" class="btn-rev-msg js-flash" title="쪽지 보내기" data-msg="쪽지 창(시안)">{ms("mail")}</button>'
               f'<button type="button" class="btn-rev-act js-flash" title="문자 보내기 (포인트 차감)" data-msg="문자 창(시안 · 포인트 차감)">{ms("sms")}</button>'
               f'<button type="button" class="btn-rev-act js-flash" title="메일 보내기" data-msg="메일 창(시안)">{ms("outgoing_mail")}</button>')
    else:
        msg = (f'<button type="button" class="btn-rev-msg is-disabled" title="{no_why}"{off}>{ms("mail")}</button>'
               f'<button type="button" class="btn-rev-act is-disabled" title="{no_why}"{off}>{ms("sms")}</button>'
               f'<button type="button" class="btn-rev-act is-disabled" title="{no_why}"{off}>{ms("outgoing_mail")}</button>')
    rpt = (f'<button type="button" class="btn-rev-act danger" title="신고 접수됨 (운영자 확인중)" disabled>{ms("flag")}</button>' if r["report"]
           else f'<button type="button" class="btn-rev-act" title="운영자에게 신고" popovertarget="revReportModal">{ms("outlined_flag")}</button>')
    iq = f'<button type="button" class="btn-rev-act js-flash" title="이 리뷰어에 대해 운영자에게 문의" data-msg="1:1 문의 창(시안)">{ms("support_agent")}</button>'
    return f'<div class="rev-actions">{fav}{blk}{msg}{rpt}{iq}</div>'


def rv_card(r, idx, attr="", extra="", full=False):
    """reviewer.inc.html 의 .reviewer-item 한 장. attr = data-bizs/data-biz, extra = 선정취소 요청 · 신고 등 아래 덧붙는 칸"""
    bi = r["bi"]
    camps = " ".join(sorted({f'v-{c["id"]}' for c, _a in r["apps"]})) if full else ""   # 캠페인 거르기 = 전체 목록에서만
    bizs = sorted({c["b"]["name"] for c, _a in r["apps"]})
    badges = ((' <span class="rev-badge-block">차단됨</span>' if r["block"] else "")
              + (f' <span class="rev-badge-fav">{ms("kid_star")}관심</span>' if r["like"] else "")
              + (f' <span class="rev-badge-report">{ms("flag")}신고함</span>' if r["report"] else "")
              + (f' <span class="rev-badge-report" style="background:#ffece9;color:#c0392b;" title="적용중 패널티 점수">{ms("gavel")}패널티 {r["pen"]}점</span>'
                 if r["pen"] else ""))
    dv = ' <span class="divider">|</span> '
    bi_html = (f'{dv}<span class="rev-bi" title="블로그지수 {bi["score"]:.1f} / 10 · 최근 30일 {bi["post30"]}글"><span class="rev-bs-label">지수</span>'
               f'<span class="badge {GRADE.get(bi["grade"], "badge--gray")}">{bi["grade"]}</span><strong>{bi["score"]:.1f}</strong><span class="rev-bi-max">/10</span></span>'
               if bi else "")
    blog = (f'<div class="rev-blog-stats"><span>블로그</span>{bi_html}'
            f'{dv}<span><span class="rev-bs-label">오늘 방문</span> <strong>{r["today"]:,}</strong></span>'
            f'{dv}<span><span class="rev-bs-label">누적 방문</span> <strong>{r["total"]:,}</strong></span>'
            f'{dv}<span><span class="rev-bs-label">이웃</span> <strong>{r["nb"]:,}</strong></span>'
            f'{dv}<span><span class="rev-bs-label">주제</span> <strong>{r["topic"]}</strong></span>'
            f'<button type="button" class="rev-bs-refresh js-flash" title="블로그 지표 새로고침 (하루 1회)" data-msg="블로그 지표를 다시 모읍니다(시안)">{ms("refresh")}</button>'
            f'<a href="#" class="rev-link" aria-label="블로그 열기"><span class="material-symbols-outlined icon-link">open_in_new</span></a></div>')
    insta = (f'<div class="rev-blog-stats"><span>인스타 <strong>https://www.instagram.com/{esc(r["nick"])}/</strong></span>'
             f'{dv}<span>팔로워 <strong>{r["insta"]:,}</strong></span>'
             f'<a href="#" class="rev-link" aria-label="인스타 열기"><span class="material-symbols-outlined icon-link">open_in_new</span></a></div>')
    biz = (f'<div class="rev-demo col-biz add">업체 {len(bizs)}곳{dv}{esc(", ".join(bizs[:4]))}{" …" if len(bizs) > 4 else ""}</div>')
    return (f'<div class="reviewer-item{" rev-blocked" if r["block"] else ""}{" " + camps if camps else ""}"{attr}>'
            f'<label style="display:flex;align-items:center;padding:0 2px;cursor:pointer;"><input type="checkbox" class="js-rev-check" aria-label="고르기"></label>'
            f'<div class="rev-num">{idx}</div>'
            f'<div class="rev-profile"><div class="rev-avatar rev-avatar--text">{esc(r["nick"][0])}</div><span class="rev-name">{esc(r["nick"])}</span></div>'
            f'<div class="rev-details"><div class="rev-demo">{r["reg"]}{dv}{r["age"]}{dv}{r["sex"]}{dv}신청 <strong>{len(r["apps"])}</strong>회{badges}</div>'
            f'{biz}{blog}{insta}{history(r, full)}{extra}</div>{rv_actions(r)}</div>')


def bizs_attr(r):
    return f' data-bizs="{" ".join(sorted({c["bid"] for c, _a in r["apps"]}))}"'


def rv_list(cards, empty="해당 조건의 리뷰어가 없습니다."):
    return "".join(cards) or f'<div class="rev-empty" style="padding:60px 0;text-align:center;color:#8e8e93;">{empty}</div>'


def cancelreq(c):
    return (f'<div class="rev-cancelreq"><span class="rev-cancelreq__badge">선정취소 요청</span>'
            f'<a class="rev-cancelreq__camp" href="campaigns.html#c-{c["id"]}-app">{esc(c["name"])}</a>'
            f'<span class="rev-cancelreq__date">11.08</span><span class="rev-cancelreq__why">일정이 맞지 않아요</span>'
            f'<span class="rev-cancelreq__free">취소해도 추가 비용은 없습니다 · 비는 자리는 신청자 중에서 다시 선정하세요</span>'
            f'<span class="rev-cancelreq__btns"><button type="button" class="rev-cancelreq__do js-flash" data-msg="선정을 취소했습니다(시안)">선정취소</button>'
            f'<button type="button" class="rev-cancelreq__no js-flash" data-msg="요청을 거절했습니다(시안)">요청 거절</button></span></div>')


def canceled(c):
    return (f'<div class="rev-canceled"><span class="rev-canceled__badge">선정취소됨</span>'
            f'<span class="rev-canceled__camp">{esc(c["name"])}</span><span class="rev-canceled__at">2026.11.08 15:40 취소</span></div>')


def reports():
    return ('<div class="rev-reports"><div class="rev-report"><div class="rev-report__head">'
            '<span class="rev-report__state rev-report__state--wait">접수</span><span class="rev-report__reason">리뷰 미등록 · 연락 두절</span>'
            '<span class="rev-report__date">2026-11-05</span></div>'
            '<div class="rev-report__body">선정 후 방문하지 않았고 쪽지에도 답이 없습니다.</div>'
            '<div class="rev-report__answer rev-report__answer--wait">운영자가 확인중입니다. 처리되면 알림·쪽지로 알려드립니다.</div></div></div>')


def rv_modals():
    report = modal("revReportModal", "리뷰어 신고",
                   '<p class="rev-msg-to">신고할 리뷰어: <strong>(누른 리뷰어)</strong></p>'
                   '<select class="rev-msg-input" aria-label="신고 사유"><option>리뷰 미등록 (패널티 3점)</option><option>연락 두절 (패널티 2점)</option>'
                   '<option>부적절한 리뷰 내용</option><option>기타</option></select>'
                   '<p class="rev-report-camp">대상 캠페인: <strong>(최근 참여 캠페인)</strong></p>'
                   '<textarea class="rev-msg-textarea" placeholder="어떤 문제가 있었는지 구체적으로 적어주세요. 운영자가 확인 후 처리합니다."></textarea>'
                   '<p class="rev-report-notice">· 접수된 신고는 운영자가 확인 후 처리하며, 결과는 별도로 안내됩니다.<br>· 허위 신고 시 불이익을 받을 수 있습니다.</p>',
                   ("", '<button type="button" class="btn btn-cancel" popovertarget="revReportModal" popovertargetaction="hide">취소</button>'
                        '<button type="button" class="btn btn-primary js-flash" data-msg="신고를 접수했습니다(시안)">신고하기</button>'),
                   " rev-msg-modal").replace('<div class="modal-content">', '<div class="modal-content rev-msg-content">')
    block = modal("revBlockModal", "리뷰어 차단",
                  '<p class="rev-msg-to">차단할 리뷰어: <strong>(누른 리뷰어)</strong></p>'
                  '<textarea class="rev-msg-textarea" placeholder="차단 사유를 입력해 주세요. (선택)"></textarea>'
                  '<p class="rev-report-notice">· 차단하면 이 리뷰어는 내가 등록한 캠페인을 신청할 수 없습니다.<br>· 차단 사유는 운영자 확인용으로 기록됩니다.</p>'
                  '<p class="rev-report-notice add">· 대행사 공용(Q14 안) — 대행사의 <b>모든 업체</b> 캠페인에서 차단됩니다.</p>',
                  ("", '<button type="button" class="btn btn-cancel" popovertarget="revBlockModal" popovertargetaction="hide">취소</button>'
                       '<button type="button" class="btn btn-primary js-flash" data-msg="차단했습니다(시안)">차단하기</button>'),
                  " rev-msg-modal").replace('<div class="modal-content">', '<div class="modal-content rev-msg-content">')
    return report + block


def build_reviewers():
    like = [r for r in RVS if r["like"]]
    block = [r for r in RVS if r["block"]]
    rep = [r for r in RVS if r["report"]]
    creq = [(r, c) for r in RVS for c in r["cancel"]]
    camps = sorted({c["id"]: c for r in RVS for c, _a in r["apps"]}.values(), key=C.code)
    opts = '<option value="0">전체 캠페인</option>' + "".join(
        f'<option value="{c["id"]}">[{C.code(c)}] {esc(c["name"])}</option>' for c in camps)
    form = (f'<div class="rev-filter-form"><select class="cmp-select rev-camp-select" id="rcp" aria-label="캠페인">{opts}</select>'
            f'<div class="rev-search-box"><input type="text" class="rev-search-input" placeholder="리뷰어 이름 검색" aria-label="리뷰어 이름 검색">'
            f'<button type="button" class="rev-search-btn js-flash" data-msg="검색(시안)" aria-label="검색">{ms("search")}</button></div>'
            f'<label class="rev-canceled-toggle"><input type="checkbox" id="rvcx"><span>선정취소한 리뷰어 보기 <b>{len(creq)}</b></span></label>'
            f'<span class="rev-export-hint">캠페인을 고르면 결과를 내려받을 수 있습니다</span></div>')
    tabs = [("all", "전체", len(RVS), "count"), ("fav", "관심 리뷰어", len(like), "count highlight"),
            ("cancelreq", "선정취소 요청", len(creq), "count danger" if creq else "count"),
            ("blocked", "차단 리뷰어", len(block), "count highlight"), ("reported", "신고한 리뷰어", len(rep), "count highlight")]
    stabs = "".join(f'<label class="status-tab"><input type="radio" name="rtab" value="{k}" hidden{" checked" if k == "all" else ""}>'
                    f'{lab} <span class="{cls}">{n}</span></label>' for k, lab, n, cls in tabs)
    bulk = ('<div class="rev-bulk-bar" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px;padding:8px 12px;background:#f7f7f8;border-radius:8px;">'
            '<label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;"><input type="checkbox" id="revCheckAll"> 전체선택</label>'
            '<span style="font-size:14px;color:#666;"><b id="revCheckCount">0</b>명 선택</span>'
            '<div style="margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;">'
            '<button type="button" class="btn btn-primary js-flash" data-msg="쪽지 창(시안)">'
            '<span class="material-symbols-outlined" style="vertical-align:middle;font-size:18px;">mail</span> 쪽지</button>'
            '<button type="button" class="btn js-flash" style="border:1px solid #d1d1d6;background:#fff;" data-msg="문자 창(시안 · 포인트 차감)">'
            '<span class="material-symbols-outlined" style="vertical-align:middle;font-size:18px;">sms</span> 문자</button>'
            '<button type="button" class="btn js-flash" style="border:1px solid #d1d1d6;background:#fff;" data-msg="메일 창(시안)">'
            '<span class="material-symbols-outlined" style="vertical-align:middle;font-size:18px;">outgoing_mail</span> 메일</button></div></div>')
    shared = '<p class="rev-bi-notice add">관심·차단 리뷰어는 <b>대행사 공용</b>(Q14 안) — 업체 범위와 상관없이 모두 보입니다.</p>'
    panes = {
        "all": rv_list(rv_card(r, i + 1, bizs_attr(r), full=True) for i, r in enumerate(RVS)),
        "fav": shared + rv_list(rv_card(r, i + 1) for i, r in enumerate(like)),
        # 선정취소 요청 탭과 "선정취소한 리뷰어 보기" 는 같은 카드 한 벌(더미의 취소 = 같은 사람) — 어느 칸을 보일지는 css/bridge/ops.css
        "cancelreq": rv_list((rv_card(r, i + 1, f' data-biz="{c["bid"]}"', cancelreq(c) + canceled(c)) for i, (r, c) in enumerate(creq)),
                             "선정취소 요청이 없습니다."),
        "blocked": shared + rv_list(rv_card(r, i + 1) for i, r in enumerate(block)),
        "reported": rv_list(rv_card(r, i + 1, bizs_attr(r), reports()) for i, r in enumerate(rep)),
    }
    lists = "".join(f'<div class="cmp-reviewer-list rv-pane rv-pane--{k}">{v}</div>' for k, v in panes.items())
    style = "<style>" + select_rules(".rvm", "rcp", [c["id"] for c in camps], ".rv-pane--all .reviewer-item") + "</style>"
    body = (f'{style}<div class="cmp-layout rvm">{K.camp_tabs("rvw")}<div class="cmp-page-card">'
            f'<div class="cmp-page-header"><h2 class="cmp-page-title">{COMPANY}님의 리뷰어 리스트</h2></div>{form}'
            f'<div class="cmp-filters-wrap" style="border-bottom:none; margin-bottom:16px; padding-bottom:0;"><div class="cmp-status-tabs">{stabs}</div></div>'
            f'{bulk}{lists}</div></div>{rv_modals()}')
    write("reviewers.html", "리뷰어 관리", "rvw", body)


# ════════════════════════ 리뷰 검수 ════════════════════════
IST = {"pend": ("wait", "wait", "검수대기"), "ok": ("approved", "done", "승인"), "fix": ("rejected", "reject", "반려")}


def insp_rows():
    rows = [(c, v) for c in D.CAMPS for v in c["revs"] if v["st"] != "unreg"]
    rows.sort(key=lambda x: (x[1]["st"] != "pend", x[1]["ago"]))
    return rows


def mission(c, v):
    """review::missionItems — [(항목, 기준, 값, ok)] · 인스타 등 자동판정 불가 채널 = None"""
    if c["ch"] not in ("블로그",):
        return None
    r = random.Random("ms-" + v["nick"] + c["id"])
    img_ok = {"fix": False, "ok": True}.get(v["st"], r.random() >= .35)
    return [("키워드", "#연남헤어 #마포미용실", "2/2", True), ("글자수", "1,000자 이상", f'{r.randint(1050, 2400):,}자', True),
            ("이미지", "10개 이상", f'{r.randint(10, 18) if img_ok else r.randint(4, 9)}개', img_ok), ("지도", "지도 첨부", "", None)]


def mission_cells(items):
    if items is None:
        return ("<span class='ri-muted'>수동확인</span>",
                "<tr><td colspan='3' class='ri-muted'>자동판정 불가 채널입니다. 리뷰를 직접 확인 후 판단해 주세요.</td></tr>")
    compact, rows = "", ""
    for lab, need, val, ok in items:
        cls, t, mark = (("ri-mission-ok", "충족", "✓") if ok is True else ("ri-mission-no", "미충족", "✗") if ok is False
                        else ("ri-mission-man", "수동확인", ""))
        compact += f"<span class='{cls}'>{lab}{mark}</span>"
        rows += (f"<tr><td style='font-weight:600;'>{lab}</td><td class='ri-muted'>{need}{' · ' + val if val else ''}</td>"
                 f"<td class='{cls}'>{t}</td></tr>")
    return compact, rows


def insp_tr(i, c, v):
    k, cls, lab = IST[v["st"]]
    b = c["b"]
    compact, _rows = mission_cells(mission(c, v))
    ck = (f'<input type="checkbox" class="js-rvi-check" aria-label="고르기">' if v["st"] == "pend" else '<span class="ri-muted">-</span>')
    reason = '<div class="ri-reject-reason">사유 : 이미지 10개 미만(미션 미충족)</div>' if v["st"] == "fix" else ""
    if v["st"] == "pend":
        info = '<span class="ri-muted">-</span>'
        act = (f'<button type="button" class="btn btn-primary js-rvi-open" style="padding:6px 14px;font-size:13px;" '
               f'popovertarget="rviModal-{i}">검수</button>')
    else:
        who = f'대행사 · {K.owner_of(b)}' if b["owner"] else "운영자"
        info = f'<div class="ri-decide">{ymd(-v["ago"] + 1)} 14:20</div><div class="ri-decide__by">{who}</div>'
        again = ('<button type="button" class="btn btn-primary js-flash" style="padding:6px 12px;font-size:13px;margin-bottom:4px;" '
                 'data-msg="다시 승인했습니다 · 리뷰어에게 승인 알림(시안)">승인</button>' if v["st"] == "fix" else "")
        d = P.d_of(-v["ago"] + 8)
        act = (f'{again}<button type="button" class="btn js-rvi-recheck" style="padding:6px 12px;font-size:13px;" popovertarget="rviRecheckModal">재검수 요청</button>'
               f'<div class="ri-muted" style="margin-top:3px;font-size:12px;">{d.month:02d}.{d.day:02d}까지</div>')
    return (f'<tr class="irow v-{k} v-{c["id"]}" data-biz="{b["id"]}"><td class="ri-col-center">{ck}</td>'
            f'<td><a class="ri-camp__name" href="campaigns.html#c-{c["id"]}-rev">{esc(c["name"])}</a><span class="ri-camp__code">{C.code(c)}</span></td>'
            f'<td class="col-biz add">{K.biz_cell(b)}<br><small>{K.owner_of(b)}</small></td>'
            f'<td>{esc(v["nick"])}</td><td class="ri-muted">{c["ch"]}</td><td>{compact}</td>'
            f'<td class="ri-col-center"><span class="ri-badge ri-badge--{cls}">{lab}</span>{reason}</td>'
            f'<td class="ri-muted">{ymd(-v["ago"])}</td><td>{info}</td>'
            f'<td class="ri-col-center"><a href="#" class="ri-link">열기</a></td><td class="ri-col-center">{act}</td></tr>')


def insp_modal(i, c, v):
    """reviewInspectModal.inc.html #rviModal — reviewInspect.open() 이 채우던 내용을 줄마다 미리 채워 둠"""
    _c, rows = mission_cells(mission(c, v))
    mid = f"rviModal-{i}"
    return modal(mid, f'리뷰 검수 — {esc(c["name"])}',
                 f'<p class="ri-modal-head"><strong>{esc(v["nick"])}</strong> · <span class="ri-muted">{c["ch"]}</span></p>'
                 f'<p class="ri-modal-url"><a href="#" class="ri-link">https://blog.naver.com/{esc(v["nick"])}/2236{i:05d}</a></p>'
                 f'<table class="ri-mission"><thead><tr><th>항목</th><th>기준</th><th>충족</th></tr></thead><tbody>{rows}</tbody></table>'
                 '<label class="ri-reason-label">반려 사유 <span class="ri-muted" style="font-weight:400;">(반려 시 필수)</span></label>'
                 '<textarea class="ri-reason-input" placeholder="반려 시 리뷰어에게 전달할 사유를 입력하세요."></textarea>'
                 '<p class="ri-modal-notice">※ 조건 미충족 상태로 승인하면 운영자에게도 통지됩니다.</p>',
                 (' style="display:flex;gap:8px;justify-content:flex-end;"',
                  '<button type="button" class="btn js-flash" style="border:1px solid #d1d1d6;background:#fff;" data-msg="반려했습니다 · 리뷰어에게 알림(시안)">반려</button>'
                  '<button type="button" class="btn btn-primary js-flash" data-msg="승인했습니다 · 지급 대기로 넘어갑니다(시안)">승인</button>'))


def recheck_modal():
    return modal("rviRecheckModal", "재검수 요청",
                 '<p class="ri-modal-head"><strong>(누른 리뷰어)</strong> · 현재 <span class="ri-muted">승인</span></p>'
                 '<p class="ri-modal-notice" style="margin-bottom:12px;">검수 결과를 직접 바꿀 수는 없습니다. 운영자에게 재검수를 요청하면 검토 후 결과가 반영됩니다.</p>'
                 '<label class="ri-reason-label">요청 사유 <span class="ri-muted" style="font-weight:400;">(선택)</span></label>'
                 '<textarea class="ri-reason-input" placeholder="어떤 점이 잘못됐는지 적어주시면 운영자 검토에 도움이 됩니다."></textarea>',
                 (' style="display:flex;gap:8px;justify-content:flex-end;"',
                  '<button type="button" class="btn" style="border:1px solid #d1d1d6;background:#fff;" popovertarget="rviRecheckModal" popovertargetaction="hide">닫기</button>'
                  '<button type="button" class="btn btn-primary js-flash" data-msg="재검수를 요청했습니다(시안)">재검수 요청</button>'))


def build_inspect():
    rows = insp_rows()
    camps = sorted({c["id"]: c for c, _v in rows}.values(), key=C.code)
    st_sel = ('<select class="cmp-select" id="ist" aria-label="상태"><option value="wait" selected>검수 대기</option>'
              '<option value="approved">승인</option><option value="rejected">반려</option><option value="all">전체</option></select>')
    c_sel = ('<select class="cmp-select" id="icp" aria-label="캠페인"><option value="0">전체 캠페인</option>'
             + "".join(f'<option value="{c["id"]}">[{C.code(c)}] {esc(c["name"])}</option>' for c in camps) + '</select>')
    style = ("<style>" + select_rules(".ri", "ist", ["wait", "approved", "rejected"], ".irow")
             + select_rules(".ri", "icp", [c["id"] for c in camps], ".irow") + "</style>")
    th = ('<th class="ri-col-center"><input type="checkbox" class="js-ckall" id="rviHeadCheck" title="전체선택" aria-label="전체선택"></th>'
          f'<th>캠페인</th><th class="col-biz add">업체 · 담당 {K.add_tag()}</th><th>리뷰어</th><th>채널</th><th>미션 충족</th>'
          '<th class="ri-col-center">상태</th><th>제출일</th><th>검수정보</th><th class="ri-col-center">리뷰</th><th class="ri-col-center">검수</th>')
    pend = [(i, c, v) for i, (c, v) in enumerate(rows) if v["st"] == "pend"]
    table = (f'<div class="ri-table-wrap"><table class="ri-table"><thead><tr>{th}</tr></thead>'
             f'<tbody>{"".join(insp_tr(i, c, v) for i, (c, v) in enumerate(rows))}</tbody></table></div>')
    bulk = ('<div class="ri-bulk"><label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;">'
            '<input type="checkbox" id="rviCheckAll"> 전체선택</label><span class="ri-bulk__count"><b id="rviCheckCount">0</b>건 선택</span>'
            '<button type="button" class="btn btn-primary js-flash" data-msg="고른 리뷰를 승인했습니다(시안)">'
            '<span class="material-symbols-outlined" style="vertical-align:middle;font-size:18px;">done_all</span> 선택 일괄 승인</button></div>')
    body = (f'{style}<div class="cmp-layout ri">{K.camp_tabs("insp")}<div class="cmp-page-card">'
            f'<div class="cmp-page-header"><h2 class="cmp-page-title">{COMPANY}님의 리뷰 검수</h2></div>'
            f'<div class="ri-filter">{st_sel}{c_sel}<span class="ri-filter__hint">제출된 리뷰의 미션 충족 여부를 확인하고 승인/반려하세요.</span></div>'
            f'{bulk}{table}</div></div>'
            + "".join(insp_modal(i, c, v) for i, c, v in pend) + recheck_modal())
    write("inspect.html", "리뷰 검수", "insp", body)


# ════════════════════════ 포인트 지급 확인 ════════════════════════
def pay_rows():
    out = []
    for c in D.CAMPS:
        if c["group"] in ("draft", "rec") or not c["reward"]:
            continue
        pays = {p["nick"]: p for p in c["pays"]}
        for v in (c["revs"] or [{"nick": a["nick"], "st": "unreg"} for a in c["rows"] if a["st"] == "sel"]):
            out.append((c, v, pays.get(v["nick"])))
    return out


def pay_tr(c, v, p):
    b = c["b"]
    paid = bool(p and p["st"] == "done")
    odd = bool(p and p["st"] == "noacc")             # 진행 상태와 지급 기록이 다른 줄(시안 = 계좌 미등록)
    sel = ymd(c["dts"]["sel"], False) if c["dts"] else "-"
    if paid:
        # [2026-11-12] 지급 칸 = 한 줄(상태 · 금액 · 버튼) — 세 줄로 쌓이던 것을 .pc-pay 한 줄로(css/bridge/ops.css)
        pay = (f'<div class="pc-pay"><span class="st-done">지급완료</span><span class="pc-amt">'
               f'{p["amt"]:,}P · {ymd(c["dts"]["rev"] + 2, False)}</span></div>')
    else:
        pay = (f'<div class="pc-pay"><span class="st-wait">지급대기</span><span class="pc-amt">예정 {c["reward"]:,}P</span>'
               '<button type="button" class="btn btn--sm btn--outline js-flash" data-msg="1:1 문의 창(시안)">1:1 문의</button></div>')
    flag = ' <span style="color:#d46b08;font-size:12px;">● 확인 필요</span>' if odd else ""
    return (f'<tr class="prow v-{c["id"]}{"" if paid else " p-wait"}" data-biz="{b["id"]}"{" style=\"background:#fff7e6;\"" if odd else ""}>'
            f'<td data-label="캠페인"><a href="campaigns.html#c-{c["id"]}-rev">{esc(c["name"])}</a>{flag}</td>'
            f'<td data-label="리뷰어">{esc(v["nick"])}</td><td data-label="선정일">{sel}</td>'
            f'<td data-label="리뷰">{RVLAB[v["st"]]}</td><td data-label="지급">{pay}</td>'
            f'<td data-label="업체" class="col-biz add">{K.biz_cell(b)}<br><small>{K.owner_of(b)}</small></td></tr>')


def pay_check(rows):
    done = [(c, v, p) for c, v, p in rows if p and p["st"] == "done"]
    wait = [(c, v, p) for c, v, p in rows if not (p and p["st"] == "done")]
    odd = sum(1 for _c, _v, p in rows if p and p["st"] == "noacc")
    camps = sorted({c["id"]: c for c, _v, _p in rows}.values(), key=C.code)
    chips = ('<div class="pm-amount-presets" style="gap:10px;flex-wrap:wrap;margin-bottom:16px;">'
             f'<span class="pm-preset-btn" style="cursor:default;">선정 <b>{len(rows):,}</b>건</span>'
             f'<span class="pm-preset-btn" style="cursor:default;">지급완료 <b>{len(done):,}</b>건 · {sum(p["amt"] for _c, _v, p in done):,}P</span>'
             f'<span class="pm-preset-btn" style="cursor:default;{"color:#c62828;" if wait else ""}">지급대기 <b>{len(wait):,}</b>건 · '
             f'{sum(c["reward"] for c, _v, _p in wait):,}P</span></div>')
    alert = ('<div style="margin-bottom:16px;padding:12px 14px;background:#fff7e6;border:1px solid #ffd591;border-radius:8px;font-size:13px;line-height:1.8;color:#8a5a00;">'
             f'<b>확인이 필요한 건이 {odd}건 있습니다.</b><br>진행 상태와 실제 지급 기록이 서로 다릅니다. 아래 표에서 <b>주황색 표시</b>가 붙은 줄입니다 —'
             ' 1:1 문의로 알려 주시면 확인해 드리겠습니다.</div>') if odd else ""
    sel = ('<select class="p-input" id="pcp" style="width:260px;" aria-label="캠페인"><option value="0">캠페인 전체</option>'
           + "".join(f'<option value="{c["id"]}">{esc(c["name"])} (#{C.code(c)})</option>' for c in camps) + '</select>')
    filt = ('<div class="pm-amount-presets" style="gap:8px;flex-wrap:wrap;margin-bottom:12px;">'
            f'<div style="display:inline-flex;gap:8px;align-items:center;">{sel}</div>'
            '<input type="checkbox" id="pwait" hidden><label for="pwait" class="pm-preset-btn pc-wait">'
            '<span class="pc-off">지급대기만 보기</span><span class="pc-on">전체 보기</span></label></div>')
    th = '<th>캠페인</th><th>리뷰어</th><th>선정일</th><th>리뷰</th><th>지급</th>' f'<th class="col-biz add">업체 · 담당 {K.add_tag()}</th>'
    body = "".join(pay_tr(c, v, p) for c, v, p in rows) or \
        '<tr><td colspan="6" style="text-align:center;color:#0e0e0e;padding:24px 0;">선정된 리뷰어가 아직 없습니다.</td></tr>'
    foot = ('<div style="margin:16px 0 0;padding:12px 14px;background:#f7f8fb;border-radius:8px;font-size:13px;line-height:1.8;color:#555;">'
            '· 포인트는 <strong>리뷰 검수가 끝난 뒤</strong> 캠페인 등록 때 예치하신 보증금에서 나갑니다. 광고주께서 따로 보내실 것은 없고, <strong>추가 비용도 없습니다.</strong><br>'
            '· <strong>지급대기</strong>는 아직 지급 처리 전이라는 뜻입니다. 검수가 끝났는데도 며칠째 대기라면 1:1 문의로 알려 주세요.<br>'
            '· 선정이 취소되거나 리뷰를 쓰지 않은 분에게는 지급되지 않으며, 그만큼은 캠페인이 끝날 때 <strong>보증금으로 돌려받으십니다.</strong><br>'
            '· 리뷰어의 보유 포인트나 다른 캠페인 내역은 <strong>보여 드리지 않습니다</strong> — 이 화면은 내 캠페인의 지급분만 확인하는 곳입니다.</div>')
    return ('<div class="mp-card"><section class="mp-section"><div class="mp-section-header">'
            '<span class="material-symbols-outlined icon-mid">paid</span><h3 class="mp-section-title">리뷰어 포인트 지급 확인</h3></div>'
            '<p class="pm-amount-notice" style="margin-bottom:16px;">내 캠페인에 <b>선정된 리뷰어</b>에게 포인트가 실제로 지급되었는지 보여 드립니다. '
            '지급은 리뷰 검수가 끝난 뒤 <b>뷰마가 보증금에서 직접</b> 보냅니다 — 광고주께서 따로 보내실 것은 없습니다.<br>'
            '<span style="color:#888;">※ 포인트를 지급하지 않는 캠페인(현물만 제공)은 이 목록에 나오지 않습니다.</span></p>'
            f'{chips}{alert}{filt}<div class="pm-history-list"><table class="pm-table"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
            f'</section>{foot}</div>')


def build_payout():
    rows = pay_rows()
    style = "<style>" + select_rules(".pc", "pcp", sorted({c["id"] for c, _v, _p in rows}), ".prow") + "</style>"
    # [2026-11-12] 광고주처럼 위 탭 없이 지급 확인 카드(620px) 하나 — 대행사 "지급 묶음"은 그 아래 따로 된 점선 칸
    batch = ('<div class="cmp-page-card pc-batch add">'
             f'<h3 class="mp-section-title" style="margin-bottom:8px;">지급 묶음 {K.add_tag()}</h3>'
             '<p class="pm-amount-notice" style="margin-bottom:16px;">대행사 추가: 여러 업체 지급을 묶어 한 번에 확정합니다(v0.7 정산 › 리뷰어 지급). '
             '업체 범위와 상관없이 대행사 전체 묶음입니다.</p>'
             '<input type="radio" name="role" id="role-admin" class="vr" checked><input type="radio" name="role" id="role-view" class="vr">'
             f'<div class="sp-p">{S.tab_pay()}</div></div>')
    body = f'{style}<div class="page-container mp-container pc">{pay_check(rows)}{batch}</div>'
    write("payout.html", "포인트 지급 확인", "payc", body, "ops.js settle.js", '<link rel="stylesheet" href="css/ag/settle.css">')


if __name__ == "__main__":
    build_reviewers()
    build_inspect()
    build_payout()
