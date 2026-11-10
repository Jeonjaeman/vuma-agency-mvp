# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.7] 보고서 화면 생성기 (기획서 v0.7 6-9)
  reports.html = 대행사 안에서 보는 보고서 링크 관리(목록 · 만들기 창 · 켜기/끄기 · 복사)
  report.html  = 업체 고객이 링크로 여는 공개 화면(로그인 없음) — 셸 없이 대행사 상호가 머리, 뷰마는 꼬리말 한 줄
    ★ 금액(리워드 · 포인트 · 수수료)은 어디에도 넣지 않는다(회의 24:32)
    공개 화면 상태 5가지: 정상 · 만료 · 꺼짐 · 원본 없음 · 기간 내 캠페인 0건 → 주소 #rp-... / #st-... + CSS :target (JS 없음)
  실행: python -I build/gen_reports.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402

P, G = D.P, D.G
esc = P.esc
AGENCY = "애니라인 마케팅"
TITLES = ["{b} 다녀왔어요 — 솔직 후기", "{b} 방문기 | 분위기·메뉴 총정리", "[{b}] 내돈내산 아닌 체험 후기", "{b} 재방문 의사 100%",
          "주말에 {b} 가 봤어요", "{b} 꼼꼼 리뷰 (사진 많음)"]


def reviews(c):
    """보고서에 실리는 리뷰 — 검수 승인된 것만. 제목 · 게시일 · 채널 · 광고 표시(검수자 체크)"""
    r = random.Random(f"rv-{c['id']}")
    out = []
    for v in c["revs"]:
        if v["st"] != "ok":
            continue
        out.append({"nick": v["nick"], "title": r.choice(TITLES).format(b=c["b"]["name"].split()[-1]),
                    "day": P.md((c["dts"]["rev"] if c["dts"] else 0) - r.randint(1, 8)), "ch": c["ch"], "ad": r.random() > .08})
    return out


def make_reports():
    """보고서 링크 더미 — 업체 단위(월) 대부분 + 캠페인 단위 몇 개, 상태 섞기"""
    r = random.Random("reports")
    out = []
    for b in P.BIZS:
        cs = [c for c in D.CAMPS if c["bid"] == b["id"] and c["group"] != "draft"]
        who = b["owner"][1] if b["owner"] else "대표"
        if not cs:
            continue
        st = "on" if r.random() > .15 else "off"
        out.append({"id": f"rp-{b['id']}-11", "b": b, "unit": "biz", "title": f"{b['name']} 11월 보고서", "period": "11/1 – 11/30",
                    "camps": [c for c in cs if not c["past"]], "st": st, "exp": "12/9" if st == "on" else "12/9",
                    "views": r.randint(0, 9), "by": who, "made": P.md(-r.randint(1, 9))})
        if r.random() < .45:
            past = [c for c in cs if c["past"]]
            out.append({"id": f"rp-{b['id']}-10", "b": b, "unit": "biz", "title": f"{b['name']} 10월 보고서", "period": "10/1 – 10/31",
                        "camps": past, "st": "exp", "exp": "11/8", "views": r.randint(1, 14), "by": who, "made": "10/9"})
        if r.random() < .2:
            c = r.choice(cs)
            out.append({"id": f"rp-{c['id']}", "b": b, "unit": "camp", "title": f"{c['name']} {c['round']}회차 보고서", "period": "캠페인 전체",
                        "camps": [c], "st": "on", "exp": "12/20", "views": r.randint(0, 4), "by": who, "made": P.md(-1)})
    # 원본 없음(보관된 업체) · 0건 예시 한 줄씩
    out.append({"id": "rp-gone", "b": None, "unit": "biz", "title": "해방촌 꽃집 10월 보고서", "period": "10/1 – 10/31", "camps": [],
                "st": "gone", "exp": "11/30", "views": 6, "by": "대표", "made": "10/12"})
    return out


REPORTS = make_reports()


def n_reviews(rp):
    return sum(len(reviews(c)) for c in rp["camps"])


# 공개 화면 첫 보고서(주소 없이 열 때) = 리뷰가 가장 많은 정상 보고서 — 시안에서 내용이 꽉 찬 모습을 먼저 보이게
LIVE = sorted((x for x in REPORTS if x["st"] == "on" and x["camps"]), key=lambda x: -n_reviews(x))
ST = {"on": ("st-green", "켜짐"), "off": ("st-gray", "꺼짐"), "exp": ("st-orange", "만료"), "gone": ("st-red", "원본 없음")}


def pub_href(rp):
    """공개 화면 주소 — 상태가 정상이 아니면 그 상태 화면으로(실제는 같은 주소에서 서버가 고름)"""
    if rp["st"] == "on":
        return f'report.html#{rp["id"]}' if rp["camps"] else "report.html#st-empty"
    return {"off": "report.html#st-off", "exp": "report.html#st-exp", "gone": "report.html#st-gone"}[rp["st"]]


