# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 운영 — 리뷰어 관리 · 리뷰 검수 · 포인트 지급 확인 (광고주 화면 그대로 + 대행사 추가분)
  광고주: reviewer.inc.html · reviewInspect.inc.html(+Modal) · payoutCheck.inc.html  (조사\광고주_운영화면_스펙_20261110.md)
  업체 범위: 줄마다 data-biz → js/scope.js 가 다른 업체 줄을 숨김. 업체·담당자 칸 = .col-biz(한 업체 범위면 숨김 · Q18)
  리뷰어 카드는 "전체 업체" 용(.all-only, 업체 칸 있음)과 업체마다(.biz-only, data-biz) 두 벌 — 한 업체 범위면 그 업체 것만
  관심·차단 리뷰어 = 대행사 공용(Q14 안) → 업체 범위와 상관없이 보임
  거르기(select) = option:checked + :has() (JS 없음). 검수·지급 묶음 확정 표시만 JS.
  실행: python -I build/gen_ops.py  →  reviewers.html · inspect.html · payout.html
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402
import gen_campaigns as C  # noqa: E402  (광고주 상태 · 캠페인 코드 · 지역)
import gen_settle as S  # noqa: E402  (지급 묶음 — 대행사 추가분)

P, G = D.P, D.G
esc = K.esc


def camp_opts(camps, first):
    return f'<option value="">{first}</option>' + "".join(
        f'<option value="{c["id"]}">[{C.code(c)}] {esc(c["name"])} · {esc(c["b"]["name"])}</option>' for c in camps)


def select_rules(sel_id, values, row_cls):
    """select 고른 값으로 줄 거르기 — option:checked 를 :has() 로 읽는다(값마다 규칙 1줄)"""
    return "".join(f'.ops:has(#{sel_id} option[value="{v}"]:checked) .{row_cls}:not(.v-{v}){{display:none}}' for v in values)


# ════════════════════════ 리뷰어 관리 ════════════════════════
def reviewers():
    """리뷰어(닉네임) → 신청·선정·리뷰 기록. 캠페인 더미의 같은 닉네임을 묶는다"""
    out = {}
    for c in D.CAMPS:
        for a in c["rows"]:
            r = out.setdefault(a["nick"], {"nick": a["nick"], "apps": [], "bi": a["bi"], "hist": a["hist"], "cancel": []})
            r["apps"].append((c, a))
            if a["st"] == "cancel":
                r["cancel"].append(c)
    for i, r in enumerate(sorted(out.values(), key=lambda x: x["nick"])):
        rr = random.Random("rv-" + r["nick"])
        r.update({"no": i + 1, "reg": rr.choice(["서울 마포", "서울 강남", "경기 성남", "인천 연수", "부산 해운대"]),
                  "age": rr.choice([20, 30, 40]), "sex": rr.choice(["여", "남"]), "like": i % 4 == 0, "block": i == 5,
                  "report": i == 9, "pen": rr.choice([0, 0, 0, 3]), "today": rr.randint(20, 900), "total": rr.randint(5000, 400000),
                  "nb": rr.randint(80, 3000), "topic": rr.choice(["맛집", "육아", "뷰티", "여행", "일상"]), "insta": rr.randint(300, 12000)})
    return sorted(out.values(), key=lambda x: x["no"])


RVS = reviewers()


def rv_badges(r):
    b = [("st-red", "차단됨") if r["block"] else None, ("st-orange", "관심") if r["like"] else None,
         ("st-red", "신고함") if r["report"] else None, ("st-orange", f'패널티 {r["pen"]}점') if r["pen"] else None]
    return "".join(K.badge(*x) for x in b if x)


def rv_icons():
    names = [("☆", "관심 등록"), ("⊘", "차단"), ("✉", "쪽지"), ("✆", "문자 보내기 (포인트 차감)"), ("@", "메일"), ("🚩", "신고"), ("🎧", "1:1 문의")]
    return "".join(f'<button type="button" class="btn sm icon js-flash" data-msg="{t}(시안)" title="{t}" aria-label="{t}">{s}</button>' for s, t in names)


