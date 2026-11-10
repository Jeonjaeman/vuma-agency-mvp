# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.6] 캠페인 화면 생성기 (기획서 v0.6 6-4)
  목록(거르기·검색) + 캠페인 페이지(탭 6개: 개요 · 신청자 · 리뷰 · 지급 · 이력 · 보고서).
  캠페인 페이지 열기·탭 바꾸기는 주소 #c-<id>[-탭] + CSS :target 만으로(JS 없음) → 대시보드·일정에서 바로 그 탭으로 연결된다.
  목록 거르기(상태·유형)도 라디오/체크박스 + CSS. 검색·담당자·업체 고르기, 선정/검수 버튼 표시만 js/campaigns.js.
  실행: python -I build/gen_campaigns.py  →  mvp/campaigns.html · mvp/campaign_new.html
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import camp_new  # noqa: E402

P, G = D.P, D.G
esc = P.esc
TABS = [("ov", "개요"), ("app", "신청자"), ("rev", "리뷰(검수)"), ("pay", "지급"), ("log", "이력"), ("rep", "보고서")]
# 대시보드 이슈 → 캠페인 페이지 탭(6-4: "검수 카드 → 리뷰 탭")
ISSUE_TAB = {"apply": "app", "select": "app", "prep": "app", "review": "rev", "nudge": "rev", "pay": "pay",
             "point": "ov", "late": "ov", "owner": "ov"}
STATUS_F = [("act", "진행 중", lambda c: c["group"] in D.ACTIVE), ("rec", "모집 중", None), ("sel", "선정 중", None),
            ("exp", "체험 중", None), ("rev", "리뷰 중", None), ("pay", "정산 중", None),
            ("draft", "작성 중", None), ("end", "완료·중단", None), ("all", "전체", lambda c: True)]


def state_badge(c):
    late = '<span class="st st-red">마감 지남</span>' if c["late"] else ""
    return f'<span class="st {D.STATE_CLS[c["state"]]}">{c["state"]}</span>{late}'


def owner_html(b):
    return (f'<span class="who"><i>{b["owner"][1][0]}</i>{b["owner"][1]}</span>' if b["owner"]
            else '<span class="who none">미담당</span>')


def due_html(c):
    nd = D.next_due(c)
    if not nd:
        return '<span class="muted">—</span>'
    k, off = nd
    lab = P.EXP_LABEL[c["ty"]] if k == "exp" else dict(P.KIND)[k]
    return (f'<span class="nd k-{k}"><i></i>{lab}</span> <span class="muted">{P.md(off)}</span> '
            f'<span class="due {G.due_class(off)}">{G.due_label(off)}</span>')


# ════════════════════════ 목록 ════════════════════════
def list_row(c):
    b = c["b"]
    n_iss = sum(n for n, _d in c["iss"].values())
    hot = any(d <= 0 for _n, d in c["iss"].values())
    iss = (f'<a class="ichip {"is-hot" if hot else "is-later"}" href="#c-{c["id"]}-{ISSUE_TAB[next(iter(c["iss"]))]}">{n_iss}</a>'
           if n_iss else '<span class="muted">—</span>')
    rec = (f'<b>{c["sel"]}</b>/{c["n"]}명 <span class="muted">· 신청 {c["applied"]}</span>' if c["group"] != "draft"
           else f'<span class="muted">0/{c["n"]}명</span>')
    sid = b["owner"][0] if b["owner"] else "un"
    return (f'<tr class="crow g-{c["group"]} t-{c["ty"]}" data-owner="{sid}" data-biz="{b["id"]}" '
            f'data-name="{esc(b["name"])} {esc(c["name"])}">'
            f'<td>{esc(b["name"])}</td>'
            f'<th scope="row"><a class="cnm" href="#c-{c["id"]}">{esc(c["name"])}</a> <small class="rnd">{c["round"]}회차</small></th>'
            f'<td>{P.ty_badges(c["name"])}</td><td>{state_badge(c)}</td><td class="num">{rec}</td>'
            f'<td>{due_html(c)}</td><td>{owner_html(b)}</td><td>{iss}</td></tr>')


