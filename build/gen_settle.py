# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.7] 정산 화면 생성기 (기획서 v0.7 6-8 · 8-4)
  탭 3개(포인트 · 리뷰어 지급 · 업체별 사용내역) = 라디오 + CSS. 보는 사람(관리자 / 팀장·조회 = 열람) = 라디오 + CSS.
  충전 창 = popover 속성(JS 없음). 묶음 확정 표시 · 링크 복사 안내만 js/settle.js.
  돈 흐름(8-4): 충전 → 사용 가능 잔액, 캠페인 시작 = 잔액 → 예치, 지급 = 예치에서 차감(지급액 + 수수료), 완료·중단 = 남은 예치 → 잔액 복귀.
  실행: python -I build/gen_settle.py  →  mvp/settle.html
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402

P, G = D.P, D.G
esc = P.esc
TODAY = P.TODAY
OWNER = {b["id"]: (b["owner"][1] if b["owner"] else "미담당") for b in P.BIZS}
BANKS = ["국민은행", "신한은행", "우리은행", "하나은행", "카카오뱅크", "토스뱅크", "농협은행"]   # 실서버 $BANKLIST 이름


def won(n):
    return f"{n:,}P"


def signed(n):
    return f'<b class="{"ag-plus" if n > 0 else "ag-minus" if n < 0 else ""}">{"+" if n > 0 else ""}{n:,}P</b>'


# ════════════════ 포인트: 포인트 내역 ════════════════
def ledger():
    """포인트 내역 — 새 것부터. '사용 가능 잔액'은 지금 잔액에서 거꾸로 계산
      지급(예치에서 빠짐)은 사용 가능 잔액을 바꾸지 않는다 → 칸에 '예치에서'"""
    r = random.Random("ledger")
    ev = []   # (일수, 시각, 구분, 업체, 캠페인, 금액, 잔액에 영향?)
    for c in D.CAMPS:
        if not c["dts"]:
            continue
        b, start = c["b"], c["dts"]["rec"] - 7
        if start < -40:
            continue
        ev.append((start, f"{r.randint(9, 18):02d}:{r.randint(0, 59):02d}", "dep", b, c, -c["deposit"], True))
        for k, p in enumerate(x for x in c["pays"] if x["st"] == "done"):
            ev.append((c["dts"]["rev"] + 2, f"15:{10 + k:02d}", "pay", b, c, -int(p["amt"] * (1 + D.FEE)), False))
        if c["group"] == "end":
            used = sum(int(p["amt"] * (1 + D.FEE)) for p in c["pays"] if p["st"] == "done")
            back = c["deposit"] - used
            if back > 0:
                ev.append((c["dts"]["rev"] + 3, "18:00", "back", b, c, back, True))
    for off in (-38, -24, -12, -3):
        ev.append((off, "10:05", "charge", None, None, r.choice([1000000, 2000000, 3000000]), True))
    ev = [e for e in ev if e[0] <= 0]
    ev.sort(key=lambda e: (e[0], e[1]), reverse=True)
    bal = D.BALANCE
    rows = []
    for off, hm, kind, b, c, amt, moves in ev[:60]:
        rows.append((off, hm, kind, b, c, amt, bal if moves else None))
        if moves:
            bal -= amt
    return rows


KIND = {"charge": ("충전", "k-charge"), "dep": ("예치", "k-dep"), "pay": ("지급", "k-pay"), "back": ("예치금 복귀", "k-back")}