# ════════════════ 관리 화면 ════════════════
def rep_row(rp):
    cls, lab = ST[rp["st"]]
    n_rev = sum(len(reviews(c)) for c in rp["camps"])
    sid = rp["b"]["owner"][0] if rp["b"] and rp["b"]["owner"] else "un"
    toggle = {"on": '<button type="button" class="btn sm js-toggle" data-to="off">끄기</button>',
              "off": '<button type="button" class="btn sm js-toggle" data-to="on">켜기</button>',
              "exp": '<button type="button" class="btn sm js-toggle" data-to="on">30일 다시 켜기</button>',
              "gone": '<span class="muted small">보관된 업체</span>'}[rp["st"]]
    unit = "업체" if rp["unit"] == "biz" else "캠페인"
    return (f'<tr class="rrow r-{rp["st"]}" data-owner="{sid}" data-name="{esc(rp["title"])}">'
            f'<th scope="row"><b>{esc(rp["title"])}</b><br><small class="muted">{unit} 단위 · {rp["period"]} · 캠페인 {len(rp["camps"])} · 리뷰 {n_rev}</small></th>'
            f'<td class="js-rst"><span class="st {cls}">{lab}</span></td><td>{rp["exp"]}</td><td class="num">{rp["views"]}</td>'
            f'<td>{rp["by"]} <small class="muted">{rp["made"]}</small></td>'
            f'<td><div class="acts"><button type="button" class="btn sm js-copy" data-url="https://report.vuma.example/{rp["id"]}"'
            f'{" disabled" if rp["st"] == "gone" else ""}>링크 복사</button>{toggle}'
            f'<a class="btn sm ghost" href="{pub_href(rp)}" target="_blank" rel="noopener">미리보기 ↗</a></div></td></tr>')


def make_pop():
    bizs = "".join(f'<option>{esc(b["name"])}</option>' for b in P.BIZS)
    return f'''<div id="pop-rep" popover class="pop" aria-labelledby="pop-rep-t">
	<header><h2 id="pop-rep-t">보고서 링크 만들기</h2><button type="button" class="t-x dark" popovertarget="pop-rep" popovertargetaction="hide" aria-label="닫기">✕</button></header>
	<div class="pop-b">
		<p class="fl">단위</p><div class="tagrs"><label class="tagr"><input type="radio" name="ru" checked><span>업체 · 기간</span></label>
			<label class="tagr"><input type="radio" name="ru"><span>캠페인 하나</span></label></div>
		<label class="fl">업체 <select class="input">{bizs}</select></label>
		<label class="fl">기간 <span class="row2"><input type="date" class="input" value="2026-11-01"> ~ <input type="date" class="input" value="2026-11-30"></span></label>
		<label class="fl">만료 <select class="input"><option>30일 뒤 (기본)</option><option>7일 뒤</option><option>90일 뒤</option></select></label>
		<p class="note">업체 고객은 로그인 없이 링크로 봅니다. 리워드·포인트·수수료 금액은 나오지 않습니다.</p></div>
	<footer><button type="button" class="btn" popovertarget="pop-rep" popovertargetaction="hide">취소</button>
		<button type="button" class="btn primary js-flash" data-msg="링크를 만들고 복사했습니다 · 만료 12/10">만들고 복사</button></footer>
</div>'''


def reports_page():
    cnt = {k: sum(1 for x in REPORTS if x["st"] == k) for k in ST}
    f = [("all", f"전체 {len(REPORTS)}"), ("on", f"켜짐 {cnt['on']}"), ("exp", f"만료 {cnt['exp']}"), ("off", f"꺼짐 {cnt['off']}")]
    radios = "".join(f'<input type="radio" name="rf" id="rf-{k}" class="vr"{" checked" if k == "all" else ""}>' for k, _l in f)
    chips = "".join(f'<label for="rf-{k}" class="pill">{lab}</label>' for k, lab in f)
    rows = "".join(rep_row(x) for x in REPORTS)
    states = "".join(f'<a class="pill" href="report.html#{h}" target="_blank" rel="noopener">{lab}</a>' for h, lab in
                     [(LIVE[0]["id"], "정상"), ("st-exp", "만료"),
                      ("st-off", "꺼짐"), ("st-gone", "원본 없음"), ("st-empty", "기간 내 캠페인 0건")])
    body = f'''<section class="board reports" aria-labelledby="t-rep">
	<div class="board-h"><div><h1 id="t-rep">보고서</h1>
		<p class="sub">업체 고객(사장님·원장님)에게 보내는 링크 — 로그인 없이 열림 · 기본 만료 30일 · <b>금액은 나오지 않음</b></p></div>
		<button type="button" class="btn primary" popovertarget="pop-rep">+ 보고서 링크 만들기</button></div>
	{radios}
	<div class="s-tools"><label class="search b-search"><span class="sr">보고서 검색</span><input type="search" class="js-rsearch" placeholder="업체명·캠페인명"></label>
		<div class="rfs" role="group" aria-label="상태">{chips}</div></div>
	<div class="s-tools pubs"><b class="small">공개 화면 미리보기</b>{states}</div>
	<div class="grid-wrap"><table class="btable rtable2"><thead><tr><th>보고서</th><th>상태</th><th>만료</th><th class="num">열람</th>
		<th>만든 사람</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
</section>{make_pop()}'''
    return P.page("보고서", "rep", body, None, '<link rel="stylesheet" href="css/settle.css">', "settle.js")