def list_view():
    cnt = {k: sum(1 for c in D.CAMPS if (fn(c) if fn else c["group"] == k)) for k, _l, fn in STATUS_F}
    radios = "".join(f'<input type="radio" name="cf" id="cf-{k}" class="vr"{" checked" if k == "act" else ""}>' for k, _l, _f in STATUS_F)
    types = "".join(f'<input type="checkbox" id="ct-{t}" class="vr" checked>' for t in G.TYPE_NAME)
    chips = "".join(f'<label for="cf-{k}" class="pill">{lab} <b>{cnt[k]}</b></label>' for k, lab, _f in STATUS_F)
    tchips = "".join(f'<label for="ct-{t}" class="tchip"><span class="ty ty-{t}">{n}</span></label>' for t, n in G.TYPE_NAME.items())
    owners = '<option value="">담당자 전체</option><option value="un">미담당</option>' + "".join(
        f'<option value="{sid}">{name} ({t})</option>' for sid, name, _l, t in G.STAFF)
    bizs = '<option value="">업체 전체</option>' + "".join(f'<option value="{b["id"]}">{esc(b["name"])}</option>' for b in P.BIZS)
    rows = "".join(list_row(c) for c in sorted(D.CAMPS, key=lambda c: (D.next_due(c) or ("", 999))[1]))
    return f'''<div class="clist">
	<div class="board-h"><div><h1 id="t-camp">캠페인</h1>
		<p class="sub">대시보드에서 못 하는 일 — 조건 수정 · 신청자 전체 관리 · 모집 연장/조기 마감 · 이력 · 검색. 담당자는 업체를 따릅니다(일괄 변경은 업체 화면).</p></div>
		<a class="btn primary" href="campaign_new.html">+ 캠페인 등록</a></div>
	{radios}{types}
	<div class="s-tools">
		<label class="search b-search"><span class="sr">캠페인 검색</span><input type="search" class="js-csearch" placeholder="캠페인명·업체명"></label>
		<select class="input js-cbiz" aria-label="업체">{bizs}</select>
		<select class="input js-cown" aria-label="담당자">{owners}</select>
		<div class="kchips" role="group" aria-label="유형">{tchips}</div>
	</div>
	<div class="s-tools cfs" role="group" aria-label="상태">{chips}</div>
	<div class="grid-wrap"><table class="btable ctable">
		<thead><tr><th>업체</th><th>캠페인명 (회차)</th><th>유형 · 채널</th><th>상태</th><th class="num">선정/모집 · 신청</th>
		<th>다음 기한</th><th>담당자</th><th>이슈</th></tr></thead>
		<tbody>{rows}</tbody></table>
		<p class="empty-row js-cempty" hidden>조건에 맞는 캠페인이 없습니다</p></div>
</div>'''