def tab_wallet():
    held = sum(c["deposit"] - sum(int(p["amt"] * (1 + D.FEE)) for p in c["pays"] if p["st"] == "done")
               for c in D.CAMPS if c["group"] in D.ACTIVE)
    rows = ledger()
    kinds = "".join(f'<input type="checkbox" id="lk-{k}" class="vr" checked>' for k in KIND)
    kchips = "".join(f'<label for="lk-{k}" class="lchip {cls}">{lab}</label>' for k, (lab, cls) in KIND.items())
    trs = "".join(
        f'<tr class="lrow l-{kind}"><td class="muted">{P.md(off)} {hm}</td><td><span class="lk {KIND[kind][1]}">{KIND[kind][0]}</span></td>'
        f'<td>{esc(b["name"]) if b else "—"}</td><td>{(esc(c["name"]) + f" <small class=rnd>{c["round"]}회차</small>") if c else "—"}</td>'
        f'<td class="ag-num">{signed(amt)}</td><td class="ag-num">{won(bal) if bal is not None else "<span class=muted>예치에서</span>"}</td></tr>'
        for off, hm, kind, b, c, amt, bal in rows)
    return f'''<div class="kpis">
		<div class="kpi"><p>포인트</p><b>{won(D.BALANCE + held)}</b><small>사용 가능 + 예치 중</small></div>
		<div class="kpi main"><p>사용 가능 잔액</p><b>{won(D.BALANCE)}</b><small>새 캠페인·추가모집에 쓸 수 있는 돈</small></div>
		<div class="kpi"><p>예치 중</p><b>{won(held)}</b><small>진행 캠페인 {sum(1 for c in D.CAMPS if c["group"] in D.ACTIVE)}개에 묶여 있음</small></div>
		<div class="kpi act"><button type="button" class="ag-btn primary w-admin" popovertarget="pop-charge">충전하기</button>
			<button type="button" class="ag-btn w-view js-flash" data-msg="관리자에게 충전 요청을 보냈습니다">관리자에게 충전 요청</button>
			<small>지갑 1개 · 내역에 업체·캠페인 표시(D3)</small></div>
	</div>
	{kinds}
	<div class="s-tools"><h2 class="sec-t">포인트 내역</h2><div class="lchips" role="group" aria-label="구분">{kchips}</div>
		<button type="button" class="ag-btn sm js-flash" data-msg="시안: 엑셀 파일을 내려받습니다">엑셀</button></div>
	<div class="grid-wrap"><table class="btable ltable"><thead><tr><th>일시</th><th>구분</th><th>업체</th><th>캠페인</th>
		<th class="ag-num">금액</th><th class="ag-num">사용 가능 잔액</th></tr></thead><tbody>{trs}</tbody></table></div>
	<p class="note">지급은 캠페인 예치금에서 빠지므로 사용 가능 잔액이 바뀌지 않습니다. 지급 차감 = 지급액 + 플랫폼 수수료 {int(D.FEE * 100)}%(5,000 → 5,500).</p>'''


# ════════════════ 리뷰어 지급: 묶음 ════════════════
PST = {"wait": ("st-gray", "지급 대기"), "ok": ("st-purple", "확정"), "send": ("st-blue", "송금 중"),
       "done": ("st-green", "입금 완료"), "fail": ("st-red", "실패"), "noacc": ("st-orange", "계좌 확인 대기")}


def pay_lines():
    """지금 지급 대기 줄(캠페인 지급 탭의 '지급 대기'·'계좌 미등록'과 같은 사람)"""
    out = []
    for c in D.CAMPS:
        for p in c["pays"]:
            if p["st"] in ("wait", "noacc"):
                out.append({"nick": p["nick"], "c": c, "amt": p["amt"], "acc": p["st"] != "noacc", "st": p["st"]})
    return out


def past_batches():
    """지난 묶음 — 송금 중 1 · 입금 완료 2(실패 1줄 섞임)"""
    r = random.Random("batches")
    done = [c for c in D.CAMPS if c["group"] == "end" and c["pays"]]
    out = []
    for no, (off, st) in enumerate([(-1, "send"), (-6, "done"), (-13, "done")]):
        lines = []
        for c in r.sample(done, min(4, len(done))):
            for p in c["pays"][:r.randint(1, 3)]:
                lines.append({"nick": p["nick"], "c": c, "amt": p["amt"], "acc": True, "st": st,
                              "day": P.md(off + 1) if st == "done" else ""})
        if no == 1:
            lines[-1]["st"], lines[-1]["why"] = "fail", "예금주 불일치 — 리뷰어에게 계좌 다시 등록 알림 보냄"
        out.append((f"11-{9 + off:02d}" if off > -9 else f"10-{31 + off + 9:02d}", off, st, lines))
    return out


def batch_rows(lines, ck=False):
    trs = []
    for x in lines:
        c = x["c"]
        cls, lab = PST[x["st"]]
        acc = ('<span class="okc">확인됨</span>' if x["acc"] else '<span class="bad">미등록</span>')
        extra = (f'<small class="muted"> · 입금 {x["day"]}</small>' if x.get("day") else "") + \
                (f'<br><small class="bad">{x["why"]}</small>' if x.get("why") else "")
        trs.append(f'<tr class="prow{"" if x["acc"] else " no-acc"}">'
                   + (f'<td class="ck"><input type="checkbox" class="js-pck" aria-label="{x["nick"]} 포함"{" checked" if x["acc"] else " disabled"}></td>' if ck else "")
                   + f'<td><b>{x["nick"]}</b></td><td><a href="campaigns.html#c-{c["id"]}-rev">{esc(c["name"])}</a></td>'
                   f'<td>{esc(c["b"]["name"])}</td><td>{OWNER[c["bid"]]}</td><td class="ag-num">{won(x["amt"])}</td>'
                   f'<td>{acc}</td><td class="js-pst"><span class="st {cls}">{lab}</span>{extra}</td></tr>')
    return "".join(trs)