# ════════════════ 공개 화면 ════════════════
def pub_report(rp, first):
    camps = rp["camps"]
    revs = {c["id"]: reviews(c) for c in camps}
    n_rev = sum(len(v) for v in revs.values())
    tot = [("캠페인", len(camps)), ("모집", sum(c["n"] for c in camps)), ("선정", sum(c["sel"] for c in camps)), ("등록된 리뷰", n_rev)]
    kp = "".join(f'<div class="pk"><p>{k}</p><b>{v}</b></div>' for k, v in tot)
    secs = []
    for c in camps:
        lis = "".join(f'<li><a href="https://blog.naver.com/" class="rt" target="_blank" rel="noopener">{esc(v["title"])} ↗</a><span class="rm">{v["nick"]} · {v["ch"]} · {v["day"]}'
                      f'{" · <i class=ad>광고 표시 ✓</i>" if v["ad"] else " · <i class=noad>광고 표시 확인 중</i>"}</span></li>'
                      for v in revs[c["id"]]) or '<li class="none">아직 등록된 리뷰가 없습니다 — 리뷰 마감 후 채워집니다</li>'
        state = "진행 중" if c["group"] in D.ACTIVE else c["state"]
        secs.append(f'<section class="pc cg-{c["ty"]}"><header><span class="ty ty-{c["ty"]}">{G.TYPE_NAME[c["ty"]]}</span>'
                    f'<span class="chn">{c["ch"]}</span><h3>{esc(c["name"])} <small>{c["round"]}회차</small></h3><span class="pst">{state}</span></header>'
                    f'<p class="pcn">모집 {c["n"]}명 · 신청 {c["applied"]}명 · 선정 {c["sel"]}명 · 리뷰 {len(revs[c["id"]])}건</p>'
                    f'<ol class="rlist">{lis}</ol></section>')
    return (f'<article class="rp{" first" if first else ""}" id="{rp["id"]}">'
            f'<p class="rp-k">{"업체 보고서" if rp["unit"] == "biz" else "캠페인 보고서"} · {rp["period"]}</p>'
            f'<h1>{esc(rp["title"])}</h1><p class="rp-meta">링크 만료 {rp["exp"]} · 만든 날 {rp["made"]}</p>'
            f'<div class="pks">{kp}</div>{"".join(secs)}</article>')


STATE_PAGES = [("st-exp", "⏰", "링크 기간이 끝났습니다", "보고서를 보내 준 담당자에게 새 링크를 요청해 주세요."),
               ("st-off", "🔒", "지금은 볼 수 없는 보고서입니다", "대행사가 링크를 껐습니다. 담당자에게 문의해 주세요."),
               ("st-gone", "📁", "보고서 원본이 없습니다", "업체 정보가 보관되었거나 캠페인이 정리되었습니다."),
               ("st-empty", "🗓️", "이 기간에는 캠페인이 없습니다", "기간 안에 진행한 캠페인이 0건입니다. 다른 기간 보고서를 요청해 주세요.")]


def public_page():
    arts = [pub_report(x, i == 0) for i, x in enumerate(LIVE)]
    states = "".join(f'<article class="rp rp-state" id="{i}"><p class="big">{e}</p><h1>{t}</h1><p class="muted">{d}</p></article>'
                     for i, e, t, d in STATE_PAGES)
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>캠페인 보고서 · {AGENCY}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="css/report.css">
</head>
<body>
<!-- [2026-11-10] 보고서 공개 화면 시안 {G.VERSION} — 업체 고객용(로그인 없음). build/gen_reports.py 로 생성(직접 수정 금지)
     보고서마다 article 하나, 주소 #rp-... 가 가리키는 것만 보임(:target). 주소가 없으면 첫 보고서. 금액은 넣지 않음 -->
<header class="top"><span class="logo" aria-hidden="true">A</span><b>{AGENCY}</b><span class="muted">캠페인 결과 보고서</span></header>
<main class="wrap">{"".join(arts)}{states}</main>
<footer class="foot">이 보고서는 뷰마(VUMA)로 만들었습니다 · 리뷰 링크는 각 채널 원문으로 연결됩니다</footer>
</body>
</html>
'''


if __name__ == "__main__":
    (P.ROOT / "reports.html").write_text(reports_page(), encoding="utf-8")
    (P.ROOT / "report.html").write_text(public_page(), encoding="utf-8")
    print(f"written reports.html · report.html · 보고서 {len(REPORTS)}")