# ════════════════════════ 캠페인 페이지 탭 ════════════════════════
def tab_ov(c):
    b, ty = c["b"], c["ty"]
    x = P.extra(b)
    place = {"v": ("노출 지역", f'{x["reg"]} · 업체 주소로 자동'), "s": ("배송", "택배 · 선정자 배송정보는 신청 후 3개월까지(기존 규칙)"),
             "p": ("전달 자료", "보도자료 · 이미지 · 가이드라인(기존 캠페인 자료)")}[ty]
    kv = (f'<dt>유형 · 채널</dt><dd>{P.ty_badges(c["name"])}</dd><dt>회차</dt><dd>{c["round"]}회차</dd>'
          f'<dt>모집 인원</dt><dd>{c["n"]}명</dd><dt>1인당 지급</dt><dd>{c["reward"]:,}P</dd>'
          f'<dt>예치</dt><dd>{c["deposit"]:,}P <small class="muted">(지급 {c["n"] * c["reward"]:,} + 수수료 {int(D.FEE * 100)}%)</small></dd>'
          f'<dt>{place[0]}</dt><dd>{place[1]}</dd>')
    if c["dts"]:
        tl = "".join(
            f'<li class="tl k-{k}{" past" if c["dts"][k] < 0 else ""}{" now" if c["dts"][k] == 0 else ""}"><i></i>'
            f'<b>{P.EXP_LABEL[ty] if k == "exp" else lab}</b><span>{P.mdw(c["dts"][k])}'
            f'{"" if c["past"] else " · " + G.due_label(c["dts"][k])}</span></li>' for k, lab in P.KIND)
        sched = f'<ol class="timeline">{tl}</ol>'
    else:
        sched = '<p class="muted">작성 중 — 일정을 아직 정하지 않았습니다.</p>'
    g = c["group"]
    can_ext = g in ("rec", "sel")
    exts = "".join(f'<option>{v}</option>' for v in ("+3일", "+5일", "+7일"))
    acts = (f'<div class="act-row"><b>모집 연장</b><select class="input sm" aria-label="연장 기간"{"" if can_ext else " disabled"}>{exts}</select>'
            f'<button type="button" class="btn sm js-flash" data-msg="모집 마감을 연장했습니다 · 이력에 남음"{"" if can_ext else " disabled"}>연장</button></div>'
            f'<div class="act-row"><b>조기 마감</b><span class="muted">지금까지 신청한 사람 중에서 선정</span>'
            f'<button type="button" class="btn sm js-flash" data-msg="모집을 마감했습니다 · 선정 중으로 넘어감"{"" if g == "rec" else " disabled"}>마감</button></div>'
            f'<div class="act-row"><b>추가모집</b><span class="muted">인원 늘리기 · 추가 모집 · 대체 리뷰어 — 비용 미리보기는 대시보드 패널</span>'
            f'<a class="btn sm" href="dashboard.html#biz={b["id"]}"{"" if g in D.ACTIVE else " aria-disabled=true"}>열기</a></div>'
            f'<div class="act-row"><b>조건 수정</b><span class="muted">{"전부 고칠 수 있음" if g == "draft" else "진행 중에는 안내문·가이드만 — 인원·지급액은 추가모집으로"}</span>'
            f'<button type="button" class="btn sm js-flash" data-msg="시안: 수정 화면은 등록 단계를 그대로 씁니다">수정</button></div>'
            f'<div class="act-row"><b>복제</b><span class="muted">같은 업체 → {c["round"] + 1}회차 · 다른 업체 → 1회차</span>'
            f'<a class="btn sm" href="campaign_new.html#copy={c["id"]}">복제</a></div>'
            f'<div class="act-row"><b>중단</b><span class="muted">남은 예치금은 지갑으로 복귀(기존 정책)</span>'
            f'<button type="button" class="btn sm ghost-danger js-flash" data-msg="시안: 중단은 확인 창을 한 번 더 띄웁니다"{"" if g in D.ACTIVE else " disabled"}>중단</button></div>')
    chips = "".join(f'<a class="ichip {G.due_class(d)}" href="dashboard.html#open={b["id"]}-{k}">{G.ISSUE_NAME[k]} {n}<small>{G.due_label(d)}</small></a>'
                    for k, (n, d) in c["iss"].items()) or '<span class="muted">걸린 이슈가 없습니다</span>'
    return (f'<div class="ov-grid"><section class="card"><h3 class="sec-t">조건</h3><dl class="kv2">{kv}</dl></section>'
            f'<section class="card"><h3 class="sec-t">일정</h3>{sched}</section>'
            f'<section class="card wide"><h3 class="sec-t">할 수 있는 일 <small>대시보드에 없는 일</small></h3>{acts}</section>'
            f'<section class="card wide"><h3 class="sec-t">걸린 이슈 <small>처리는 대시보드에서</small></h3><div class="ichips">{chips}</div></section></div>')


A_ST = {"new": ("st-purple", "새 신청"), "wait": ("st-gray", "대기"), "sel": ("st-blue", "선정"),
        "no": ("st-gray", "미선정"), "cancel": ("st-red", "취소 요청"), "hold": ("st-orange", "보류")}


def app_row(c, a, can_pick):
    need = not a["bi"] and not a["hist"]
    cls, lab = A_ST[a["st"]]
    if a["st"] == "cancel":
        act = '<button type="button" class="btn sm js-flash" data-msg="취소를 승인했습니다 · 빈자리는 대체 리뷰어 모집으로">취소 승인</button>'
    elif can_pick and a["st"] in ("new", "wait"):
        lock = ' disabled title="블로그를 먼저 확인하세요"' if need else ""
        act = (f'<button type="button" class="btn sm primary js-pick"{lock}>선정</button>'
               '<button type="button" class="btn sm js-hold">보류</button>')
    elif a["st"] == "sel" and c["ty"] == "s":
        act = '<span class="muted small">📦 배송정보 보기 가능</span>'
    elif a["st"] == "sel" and c["ty"] == "p":
        act = '<span class="muted small">자료 받아 감 ✓</span>'
    else:
        act = ""
    gate = '<span class="gate">근거 없음 · 블로그를 열어 확인한 뒤 선정</span>' if need and can_pick and a["st"] in ("new", "wait") else ""
    return (f'<tr class="arow a-{"wait" if a["st"] == "new" else a["st"]}{" need-check" if need else ""}">'
            f'<td><b>{a["nick"]}</b><small class="muted"> · {a["ago"]}일 전</small><br><a href="#" class="blog-open js-blog">블로그 보기 ↗</a></td>'
            f'<td class="evcell">{G.evidence_html(a["bi"], a["hist"])}{gate}</td>'
            f'<td class="muted">"{a["memo"]}"</td><td class="js-ast"><span class="st {cls}">{lab}</span></td><td><div class="acts">{act}</div></td></tr>')