def batch_card(title, sub, st, lines, open_=False, ck=False, foot=""):
    amt = sum(x["amt"] for x in lines)
    cls, lab = PST[st]
    head = ("<th class=ck></th>" if ck else "") + "<th>리뷰어</th><th>캠페인</th><th>업체</th><th>담당자</th><th class=num>금액</th><th>계좌</th><th>상태</th>"
    return (f'<details class="batch b-{st}"{" open" if open_ else ""}><summary><span class="st {cls} js-bst">{lab}</span><b>{title}</b>'
            f'<span class="muted">{sub}</span><span class="bsum">{len(lines)}명 · <b>{won(amt)}</b>'
            f'<small> · 차감 {won(int(amt * (1 + D.FEE)))}</small></span></summary>'
            f'<table class="mini ptable"><thead><tr>{head}</tr></thead><tbody>{batch_rows(lines, ck)}</tbody></table>{foot}</details>')


def tab_pay():
    now = pay_lines()
    ok_lines = [x for x in now if x["acc"]]
    no_lines = [x for x in now if not x["acc"]]
    past = past_batches()
    month_done = sum(x["amt"] for _t, _o, st, ls in past if st == "done" for x in ls if x["st"] == "done")
    foot = (f'<div class="bfoot"><p class="muted small">계좌 미확인 줄은 확정할 때 자동으로 빠져 "계좌 확인 대기" 묶음으로 갑니다.</p>'
            f'<button type="button" class="ag-btn primary w-admin js-bconfirm">묶음 확정 {len(ok_lines)}명 · {won(sum(x["amt"] for x in ok_lines))}</button>'
            f'<span class="w-view muted small">팀장·담당자는 확정할 수 없습니다 — 캠페인 지급 탭에서 [지급 요청]</span></div>')
    cards = (batch_card("11월 10일 묶음", "지금 지급 대기 — 대시보드 \"지급\" 이슈와 같은 줄", "wait", now, True, True, foot)
             + (batch_card("계좌 확인 대기", "리뷰어가 계좌를 등록하면 다음 묶음에 들어감", "noacc", no_lines) if no_lines else "")
             + "".join(batch_card(f"{t.replace('-', '월 ')}일 묶음", "송금 중 — 뷰마가 보내는 중" if st == "send" else "입금 완료",
                                  st, ls) for t, _o, st, ls in past))
    flow = "".join(f'<li><span class="st {PST[k][0]}">{PST[k][1]}</span></li>' for k in ("wait", "ok", "send", "done"))
    return f'''<div class="kpis">
		<div class="kpi main"><p>지급 대기 합계</p><b>{won(sum(x["amt"] for x in now))}</b><small>{len(now)}명 · 이 중 계좌 미확인 {len(no_lines)}명</small></div>
		<div class="kpi"><p>이번 달 입금 완료</p><b>{won(month_done)}</b><small>11월 · 리뷰어 계좌로 들어간 돈</small></div>
		<div class="kpi"><p>송금 중</p><b>{won(sum(x["amt"] for _t, _o, st, ls in past if st == "send" for x in ls))}</b><small>확정 후 뷰마가 보내는 중</small></div>
	</div>
	<div class="flowline"><b>지급 상태</b><ol class="pflow">{flow}</ol><span class="muted small">/ <span class="st st-red">실패</span>(사유 표시 · 리뷰어에게 계좌 재등록 알림)</span></div>
	<div class="batches">{cards}</div>
	<p class="note">대시보드 "지급" 이슈의 [지급 확정] = 여기 묶음 확정과 같은 동작(관리자). 지급대행 수수료(Q2)는 1차 없음.</p>'''


# ════════════════ 업체별 사용내역 ════════════════
PERIODS = [("m0", "이번 달(11월)"), ("m1", "지난달(10월)"), ("m3", "최근 3개월")]


def usage_rows(pid):
    r = random.Random(f"use-{pid}")
    scale = {"m0": 1, "m1": 1.3, "m3": 3.6}[pid]
    rows = []
    for b in P.BIZS:
        cs = [c for c in D.CAMPS if c["bid"] == b["id"] and c["group"] != "draft"]
        n = len(cs) if pid != "m1" else max(0, len(cs) - r.randint(0, 2))
        used = int(sum(c["deposit"] for c in cs) * scale * r.uniform(.25, .6)) // 100 * 100 if n else 0
        pays = sum(len(c["pays"]) for c in cs) if pid != "m1" else r.randint(0, 6)
        rows.append((b, n, pays, used))
    rows.sort(key=lambda x: -x[3])
    return rows