def rv_card(r, apps, shared=False):
    """리뷰어 카드 1장 — data-bizs = 신청한 업체들(한 업체 범위면 그 업체에 신청한 리뷰어만, 참여 캠페인도 그 업체 것만)
       shared=True(관심·차단 = 대행사 공용) → 업체 범위와 상관없이 보임"""
    bi = r["bi"]
    idx = (f'지수 <span class="bgrade g-{ {"최적화": "a", "준최적화": "b"}.get(bi["grade"], "c") }">{bi["grade"]}</span> {bi["score"]}/10'
           if bi else '지수 <span class="muted">없음</span>')
    camps = "".join(f'<li data-biz="{c["bid"]}">{C.step_badge(c)} <a href="campaigns.html#c-{c["id"]}">[{C.code(c)}] {esc(c["name"])}</a>'
                    f'<span class="col-biz add"> · {esc(c["b"]["name"])}</span> <small class="muted">{"선정" if a["st"] == "sel" else "신청"}</small></li>'
                    for c, a in apps)
    bizs = sorted({c["b"]["name"] for c, _a in apps})
    attr = "" if shared else f' data-bizs="{" ".join(sorted({c["bid"] for c, _a in apps}))}"'
    tags = f'<p class="rv-biz col-biz add">업체 {len(bizs)}곳 · {esc(", ".join(bizs[:3]))}{" …" if len(bizs) > 3 else ""}</p>'
    return (f'<article class="rvcard"{attr}><div class="rv-h"><input type="checkbox" aria-label="고르기"><span class="muted">{r["no"]}</span>'
            f'<span class="ava">{r["nick"][0]}</span><b>{r["nick"]}</b><span class="rv-ic">{rv_icons()}</span></div>'
            f'<p class="rv-m">{r["reg"]} | {r["age"]}대 | {r["sex"]} | 신청 {len(apps)}회 {rv_badges(r)}</p>'
            f'<p class="rv-m">블로그 | {idx} | 오늘 방문 {r["today"]:,} | 누적 방문 {r["total"]:,} | 이웃 {r["nb"]:,} | 주제 {r["topic"]}</p>'
            f'<p class="rv-m">인스타 instagram.com/{r["nick"]} | 팔로워 {r["insta"]:,}</p>{tags}'
            f'<div class="rv-x"><details><summary>참여 캠페인 {len(apps)}</summary><ul class="rv-l">{camps}</ul></details>'
            f'<details><summary>주고받은 쪽지 2</summary><p class="muted">11/6 방문 일정 문의 · 11/7 답장</p></details>'
            f'<details><summary>보낸 문자 0</summary></details><details><summary>보낸 메일 0</summary></details></div></article>')


def rv_list(rs, shared=False):
    """shared=True → 관심·차단(대행사 공용) 카드만 한 벌"""
    cards = [rv_card(r, r["apps"], shared) for r in rs]
    return f'<div class="rvlist">{"".join(cards)}</div>' if cards else '<p class="empty">리뷰어가 없습니다.</p>'


def cancel_list():
    rows = []
    for r in RVS:
        for c in r["cancel"]:
            rows.append(f'<div class="creq-c" data-biz="{c["bid"]}"><b>{r["nick"]}</b> <span class="st st-red">선정취소 요청</span> '
                        f'<a href="campaigns.html#c-{c["id"]}-app">[{C.code(c)}] {esc(c["name"])}</a> <span class="col-biz add">· {esc(c["b"]["name"])}</span>'
                        f' <span class="muted">11/8 · 일정이 맞지 않아요 · 취소해도 추가 비용은 없습니다</span> '
                        f'{K.btn("선정취소", "선정을 취소했습니다")}{K.btn("요청 거절", "요청을 거절했습니다")}</div>')
    return "".join(rows) or '<p class="empty">선정취소 요청이 없습니다.</p>'