def tab_app(c):
    if c["group"] == "draft":
        return '<p class="empty-tab">작성 중인 캠페인 — 모집을 시작하면 신청자가 여기에 쌓입니다.</p>'
    can = c["group"] in ("rec", "sel")
    cid = c["id"]
    f = [("all", "전체"), ("wait", "대기"), ("sel", "선정"), ("hold", "보류")]
    radios = "".join(f'<input type="radio" name="af-{cid}" id="af-{cid}-{k}" class="vr af-{k}"{" checked" if k == "all" else ""}>' for k, _l in f)
    chips = "".join(f'<label for="af-{cid}-{k}" class="pill">{lab}</label>' for k, lab in f)
    rows = "".join(app_row(c, a, can) for a in c["rows"])
    more = (f'<p class="muted small">신청 {c["applied"]}명 중 {D.SHOW_APPS}명만 보여 줍니다(시안) — 실제는 페이지 넘김</p>' if c["applied"] > D.SHOW_APPS else "")
    head = (f'<p class="tab-sum">신청 <b>{c["applied"]}</b> · 선정 <b class="js-selc">{c["sel"]}</b>/{c["n"]}명'
            f'{" · 선정 마감 " + P.md(c["dts"]["sel"]) if c["dts"] and can else ""}</p>')
    note = ('<p class="note">선정 근거(블로그지수 · 뷰마 이력 · 평점)가 줄마다 보입니다. 둘 다 없는 첫 참여 리뷰어는 블로그를 열어 본 뒤 선정할 수 있어요.</p>'
            if can else '<p class="note">선정이 끝난 캠페인 — 기록만 봅니다. 취소 요청은 여기서 승인합니다.</p>')
    return (f'{radios}<div class="tab-tools">{head}<div class="afs">{chips}</div></div>{note}'
            f'<table class="mini atable"><thead><tr><th>리뷰어</th><th>선정 근거</th><th>신청 메모</th><th>상태</th><th></th></tr></thead>'
            f'<tbody>{rows}</tbody></table>{more}')


R_ST = {"pend": ("st-purple", "검수 대기"), "ok": ("st-green", "승인"), "fix": ("st-orange", "수정 요청"), "unreg": ("st-red", "미등록")}