def tab_use():
    radios = "".join(f'<input type="radio" name="up" id="up-{k}" class="vr"{" checked" if k == "m0" else ""}>' for k, _l in PERIODS)
    chips = "".join(f'<label for="up-{k}" class="pill">{lab}</label>' for k, lab in PERIODS)
    bodies = []
    for k, _l in PERIODS:
        rows = usage_rows(k)
        tr = "".join(f'<tr><th scope="row"><a href="biz.html#biz={b["id"]}">{esc(b["name"])}</a></th><td>{OWNER[b["id"]]}</td>'
                     f'<td class="ag-num">{n}</td><td class="ag-num">{pays}</td><td class="ag-num"><b>{won(u)}</b></td></tr>' for b, n, pays, u in rows)
        tot = sum(u for *_x, u in rows)
        bodies.append(f'<tbody class="ub ub-{k}">{tr}<tr class="sumr"><th>합계</th><td></td>'
                      f'<td class="ag-num">{sum(n for _b, n, _p, _u in rows)}</td><td class="ag-num">{sum(p for _b, _n, p, _u in rows)}</td>'
                      f'<td class="ag-num"><b>{won(tot)}</b></td></tr></tbody>')
    return f'''{radios}<div class="s-tools"><div class="ups" role="group" aria-label="기간">{chips}</div>
		<button type="button" class="ag-btn sm js-flash" data-msg="시안: 업체별 사용내역 엑셀을 내려받습니다">엑셀</button></div>
	<div class="grid-wrap"><table class="btable utable"><thead><tr><th>업체</th><th>담당자</th><th class="ag-num">캠페인 수</th>
		<th class="ag-num">지급 건수</th><th class="ag-num">사용액(지급 + 수수료)</th></tr></thead>{"".join(bodies)}</table></div>
	<p class="note">세금계산서는 대행사 명의 1장(Q7 안) — 업체별로 나눠 청구할 때는 이 엑셀을 씁니다. 보고서(업체 고객용)에는 금액이 나오지 않습니다.</p>'''


def charge_pop():
    opts = "".join(f'<label class="tagr"><input type="radio" name="chg"{" checked" if v == 1000000 else ""}><span>{v:,}P</span></label>'
                   for v in (500000, 1000000, 3000000, 5000000))
    return f'''<div id="pop-charge" popover class="pop" aria-labelledby="pop-charge-t">
	<header><h2 id="pop-charge-t">포인트 충전</h2><button type="button" class="t-x dark" popovertarget="pop-charge" popovertargetaction="hide" aria-label="닫기">✕</button></header>
	<div class="pop-b"><p class="muted small">기존 광고주 사이트 충전과 같은 결제창을 씁니다(시안은 화면만 — 결제 없음).</p>
		<div class="tagrs">{opts}</div>
		<dl class="kv2"><dt>지금 잔액</dt><dd>{won(D.BALANCE)}</dd><dt>결제 수단</dt><dd>카드 · 계좌이체 · 무통장(기존)</dd></dl></div>
	<footer><button type="button" class="ag-btn" popovertarget="pop-charge" popovertargetaction="hide">취소</button>
		<button type="button" class="ag-btn primary js-flash" data-msg="시안: 결제창으로 이동합니다">결제하기</button></footer>
</div>'''


def settle_page():
    tabs = [("w", "포인트"), ("p", "리뷰어 지급"), ("u", "업체별 사용내역")]
    radios = "".join(f'<input type="radio" name="st" id="st-{k}" class="vr"{" checked" if k == "w" else ""}>' for k, _l in tabs)
    bar = "".join(f'<label for="st-{k}" class="stab stab-{k}">{lab}</label>' for k, lab in tabs)
    body = f'''<section class="board settle" aria-labelledby="t-settle">
	<input type="radio" name="role" id="role-admin" class="vr" checked><input type="radio" name="role" id="role-view" class="vr">
	{radios}
	<div class="board-h"><div><h1 id="t-settle">정산</h1>
		<p class="sub">관리자 = 쓰기(충전 · 지급 확정) · 팀장/조회 = 열람만 · 포인트 1개를 모든 업체가 함께 씁니다</p></div>
		<div class="seg sm role-seg" role="group" aria-label="보는 사람(시안)"><label for="role-admin">대표(관리자)로 보기</label><label for="role-view">김지은(팀장 · 열람)으로 보기</label></div></div>
	<nav class="stabs" aria-label="정산 탭">{bar}</nav>
	<div class="spane sp-w">{tab_wallet()}</div>
	<div class="spane sp-p">{tab_pay()}</div>
	<div class="spane sp-u">{tab_use()}</div>
</section>{charge_pop()}'''
    return P.page("정산", "pay", body, None, '<link rel="stylesheet" href="css/ag/settle.css">', "settle.js")


if __name__ == "__main__":
    # [2026-11-10 v0.8] 정산 화면은 나뉨 — 포인트(point.html · gen_account) / 지급 묶음(payout.html · gen_ops).
    #   이 파일은 그 두 화면이 가져다 쓰는 함수 모음으로만 남는다(settle.html 은 더 만들지 않음)
    print("v0.8: settle.html 은 만들지 않습니다 — gen_account.py · gen_ops.py 를 돌리세요")