def build_reviewers():
    ncan = sum(len(r["cancel"]) for r in RVS)
    like = [r for r in RVS if r["like"]]
    block = [r for r in RVS if r["block"]]
    rep = [r for r in RVS if r["report"]]
    bar = K.fbar(K.select("캠페인", ["전체 캠페인"] + [f"[{C.code(c)}] {c['name']}" for c in D.CAMPS[:12]]),
                 K.search("리뷰어 이름 검색"), '<label class="small"><input type="checkbox"> 선정취소한 리뷰어 보기 0</label>',
                 '<span class="muted small">캠페인을 고르면 결과를 내려받을 수 있습니다</span>')
    bulk = (f'<div class="obulk"><label><input type="checkbox"> 전체선택</label><span class="muted">0명 선택</span>'
            f'{K.btn("쪽지", "쪽지 창(시안)")}{K.btn("문자", "문자 창(시안 · 포인트 차감)")}{K.btn("메일", "메일 창(시안)")}</div>')
    shared = '<p class="note add">관심·차단 리뷰어는 <b>대행사 공용</b>(Q14 안) — 한 업체에서 차단하면 대행사 모든 업체에서 차단됩니다.</p>'
    tabs = K.tabs("rv", [(f"전체 {len(RVS)}", bar + bulk + rv_list(RVS)),
                         (f"관심 리뷰어 {len(like)}", shared + rv_list(like, True)),
                         (f'선정취소 요청 <em>{ncan}</em>' if ncan else "선정취소 요청 0", cancel_list()),
                         (f"차단 리뷰어 {len(block)}", shared + rv_list(block, True)),
                         (f"신고한 리뷰어 {len(rep)}", rv_list(rep, True) + '<p class="help">운영자가 확인중입니다… · 처리 결과가 나오면 알림으로 알려드립니다.</p>')])
    body = (K.head("애니라인 마케팅님의 리뷰어 리스트", "광고주 리뷰어 관리와 같은 화면 — 대행사 모든 업체 캠페인에 신청한 리뷰어")
            + K.camp_tabs("rvw") + tabs)
    write("reviewers.html", "리뷰어 관리", "rvw", body)


# ════════════════════════ 리뷰 검수 ════════════════════════
IST = {"pend": ("pend", "st-purple", "검수대기"), "ok": ("ok", "st-green", "승인"), "fix": ("fix", "st-red", "반려")}


def insp_rows():
    rows = []
    for c in D.CAMPS:
        for v in c["revs"]:
            if v["st"] == "unreg":
                continue
            rows.append((c, v))
    rows.sort(key=lambda x: (x[1]["st"] != "pend", x[1]["ago"]))
    return rows


def mission(v):
    r = random.Random("ms-" + v["nick"] + v["ch"])
    if v["st"] == "pend" and r.random() < .25:
        return '<span class="mchip no">글자수✓ 사진✗</span>'
    return r.choice(['<span class="mchip">글자수✓ 사진✓</span>', '<span class="mchip">수동확인</span>', '<span class="mchip">조건없음</span>'])


def insp_tr(c, v):
    k, cls, lab = IST[v["st"]]
    b = c["b"]
    act = {"pend": '<button type="button" class="btn sm primary" popovertarget="pop-insp">검수</button>',
           "fix": K.btn("승인", "승인했습니다") + K.btn("재검수 요청", "재검수를 요청했습니다"),
           "ok": K.btn("재검수 요청", "재검수를 요청했습니다") + ' <small class="muted">11/16까지</small>'}[v["st"]]
    who = "" if v["st"] == "pend" else f'{P.md(-v["ago"] + 1)} · {"대행사 · " + C.owner_html(b) if b["owner"] else "운영자"}'
    reason = '<br><small class="bad">사유 : 사진 5장 미만</small>' if v["st"] == "fix" else ""
    ck = '<input type="checkbox" aria-label="고르기">' if v["st"] == "pend" else ""
    return (f'<tr class="irow v-{k} v-{c["id"]}" data-biz="{b["id"]}"><td class="ck">{ck}</td>'
            f'<td><a href="campaigns.html#c-{c["id"]}-rev">{esc(c["name"])}</a><br><small>#{C.code(c)}</small></td>'
            f'<td class="col-biz add">{K.biz_cell(b)}<br><small>{K.owner_of(b)}</small></td>'
            f'<td><b>{v["nick"]}</b></td><td>{v["ch"]}</td><td>{mission(v)}</td><td><span class="st {cls}">{lab}</span>{reason}</td>'
            f'<td class="muted">{P.md(-v["ago"])}</td><td><small>{who}</small></td><td><a href="#" class="ext">열기</a></td><td><div class="acts">{act}</div></td></tr>')