def tab_rev(c):
    if not c["revs"]:
        when = f' (리뷰 마감 {P.md(c["dts"]["rev"])})' if c["dts"] else ""
        return f'<p class="empty-tab">아직 리뷰 단계가 아닙니다{when}.</p>'
    rows = []
    for v in c["revs"]:
        cls, lab = R_ST[v["st"]]
        if v["st"] == "pend":
            act = ('<div class="checks"><label><input type="checkbox" checked> 필수 키워드</label><label><input type="checkbox" checked> 글자 수</label>'
                   '<label><input type="checkbox"> 사진 5장</label><label><input type="checkbox" checked> 광고 표시</label></div>'
                   '<button type="button" class="btn sm primary js-rv" data-to="승인">승인</button>'
                   '<button type="button" class="btn sm js-rv" data-to="수정 요청">수정 요청</button>'
                   '<button type="button" class="btn sm ghost-danger js-rv" data-to="반려">반려</button>')
        elif v["st"] == "unreg":
            act = '<button type="button" class="btn sm js-flash" data-msg="등록 요청 알림을 보냈습니다">등록 요청 알림</button>'
        else:
            act = ""
        link = '<span class="muted">—</span>' if v["st"] == "unreg" else f'<a href="#" class="ext">{v["ch"]} 리뷰 보기 ↗</a> <small class="muted">{v["ago"]}일 전</small>'
        rows.append(f'<tr><td><b>{v["nick"]}</b></td><td>{link}</td><td class="js-ast"><span class="st {cls}">{lab}</span></td><td><div class="acts wrap">{act}</div></td></tr>')
    ok = sum(1 for v in c["revs"] if v["st"] == "ok")
    pend = sum(1 for v in c["revs"] if v["st"] == "pend")
    return (f'<div class="tab-tools"><p class="tab-sum">승인 <b>{ok}</b>/{c["n"]} · 검수 대기 <b>{pend}</b>'
            f'{" · 리뷰 마감 " + P.md(c["dts"]["rev"]) if c["dts"] else ""}</p></div>'
            f'<table class="mini rtable"><thead><tr><th>리뷰어</th><th>리뷰</th><th>상태</th><th>검수</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


P_ST = {"wait": ("st-purple", "지급 대기"), "done": ("st-green", "지급 완료"), "noacc": ("st-red", "계좌 미등록")}


def tab_pay(c):
    paid = sum(p["amt"] for p in c["pays"] if p["st"] == "done")
    wait = sum(p["amt"] for p in c["pays"] if p["st"] != "done")
    back = max(0, c["deposit"] - int((paid + wait) * (1 + D.FEE))) if c["group"] == "end" else 0
    kv = (f'<dl class="paysum"><dt>예치</dt><dd>{c["deposit"]:,}P</dd><dt>지급 완료</dt><dd>{paid:,}P</dd>'
          f'<dt>지급 대기</dt><dd>{wait:,}P</dd><dt>{"지갑 복귀" if c["group"] == "end" else "복귀 예정"}</dt>'
          f'<dd>{back:,}P</dd></dl><p class="note">지급액에 수수료 {int(D.FEE * 100)}%를 더해 차감합니다(5,000 지급 → 5,500 차감). 완료·중단 시 남은 예치금은 지갑으로.</p>')
    if not c["pays"]:
        return kv + '<p class="empty-tab">아직 지급할 리뷰가 없습니다 — 검수 승인된 리뷰부터 지급 대기에 올라옵니다.</p>'
    rows = "".join(f'<tr><td><b>{p["nick"]}</b></td><td class="num">{p["amt"]:,}P</td>'
                   f'<td><span class="st {P_ST[p["st"]][0]}">{P_ST[p["st"]][1]}</span></td>'
                   f'<td class="muted small">{"리뷰어에게 계좌 등록 알림 보냄" if p["st"] == "noacc" else ""}</td></tr>' for p in c["pays"])
    n_wait = sum(1 for p in c["pays"] if p["st"] == "wait")
    btn = (f'<div class="acts wide"><button type="button" class="btn primary js-flash" data-msg="지급을 확정했습니다 · 정산 내역에 남음">지급 확정 {n_wait}명</button>'
           '<span class="muted small">관리자 = 확정 · 팀장/담당자 = 지급 요청(8-3)</span></div>' if n_wait else "")
    return kv + f'<table class="mini"><thead><tr><th>리뷰어</th><th class="num">금액</th><th>상태</th><th></th></tr></thead><tbody>{rows}</tbody></table>{btn}'


def tab_log(c):
    b = c["b"]
    who = b["owner"][1] if b["owner"] else "대표"
    d = c["dts"] or {}
    ev = []
    if c["group"] == "draft":
        ev = [("11/8 16:10", who, "작성 중으로 저장 — 잔액 부족(예치 예정 " + f'{c["deposit"]:,}P)')]
    else:
        ev.append((P.md(d["rec"] - 7) + " 10:12", who, f'캠페인 등록 · 예치 {c["deposit"]:,}P'))
        ev.append((P.md(d["rec"] - 7) + " 10:12", "시스템", "모집 시작"))
        if c["group"] != "rec":
            ev.append((P.md(d["rec"]) + " 23:59", "시스템", f'모집 마감 · 신청 {c["applied"]}명'))
        if c["group"] in ("exp", "rev", "pay", "end"):
            ev.append((P.md(d["sel"]) + " 14:30", who, f'선정 {c["sel"]}명 · 발표'))
        if c["group"] in ("rev", "pay", "end"):
            ev.append((P.md(d["rev"] - 3) + " 09:05", who, "검수 승인 " + str(sum(1 for v in c["revs"] if v["st"] == "ok")) + "건"))
        if c["state"] == "중단":
            ev.append((P.md(d["exp"]) + " 11:20", "대표", "캠페인 중단 · 남은 예치금 지갑 복귀"))
        elif c["group"] == "end":
            ev.append((P.md(d["rev"] + 3) + " 18:00", "대표", "지급 확정 · 완료"))
        if c["watch"]:
            ev.append(("오늘 09:41", c["watch"], "신청자 목록 열람"))
    lis = "".join(f'<li><span class="muted">{t}</span> <b>{w}</b> {esc(x)}</li>' for t, w, x in reversed(ev))
    return f'<ul class="logs big">{lis}</ul><p class="note">누가 · 언제 · 무엇을 — 담당자 변경·조건 수정·연장·마감·선정·검수·지급이 모두 남습니다.</p>'


def tab_rep(c):
    b = c["b"]
    ok = [v for v in c["revs"] if v["st"] == "ok"]
    links = "".join(f'<li><b>{v["nick"]}</b> <a href="#" class="ext">{v["ch"]} 리뷰 ↗</a></li>' for v in ok) \
        or '<li class="muted">승인된 리뷰가 아직 없습니다</li>'
    return (f'<p class="tab-sum">이 캠페인은 <b>{esc(b["name"])} 11월 보고서</b>에 들어갑니다.</p>'
            f'<dl class="paysum"><dt>모집</dt><dd>{c["n"]}명</dd><dt>신청</dt><dd>{c["applied"]}명</dd>'
            f'<dt>등록된 리뷰</dt><dd>{len(ok)}건</dd></dl>'
            f'<h3 class="sec-t">보고서에 실리는 리뷰</h3><ul class="replinks">{links}</ul>'
            f'<div class="acts wide"><a class="btn" href="biz.html#biz={b["id"]}">업체 보고서 링크 →</a></div>'
            '<p class="note">보고서는 업체 고객용 — 리워드·포인트·수수료 금액은 나오지 않습니다.</p>')


def detail(c):
    b, cid = c["b"], c["id"]
    tabbar = "".join(f'<a href="#c-{cid}-{k}" class="ctab ctab-{k}">{lab}{tab_badge(c, k)}</a>' for k, lab in TABS)
    body = {"ov": tab_ov, "app": tab_app, "rev": tab_rev, "pay": tab_pay, "log": tab_log, "rep": tab_rep}
    panes = "".join(f'<div class="ctp ctp-{k}" id="c-{cid}-{k}">{body[k](c)}</div>' for k, _l in TABS)
    watch = (f'<span class="watch" title="같은 캠페인을 다른 직원이 열어 두었습니다"><i></i>{c["watch"]}님이 보고 있습니다</span>' if c["watch"] else "")
    owner = b["owner"][1] if b["owner"] else "미담당"
    return (f'<section class="cdetail cg-{c["ty"]}" id="c-{cid}" aria-label="{esc(c["name"])}">'
            f'<header class="cd-h"><a class="back" href="#">← 캠페인 목록</a>'
            f'<p class="pane-biz">{esc(b["name"])} <span>담당 {owner} · 업체 담당자를 따름</span>{watch}</p>'
            f'<h1 class="cd-title">{P.ty_badges(c["name"])}<b>{esc(c["name"])}</b><small class="rnd">{c["round"]}회차</small>{state_badge(c)}</h1>'
            f'<nav class="ctabs" aria-label="캠페인 탭">{tabbar}</nav></header>'
            f'<div class="cd-b">{panes}</div></section>')


def tab_badge(c, k):
    n = {"app": sum(n for kk, (n, _d) in c["iss"].items() if ISSUE_TAB[kk] == "app"),
         "rev": sum(n for kk, (n, _d) in c["iss"].items() if ISSUE_TAB[kk] == "rev"),
         "pay": sum(n for kk, (n, _d) in c["iss"].items() if ISSUE_TAB[kk] == "pay")}.get(k, 0)
    return f' <em>{n}</em>' if n else ""


def campaigns_page():
    body = (f'<section class="board camp-page" aria-labelledby="t-camp">{list_view()}'
            f'{"".join(detail(c) for c in D.CAMPS)}</section>')
    return P.page("캠페인", "camp", body, None, '<link rel="stylesheet" href="css/campaigns.css">', "campaigns.js")


if __name__ == "__main__":
    (P.ROOT / "campaigns.html").write_text(campaigns_page(), encoding="utf-8")
    (P.ROOT / "campaign_new.html").write_text(camp_new.page(), encoding="utf-8")
    print(f"written campaigns.html · campaign_new.html · 캠페인 {len(D.CAMPS)}")