def insp_pop():
    rows = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in
                   [("글자수", "1,000자 이상", "충족"), ("사진", "5장 이상", "미충족"), ("필수 키워드", "#연남헤어", "충족"), ("광고 표시", "문구 포함", "수동확인")])
    return K.pop("pop-insp", "리뷰 검수",
                 '<p><b>맛집탐방러</b> · 블로그 <a href="#" class="ext">blog.naver.com/…</a></p>'
                 f'<table class="otable"><thead><tr><th>항목</th><th>기준</th><th>충족</th></tr></thead><tbody>{rows}</tbody></table>'
                 '<label class="fl">반려 사유 (반려 시 필수)<textarea></textarea></label>'
                 '<p class="help">※ 조건 미충족 상태로 승인하면 운영자에게도 통지됩니다.</p>'
                 f'<p>{K.btn("반려", "반려했습니다 · 리뷰어에게 알림", "btn")}</p>', "승인", "승인했습니다 · 지급 대기로 넘어갑니다")


def build_inspect():
    rows = insp_rows()
    camps = sorted({c["id"]: c for c, _v in rows}.values(), key=lambda c: C.code(c))
    st_sel = ('<label><span class="sr">상태</span><select id="ist" aria-label="상태"><option value="pend" selected>검수 대기</option>'
              '<option value="ok">승인</option><option value="fix">반려</option><option value="all">전체</option></select></label>')
    c_sel = f'<label><span class="sr">캠페인</span><select id="icp" aria-label="캠페인">{camp_opts(camps, "전체 캠페인")}</select></label>'
    style = ("<style>" + select_rules("ist", ["pend", "ok", "fix"], "irow") + select_rules("icp", [c["id"] for c in camps], "irow") + "</style>")
    heads = [("캠페인", ""), (f"업체 · 담당 {K.add_tag()}", "col-biz add"), ("리뷰어", ""), ("채널", ""), ("미션 충족", ""), ("상태", ""),
             ("제출일", ""), ("검수정보", ""), ("리뷰", ""), ("검수", "")]
    th = '<th class="ck"><input type="checkbox" class="js-ckall" aria-label="모두 고르기"></th>' + "".join(f'<th class="{c}">{h}</th>' for h, c in heads)
    npend = sum(1 for _c, v in rows if v["st"] == "pend")
    table = (f'<div class="owrap"><table class="otable"><thead><tr>{th}</tr></thead><tbody>{"".join(insp_tr(c, v) for c, v in rows)}</tbody></table>'
             f'<div class="obulk"><label>전체선택</label><span class="muted">검수대기 {npend}건</span>{K.btn("선택 일괄 승인", "고른 리뷰를 승인했습니다")}</div></div>')
    note = '<p class="note add">대시보드 "검수" 칸의 [상세 관리 →] 가 이 화면을 그 업체 범위로 엽니다. 검수 기한은 대시보드와 같은 숫자입니다.</p>'
    body = (style + K.head("애니라인 마케팅님의 리뷰 검수", "제출된 리뷰의 미션 충족 여부를 확인하고 승인/반려하세요.")
            + K.camp_tabs("insp") + K.fbar(st_sel, c_sel, count=f"검수대기 <b>{npend}</b>건") + table + note + insp_pop())
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


RLAB = {"unreg": "미제출", "pend": "검수대기", "ok": "검수완료", "fix": "반려"}


def pay_tr(c, v, p):
    b = c["b"]
    need = p and p["st"] == "noacc"
    if p and p["st"] == "done":
        pay = f'<span class="st st-green">지급완료</span> <small>{p["amt"]:,}P · {P.md(c["dts"]["rev"] + 2)}</small>'
    else:
        pay = f'<span class="st st-orange">지급대기</span> <small>예정 {c["reward"]:,}P</small>'
    flag = ' <b class="bad">● 확인 필요</b> <small class="muted add">계좌 미등록</small>' if need else ""
    wait = "" if p and p["st"] == "done" else " p-wait"
    return (f'<tr class="prow2 v-{c["id"]}{wait}{" need" if need else ""}" data-biz="{b["id"]}">'
            f'<td><a href="campaigns.html#c-{c["id"]}-rev">{esc(c["name"])}</a> <small>#{C.code(c)}</small></td>'
            f'<td class="col-biz add">{K.biz_cell(b)}<br><small>{K.owner_of(b)}</small></td>'
            f'<td><b>{v["nick"]}</b></td><td class="muted">{P.md(c["dts"]["sel"]) if c["dts"] else "-"}</td>'
            f'<td>{RLAB[v["st"]]}</td><td>{pay}{flag}</td></tr>')


def tab_check(rows):
    done = [(c, v, p) for c, v, p in rows if p and p["st"] == "done"]
    wait = [(c, v, p) for c, v, p in rows if not (p and p["st"] == "done")]
    need = sum(1 for _c, _v, p in rows if p and p["st"] == "noacc")
    camps = sorted({c["id"]: c for c, _v, _p in rows}.values(), key=lambda c: C.code(c))
    chips = (f'<p class="pchips"><span class="chip">선정 {len(rows)}건</span>'
             f'<span class="chip">지급완료 {len(done)}건 · {sum(p["amt"] for _c, _v, p in done):,}P</span>'
             f'<span class="chip {"bad" if wait else ""}">지급대기 {len(wait)}건 · {sum(c["reward"] for c, _v, _p in wait):,}P</span></p>')
    alert = f'<p class="alert-o">확인이 필요한 건이 {need}건 있습니다.</p>' if need else ""
    sel = f'<label><span class="sr">캠페인</span><select id="pcp" aria-label="캠페인">{camp_opts(camps, "캠페인 전체")}</select></label>'
    tog = '<input type="checkbox" id="pwait" class="vr"><label for="pwait" class="btn sm">지급대기만 보기</label>'
    heads = "".join(f'<th class="{c}">{h}</th>' for h, c in [("캠페인", ""), (f"업체 · 담당 {K.add_tag()}", "col-biz add"), ("리뷰어", ""),
                                                              ("선정일", ""), ("리뷰", ""), ("지급", "")])
    body = "".join(pay_tr(c, v, p) for c, v, p in rows) or '<tr><td colspan="6" class="empty">선정된 리뷰어가 아직 없습니다.</td></tr>'
    foot = ('<ul class="help"><li>지급은 캠페인 예치금(통포인트에서 묶인 돈)에서 나갑니다.</li><li>리뷰 검수완료 뒤 지급대기 → 뷰마가 지급하면 지급완료.</li>'
            '<li>계좌 미등록 리뷰어는 등록하면 다음 지급에 들어갑니다.</li><li>지급 차감 = 지급액 + 플랫폼 수수료(5,000 → 5,500).</li></ul>')
    return (f'{chips}{alert}<div class="fbar">{sel}</div>{tog}'
            f'<div class="owrap"><table class="otable"><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>{foot}')


def build_payout():
    rows = pay_rows()
    camps = {c["id"] for c, _v, _p in rows}
    style = ("<style>" + select_rules("pcp", sorted(camps), "prow2")
             + "#pwait:checked ~ .owrap .prow2:not(.p-wait){display:none}#pwait:checked + label{background:var(--c-14);color:#fff}"
             + "label[for=pwait]{margin-bottom:10px}"
             + ".prow2.need td{background:#fff8f0}</style>")
    batches = ('<p class="note add">대행사 추가: 여러 업체 지급을 묶어 한 번에 확정합니다(v0.7 정산 › 리뷰어 지급). 업체 범위와 상관없이 대행사 전체 묶음입니다.</p>'
               '<input type="radio" name="role" id="role-admin" class="vr" checked><input type="radio" name="role" id="role-view" class="vr">'
               f'<div class="sp-p">{S.tab_pay()}</div>')
    body = (style + K.head("리뷰어 포인트 지급 확인",
                           "내 캠페인에 선정된 리뷰어에게 포인트가 실제로 지급되었는지 보여 드립니다. ※ 포인트를 지급하지 않는 캠페인(현물만 제공)은 이 목록에 나오지 않습니다.")
            + K.tabs("pc", [("지급 확인", tab_check(rows)), (f'지급 묶음 {K.add_tag()}', batches)]))
    (K.ROOT / "payout.html").write_text(P.page("포인트 지급 확인", "payc", f'<section class="ops">{body}</section>', None,
                                               K.CSS + '<link rel="stylesheet" href="css/settle.css">', "ops.js settle.js"), encoding="utf-8")
    print("written payout.html")


def write(fname, title, key, body):
    (K.ROOT / fname).write_text(P.page(title, key, f'<section class="ops">{body}</section>', None,
                                       K.CSS + '<link rel="stylesheet" href="css/campaigns.css">', "ops.js"), encoding="utf-8")
    print(f"written {fname}")


if __name__ == "__main__":
    build_reviewers()
    build_inspect()
    build_payout()
