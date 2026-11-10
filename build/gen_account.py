# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 계정 층 6화면 — 광고주 계정 화면(조사/광고주_계정화면_스펙_20261110.md)을 "대행사 하나" 단위로 옮김
  point.html 통포인트(pay) · plan.html 사용료(plan) · sms.html 문자설정(sms)
  penalty.html 패널티(pen) · info.html 대행사 정보(info) · help.html 고객센터(help)
  지갑·등급·문자·패널티 = 대행사 하나(업체마다 아님). 탭·문구·칸 순서 = 광고주 화면 그대로.
  탭 = 라디오 + CSS(ops.css .ot), 창 = popover, 거르기 칩·증빙 칸 열기·기간별 금액 = :has()(css/account.css).
  JS 는 공통 ops.js 만(안내 글자 · 모두 고르기).
  광고주 화면에 없는 대행사 추가분 = class="add"(점선) · K.add_tag()
  실행: python -I build/gen_account.py
"""
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402

P, G = D.P, D.G


# [2026-11-10 v0.8] 정산(gen_settle.py)의 ledger() · usage_rows() 와 같은 계산·같은 시드
#   gen_settle 을 import 하지 않고 옮겨 둠 — 그 파일이 깨지거나 바뀌어도 이 화면 생성이 멈추지 않게
class S:
    PERIODS = [("m0", "이번 달(11월)"), ("m1", "지난달(10월)"), ("m3", "최근 3개월")]
    OWNER = {b["id"]: (b["owner"][1] if b["owner"] else "미담당") for b in P.BIZS}

    @staticmethod
    def ledger():
        """포인트 내역 — 새 것부터 (off, hm, kind, b, c, amt, bal)"""
        r = random.Random("ledger")
        ev = []
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
                back = c["deposit"] - sum(int(p["amt"] * (1 + D.FEE)) for p in c["pays"] if p["st"] == "done")
                if back > 0:
                    ev.append((c["dts"]["rev"] + 3, "18:00", "back", b, c, back, True))
        for off in (-38, -24, -12, -3):
            ev.append((off, "10:05", "charge", None, None, r.choice([1000000, 2000000, 3000000]), True))
        ev = sorted((e for e in ev if e[0] <= 0), key=lambda e: (e[0], e[1]), reverse=True)
        bal, rows = D.BALANCE, []
        for off, hm, kind, b, c, amt, moves in ev[:60]:
            rows.append((off, hm, kind, b, c, amt, bal if moves else None))
            bal -= amt if moves else 0
        return rows

    @staticmethod
    def usage_rows(pid):
        """업체별 사용내역 (업체, 캠페인 수, 지급 건수, 사용액)"""
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
esc = K.esc
won = K.won
AGENCY = "애니라인 마케팅"
REG_ACC = ("신한은행", "110-***-**1234", "(주)애니라인마케팅")      # 더미 · 가림 표시
EXTRA = K.CSS + '<link rel="stylesheet" href="css/account.css">'


# ════════════════ 공통 ════════════════
def write(fname, title, active, body):
    """K.write 와 같되 css/account.css 를 더 붙인다"""
    out = P.page(title, active, f'<section class="ops acc">{body}</section>', None, EXTRA, "ops.js")
    (K.ROOT / fname).write_text(out, encoding="utf-8")
    print(f"written {fname} ({len(out.encode('utf-8')) / 1024:.0f} KB)")


def dt(off, hm="10:00"):
    return f"{P.d_of(off):%Y-%m-%d} {hm}"


def ymd(d):
    return f"{d:%Y.%m.%d}"


def addbox(inner, tag="대행사"):
    """대행사 추가 안내 한 덩이(점선)"""
    return f'<div class="add addbox">{K.add_tag(tag)} {inner}</div>'


def addh(text):
    """표 머리 — 대행사 추가 칸"""
    return f"{text}{K.add_tag()}"


def radios(name, items, checked=0):
    """items = [(value, 라벨)] → .radios 묶음"""
    return '<div class="radios">' + "".join(
        f'<label><input type="radio" name="{name}" value="{v}"{" checked" if i == checked else ""}> {lab}</label>'
        for i, (v, lab) in enumerate(items)) + "</div>"


def kv(pairs, cls="kv"):
    return f'<dl class="{cls}">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in pairs) + "</dl>"


def info_box(title, lines):
    return f'<div class="infobox"><b>{title}</b><ul>{"".join(f"<li>{x}</li>" for x in lines)}</ul></div>'


def file_in(label):
    return f'<label class="fl">{label}<input type="file"></label>'


# ════════════════ 1. 통포인트(point.html) ════════════════
LEDGER = S.ledger()          # (off, hm, kind, b, c, amt, bal) — 정산 화면과 같은 줄
PRESETS = [10000, 50000, 100000, 300000, 500000]
CHARGE_ST = {"결제대기": "st-gray", "입금대기(가상계좌)": "st-orange", "입금대기": "st-orange", "확인중": "st-blue",
             "완료": "st-green", "거절": "st-red", "취소": "st-gray"}


def held_list():
    """진행 캠페인마다 (캠페인, 지급됨, 남은 예치) — 정산 tab_wallet 과 같은 계산"""
    out = []
    for c in D.CAMPS:
        if c["group"] not in D.ACTIVE:
            continue
        paid = sum(int(p["amt"] * (1 + D.FEE)) for p in c["pays"] if p["st"] == "done")
        out.append((c, paid, c["deposit"] - paid))
    return out


HELD = sum(left for _c, _p, left in held_list())
CHARGES = [(off, hm, amt) for off, hm, kind, _b, _c, amt, _bal in LEDGER if kind == "charge"]


def point_kpis():
    return (f'<div class="kpis"><div class="kpi main"><p>사용 가능</p><b>{won(D.BALANCE)}</b><small>새 캠페인·추가모집·문자에 쓸 수 있음</small></div>'
            f'<div class="kpi add"><p>예치 중{K.add_tag()}</p><b>{won(HELD)}</b><small>진행 캠페인 {len(held_list())}개에 묶여 있음</small></div>'
            f'<div class="kpi"><p>통포인트 합계</p><b>{won(D.BALANCE + HELD)}</b><small>사용 가능 + 예치 중</small></div>'
            '<div class="kpi kact"><label for="pt-0" class="btn primary">포인트 충전</label>'
            '<small>지갑 1개를 모든 업체가 함께 씁니다</small></div></div>')


def breakdown(v):
    return (f'<dl class="bd bd-{v}"><dt>적립 포인트</dt><dd>{v:,}P</dd><dt>공급가액</dt><dd>{v:,}원</dd>'
            f'<dt>부가세</dt><dd>{v // 10:,}원</dd><dt>결제 금액</dt><dd><b>{v * 11 // 10:,}원</b></dd></dl>')


def receipt_fields():
    tax = ('<div class="rc rc-tax">'
           '<label class="fl">사업자등록번호<input type="text" value="123-45-*****"></label>'
           f'<label class="fl">상호<input type="text" value="{AGENCY}"></label>'
           '<label class="fl">대표자<input type="text" value="이정민"></label>'
           '<label class="fl">이메일<input type="email" value="tax@anyline.kr"></label></div>')
    cash = '<div class="rc rc-cash"><label class="fl">휴대폰<input type="tel" value="010-****-1234"></label></div>'
    return tax + cash


def tab_charge():
    pre = "".join(f'<label class="pre"><input type="radio" name="amt" value="{v}"{" checked" if v == 100000 else ""}>+ {v // 10000}만</label>'
                  for v in PRESETS)
    return (addbox("관리자만 충전 · 담당자는 충전 요청 "
                   + K.btn("관리자에게 충전 요청", "시안: 관리자에게 충전 요청을 보냈습니다"))
            + '<div class="charge form-c">'
            f'<div class="fl">충전 금액<div class="pres">{pre}{K.btn("초기화", "시안: 금액을 지웠습니다")}</div>'
            '<div class="amt-in"><input type="text" inputmode="numeric" placeholder="충전할 포인트를 입력해주세요" aria-label="충전 포인트"> P</div>'
            '<small>* 최소 충전 포인트는 10,000P입니다.</small>'
            f'<small class="add">시안: 금액 버튼을 고르면 아래 계산이 바뀝니다(실제는 버튼마다 더하기){K.add_tag("시안")}</small></div>'
            + "".join(breakdown(v) for v in PRESETS)
            + f'<div class="fl">결제 방법{radios("pay", [("card", "신용카드"), ("vbank", "가상계좌")])}</div>'
            f'<div class="fl">증빙 신청{radios("rcpt", [("none", "신청 안 함"), ("tax", "세금계산서"), ("cash", "현금영수증")])}</div>'
            + receipt_fields()
            + '<div class="terms"><label><input type="checkbox"> 포인트 충전 약관에 동의합니다</label>'
            + K.btn("약관보기", pop="pop-terms", cls="btn sm ghost") + "</div>"
            + K.btn("포인트 충전 신청하기", "시안: 결제창으로 이동합니다", "btn primary wide")
            + "</div>")


def tab_req():
    r = random.Random("acc-req")
    rows = [(dt(0, "09:40"), "가상계좌", 2000000, "세금계산서", "입금대기(가상계좌)", "김지은(팀장) 요청 → 대표"),
            (dt(-1, "16:22"), "신용카드", 500000, "신청 안 함", "취소", "대표")]
    rows += [(dt(off, hm), r.choice(["신용카드", "가상계좌"]), amt, "세금계산서", "완료", "대표") for off, hm, amt in CHARGES]
    trs = [("", [d, m, won(a), e, K.badge(CHARGE_ST[s], s), who]) for d, m, a, e, s, who in rows]
    heads = [("신청일시", ""), ("결제수단", ""), ("금액", "num"), ("증빙", ""), ("상태", ""), (addh("신청·요청자"), "add-c")]
    guide = info_box("상태 안내", ["결제대기 — 결제창에서 결제를 마치지 않았습니다", "입금대기(가상계좌) — 안내된 가상계좌로 입금하면 자동 충전됩니다",
                                 "입금대기 · 확인중 — 입금을 확인하고 있습니다", "완료 — 포인트가 적립되었습니다",
                                 "거절 · 취소 — 포인트가 적립되지 않습니다"])
    return K.table(heads, trs) + guide


def tab_refund():
    bank, acc, holder = REG_ACC
    other = ('<div class="rc rc-other"><label class="fl">은행<select><option>은행 선택</option><option>국민</option><option>신한</option>'
             '<option>우리</option><option>하나</option></select></label><label class="fl">계좌번호<input type="text" placeholder="- 없이 숫자만"></label>'
             '<label class="fl">예금주<input type="text"></label></div>')
    return ('<div class="form-c refund">'
            '<p class="okline"><span class="st st-green">본인확인 완료</span> 대표 이정민 · 2026-10-02 — 본인확인 후 환불을 신청할 수 있습니다</p>'
            f'<p class="big">환불 가능 포인트 <b>{won(D.BALANCE)}</b> <span class="muted">(보유 {won(D.BALANCE + HELD)})</span></p>'
            + addbox(f"예치 중 {won(HELD)}는 환불할 수 없습니다 — 캠페인이 끝나면 남은 예치가 사용 가능으로 돌아온 뒤 환불할 수 있습니다.")
            + f'<div class="fl">환불 포인트<div class="amt-in"><input type="text" inputmode="numeric" aria-label="환불 포인트"> P '
            f'{K.btn("전액", "시안: 환불 가능 포인트 전액을 넣었습니다")}</div></div>'
            f'<div class="fl">환불 받을 계좌{radios("rfa", [("reg", f"등록 계좌 · {bank} {acc} · {holder}"), ("other", "다른 계좌")])}</div>'
            + other
            + '<label class="fl">환불 요청 사유 *<textarea placeholder="환불 사유를 입력해 주세요"></textarea></label>'
            + K.btn("포인트 환불 신청하기", "시안: 환불 신청을 접수했습니다", "btn primary wide") + "</div>")


REFUNDS = [(-2, "14:10", 300000, "승인대기", "", ""), (-19, "11:02", 500000, "승인완료", dt(-17, "15:00"), "확인 후 환불 처리"),
           (-33, "10:30", 200000, "거절", dt(-32, "09:20"), "사업자 명의 계좌가 아님 — 계좌 변경 후 다시 신청")]
REFUND_ST = {"승인대기": "st-gray", "승인완료": "st-green", "거절": "st-red"}


def tab_refund_list():
    bank, acc, holder = REG_ACC
    trs, pops = [], []
    for i, (off, hm, amt, st, done, memo) in enumerate(REFUNDS):
        trs.append(("", [dt(off, hm), won(amt), f"{bank} {acc}", K.badge(REFUND_ST[st], st),
                         K.btn("상세내용보기", pop=f"pop-rf{i}")]))
        body = kv([("신청일시", dt(off, hm)), ("처리상태", st), ("환불 금액", won(amt)), ("환불 계좌", f"{bank} {acc}"),
                   ("예금주", holder), ("요청 사유", "남은 포인트 정리"), ("처리일시", done or "—"), ("관리자 메모", memo or "—")])
        pops.append(K.pop(f"pop-rf{i}", "환불 신청 상세", body, "확인", "시안: 닫습니다"))
    heads = [("신청일시", ""), ("금액", "num"), ("환불계좌", ""), ("상태", ""), ("", "")]
    return K.table(heads, trs) + "".join(pops)


L_KIND = {"charge": ("충전", "k-charge"), "dep": ("캠페인 예치", "k-camp"), "pay": ("리뷰 지급", "k-camp"),
          "back": ("잔액 환불", "k-camp k-refund"), "sms": ("서비스 이용", "k-sms"), "talk": ("서비스 이용", "k-talk")}


def ledger_rows():
    """정산 ledger() + 문자·알림톡 사용(서비스 이용) 몇 줄 — 새 것부터"""
    r = random.Random("acc-ledger")
    rows = [(off, hm, kind, b, c, amt) for off, hm, kind, b, c, amt, _bal in LEDGER]
    for _i in range(8):
        kind = r.choice(["sms", "talk"])
        c = r.choice([x for x in D.CAMPS if x["group"] in D.ACTIVE])
        n = r.randint(3, 25)
        rows.append((-r.randint(0, 30), f"{r.randint(9, 18):02d}:{r.randint(0, 59):02d}", kind, c["b"], c, -n * (20 if kind == "sms" else 15)))
    rows.sort(key=lambda e: (e[0], e[1]), reverse=True)
    return rows


def ledger_text(kind, c, amt):
    if kind == "charge":
        return "포인트 충전"
    if kind == "dep":
        return "캠페인 시작 — 예치"
    if kind == "pay":
        return f"리뷰어 지급(지급액 + 수수료 {int(D.FEE * 100)}%)"
    if kind == "back":
        return "캠페인 종료 — 남은 예치 환불"
    return f'{"문자" if kind == "sms" else "알림톡"} 발송 {-amt // (20 if kind == "sms" else 15)}건'


def tab_ledger():
    chips = [("all", "전체"), ("sms", "문자"), ("talk", "알림톡"), ("camp", "캠페인"), ("charge", "충전"), ("refund", "환불")]
    ins = "".join(f'<input type="radio" name="pf" id="pf-{v}" value="{v}" class="hr"{" checked" if v == "all" else ""}>' for v, _l in chips)
    labs = "".join(f'<label for="pf-{v}" class="fchip">{lab}</label>' for v, lab in chips)
    trs = []
    for off, hm, kind, b, c, amt in ledger_rows():
        lab, cls = L_KIND[kind]
        camp = f'{esc(c["name"])} <small class="rnd">{c["round"]}회차</small>' if c else "—"
        trs.append((f'class="{cls}"', [dt(off, hm), lab, ledger_text(kind, c, amt), esc(b["name"]) if b else "—", camp,
                                       f'<b class="{"plus" if amt > 0 else ""}">{"+" if amt > 0 else ""}{amt:,}P</b>',
                                       K.badge("st-green", "완료"), K.btn("상세보기", "시안: 상세 창")]))
    heads = [("일시", ""), ("구분", ""), ("내역", ""), (addh("업체"), "add-c"), (addh("캠페인"), "add-c"),
             ("금액", "num"), ("상태", ""), ("", "")]
    return (f'<div class="pf">{ins}<div class="fchips" role="group" aria-label="구분">{labs}</div>'
            + K.table(heads, trs) + '<p class="help">최근 100건까지 보입니다. 구분: 충전 · 캠페인 예치 · 보증금 환불 · 리뷰 지급 · 잔액 환불 · '
            '조정 · 서비스 이용 · 서비스 환불 · 소멸</p></div>')


def tab_trade():
    rows = [("", [dt(off, hm), "결제", "포인트 충전 · 신용카드", f"{amt * 11 // 10:,}", f"+{amt:,}P", K.btn("영수증", "시안: 영수증 창")])
            for off, hm, amt in CHARGES]
    off, hm, amt = REFUNDS[1][:3]
    rows.append(("", [dt(off, hm), "환불", "포인트 환불 · 승인완료", f"−{amt:,}", f"−{amt:,}P", "—"]))
    rows.sort(key=lambda x: x[1][0], reverse=True)
    paid = sum(a * 11 // 10 for _o, _h, a in CHARGES)
    heads = [("일시", ""), ("구분", ""), ("내용", ""), ("금액(원)", "num"), ("포인트", "num"), ("영수증", "")]
    return (K.fbar("조회 기간", K.dates(), K.btn("조회", "시안: 조회했습니다"), K.btn("🖨 거래내역서 인쇄", "시안: 인쇄 창"),
                   count=f"실제 결제 <b>{paid - amt:,}원</b> (환불 −{amt:,}원 차감)")
            + K.table(heads, rows)
            + info_box("증빙 안내", ["신용카드 결제는 카드 영수증이 증빙이 됩니다.",
                                   "세금계산서·현금영수증은 충전할 때 [증빙 신청]에서 고릅니다.",
                                   "세금계산서는 대행사 명의 1장으로 발행됩니다(업체별로 나누지 않음)."]))


def tab_held():
    heads = [("업체", ""), ("캠페인", ""), ("상태", ""), ("예치", "num"), ("지급됨", "num"), ("남은 예치", "num")]
    rows = [("", [K.biz_cell(c["b"]), f'{esc(c["name"])} <small class="rnd">{c["round"]}회차</small>',
                  K.badge(D.STATE_CLS[c["state"]], c["state"]), won(c["deposit"]), won(paid), f"<b>{won(left)}</b>"])
            for c, paid, left in sorted(held_list(), key=lambda x: -x[2])]
    rows.append(('class="sumr"', ["<b>합계</b>", "", "", won(sum(c["deposit"] for c, _p, _l in held_list())),
                                  won(sum(p for _c, p, _l in held_list())), f"<b>{won(HELD)}</b>"]))
    return ('<div class="add">' + K.table(heads, rows)
            + f'<p class="help">캠페인 시작 = 사용 가능 → 예치, 리뷰 지급 = 예치에서 차감(지급액 + 수수료 {int(D.FEE * 100)}%), '
            '완료·중단 = 남은 예치 → 사용 가능.</p></div>')


def tab_use():
    items = []
    for k, lab in S.PERIODS:
        rows = S.usage_rows(k)
        trs = [("", [K.biz_cell(b), S.OWNER[b["id"]], n, pays, f"<b>{won(u)}</b>"]) for b, n, pays, u in rows]
        trs.append(('class="sumr"', ["<b>합계</b>", "", sum(x[1] for x in rows), sum(x[2] for x in rows),
                                     f'<b>{won(sum(x[3] for x in rows))}</b>']))
        heads = [("업체", ""), ("담당자", ""), ("캠페인 수", "num"), ("지급 건수", "num"), ("사용액(지급 + 수수료)", "num")]
        items.append((lab, K.table(heads, trs)))
    return ('<div class="add">' + K.tabs("up", items)
            + '<p class="help">업체별로 나눠 청구할 때 쓰는 표입니다. 보고서(업체 고객용)에는 금액이 나오지 않습니다. '
            + K.btn("엑셀", "시안: 업체별 사용내역 엑셀을 내려받습니다") + "</p></div>")


def point_page():
    terms = K.pop("pop-terms", "포인트 충전 약관",
                  "<ol class='terms-t'><li>충전한 포인트는 뷰마 서비스(캠페인 예치·리뷰어 지급·문자 발송·등급 이용) 안에서만 씁니다.</li>"
                  "<li>환불은 본인확인 후 사업자 명의 계좌로만 가능합니다.</li><li>예치 중인 포인트는 캠페인이 끝난 뒤 환불할 수 있습니다.</li>"
                  "<li>마지막 사용일로부터 5년이 지난 포인트는 소멸됩니다.</li></ol><p class='help'>시안 — 약관 원문은 운영 사이트 문구를 씁니다.</p>",
                  "동의", "시안: 약관에 동의했습니다")
    tabs = [("포인트 충전", tab_charge()), ("충전 신청 내역", tab_req()), ("포인트 환불", tab_refund()),
            ("환불 신청 내역", tab_refund_list()), ("포인트 내역", tab_ledger()), ("결제·거래내역", tab_trade()),
            (f"예치 중{K.add_tag()}", tab_held()), (f"업체별 사용내역{K.add_tag()}", tab_use())]
    body = (K.head("통포인트", f"보유 포인트 {won(D.BALANCE)}(사용 가능) · 광고주 \"포인트 관리\"와 같은 탭 — 지갑은 대행사 하나")
            + point_kpis() + K.tabs("pt", tabs) + terms)
    write("point.html", "통포인트", "pay", body)


# ════════════════ 2. 사용료(plan.html) ════════════════
FEATS = [("campaignLoad", "이전 캠페인 불러오기"), ("keywordSuggest", "연관키워드 검색"), ("directSend", "문자·메일 직접 발송"),
         ("photoManage", "리뷰 사진 관리·내려받기"), ("searchReport", "검색결과 리포트"), ("autoSend", "자동발송 설정"),
         ("resultExcel", "캠페인 결과 엑셀 다운"), ("videoRequest", "영상 제작 요청"), ("rerecruitRequest", "추가모집 요청"),
         ("sendNumber", "발신번호 관리")]
LIMITS = ["캠페인당 모집인원(명)", "한 달 등록 캠페인 수(개)", "동시 진행 캠페인 수(개)"]
ADD_LIMITS = ["관리 업체 수(곳)", "직원 수(명)"]
# (키, 이름, 월 요금, 한도 3 + 대행사 한도 2(0 = 무제한), 기능 코드) — 이름·금액은 예시(Q3)
GRADES = [("free", "무료 이용", 0, (10, 3, 3, 5, 2), ["campaignLoad", "keywordSuggest"]),
          ("std", "스탠다드", 99000, (30, 20, 10, 20, 5), ["campaignLoad", "keywordSuggest", "autoSend", "sendNumber", "resultExcel"]),
          ("dlx", "디럭스", 199000, (50, 50, 30, 50, 15), ["campaignLoad", "keywordSuggest", "autoSend", "sendNumber", "resultExcel",
                                                          "directSend", "photoManage", "rerecruitRequest"]),
          ("pre", "프리미엄", 349000, (0, 0, 0, 0, 0), [f for f, _l in FEATS])]
MONTHS = [(1, 0), (3, 5), (6, 10), (12, 15)]      # (개월, 할인 %) — 예시
PLAN_END = P.d_of(142)                            # 사이드바 "무료 이용 중 · D-142"


def add_months(d, m):
    y, mo = divmod(d.month - 1 + m, 12)
    return date(d.year + y, mo + 1, min(d.day, 28))


def lim(v):
    return "무제한" if v == 0 else f"{v:,}"


def price_lines(monthly):
    out = []
    for m, dc in MONTHS:
        total = monthly * m * (100 - dc) // 100 // 100 * 100
        out.append(f'<div class="pr pr-{m}"><p class="per">사용기간 {ymd(P.d_of(0))} ~ {ymd(add_months(P.d_of(0), m))}</p>'
                   f'<p class="amt"><b>{total:,} 원</b> (VAT 포함)</p><p class="muted">월 {total // m:,}원'
                   f'{f" · {dc}% 할인" if dc else ""}</p></div>')
    return "".join(out)


def grade_card(key, name, monthly, lims, feats):
    cur = key == "free"
    ls = "".join(f"<li>{LIMITS[i]} <b>{lim(lims[i])}</b></li>" for i in range(3))
    ls += "".join(f'<li class="add">{ADD_LIMITS[i]} <b>{lim(lims[3 + i])}</b>{K.add_tag()}</li>' for i in range(2))
    names = [lab for code, lab in FEATS if code in feats]
    fs = "".join(f"<li>✓ {x}</li>" for x in names[:3]) + (f'<li class="muted">그 외 {len(names) - 3}개</li>' if len(names) > 3 else "")
    foot = ('<p class="muted">가입 혜택 · 결제 없음</p>' if cur else price_lines(monthly)
            + K.btn("이 등급으로 결제", f"시안: {name} 결제창(카드)으로 이동합니다", "btn primary wide"))
    return (f'<div class="gcard g-{key}{" cur" if cur else ""}"><h3>{name}{K.badge("st-green", "이용중") if cur else ""}</h3>'
            f'<ul class="glim">{ls}</ul><ul class="gfeat">{fs or "<li class=muted>등급 기능 없음</li>"}</ul>{foot}</div>')


def compare_table():
    th = "".join(f"<th>{g[1]}</th>" for g in GRADES)
    rows = [f'<tr><th scope="row">이용 요금(월)</th>{"".join(f"<td>{g[2]:,}원</td>" if g[2] else "<td>무료</td>" for g in GRADES)}</tr>']
    for i, lab in enumerate(LIMITS + ADD_LIMITS):
        cls = ' class="add-c"' if i >= 3 else ""
        rows.append(f'<tr{cls}><th scope="row">{lab}{K.add_tag() if i >= 3 else ""}</th>{"".join(f"<td>{lim(g[3][i])}</td>" for g in GRADES)}</tr>')
    for code, lab in FEATS:
        rows.append(f'<tr><th scope="row">{lab} <small>{code}</small></th>'
                    + "".join('<td class="y">✓</td>' if code in g[4] else '<td class="n">—</td>' for g in GRADES) + "</tr>")
    return (f'<h2 class="sec-t">등급별 한도 · 기능</h2><div class="owrap"><table class="otable perm cmp"><thead><tr><th>구분</th>{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
            '<p class="help">항상 열림: 결제(payment) · 고객센터(support) · 본인확인(identity). 한도 0 = 무제한.</p>')


def tab_buy():
    d_left = (PLAN_END - P.d_of(0)).days
    status = (f'<div class="kpis st2"><div class="kpi"><p>현재 등급</p><b>무료 이용</b><small>가입 혜택</small></div>'
              f'<div class="kpi"><p>이용 기간</p><b>{ymd(PLAN_END)} 까지</b><small>D-{d_left}{" · 만료 임박" if d_left <= 14 else ""}</small></div></div>')
    months = radios("pm", [(m, f"{m}개월") for m, _d in MONTHS])
    notes = info_box("유의사항", ["결제는 카드 결제만 가능합니다.", "결제가 완료되면 즉시 등급이 적용되고 이용 기간이 시작됩니다.",
                                "이용 중인 등급을 같은 등급으로 결제하면 이용 기간이 연장됩니다.",
                                "등급을 바꾸면 한도와 기능이 바로 바뀝니다(진행 중 캠페인은 그대로 진행).",
                                "환불·등급 변경은 1:1 문의로 요청해 주세요.", "이용 기간이 끝나면 무료 이용으로 돌아갑니다."])
    blocked = addbox('막힌 기능 화면 문구(광고주와 같음): "{기능}은/는 등급별 기능입니다" / "지금 등급에서는 사용할 수 없습니다. '
                     '이용을 원하시면 1:1 문의로 요청해 주세요." [1:1 문의하기]', "참고")
    return ('<div class="plan-buy">' + status
            + '<p class="eg-note">등급 이름·금액은 예시 — Q3 결정 대기</p>'
            + f'<h2 class="sec-t"><span class="stepn">1</span> 이용 기간 선택</h2>{months}'
            + '<h2 class="sec-t"><span class="stepn">2</span> 등급 선택 후 결제</h2>'
            + f'<div class="gcards">{"".join(grade_card(*g) for g in GRADES)}</div>'
            + notes + compare_table() + blocked + "</div>")


def tab_plan_hist():
    heads = [("번호", "num"), ("등급", ""), ("결제일시", ""), ("결제수단", ""), ("결제금액", "num"), ("이용기간", ""),
             ("만료일", ""), ("상태", ""), ("영수증", "")]
    rows = [("", ["2", "스탠다드", dt(-3, "11:20"), "신용카드", "99,000원", "1개월", "—", K.badge("st-red", "결제실패"), "—"]),
            ("", ["1", "무료 이용", dt(-40, "10:00"), "—", "0원", "6개월", ymd(PLAN_END), K.badge("st-green", "이용중"), "—"])]
    return (K.table(heads, rows)
            + '<p class="help">상태: 결제대기 · 이용중 · 결제실패 · 기간만료. 사용료는 대행사 하나에 매깁니다(업체마다 아님).</p>')


def plan_page():
    body = (K.head("대행사 사용료(등급)", "등급을 올리면 캠페인 한도와 기능이 함께 열립니다. 결제가 완료되면 즉시 적용됩니다.")
            + '<p class="help">광고주 "유료등급 이용권" 화면 — 대행사 하나 단위. 등급 카드 스킨(standard/deluxe/premium)은 모양일 뿐, 이름·기능은 DB 값.</p>'
            + K.tabs("pl", [("구매하기", tab_buy()), ("결제내역", tab_plan_hist())]))
    write("plan.html", "사용료", "plan", body)


# ════════════════ 3. 문자설정(sms.html) ════════════════
SMS_PRICE = [("문자", 20), ("장문", 50), ("알림톡", 15)]       # 예시 단가(P)
AUTO = [("선정 안내", "선정 확정 즉시 · 항상 발송 · 뷰마 부담", True),
        ("미선정 안내", "캠페인 시작일", False), ("방문 하루 전 안내", "방문 예정일 하루 전", False),
        ("리뷰 마감 임박 안내", "3일 전", False), ("리뷰 미등록 안내", "마감 다음날", False),
        ("리뷰 감사 인사", "검수 승인 즉시", False), ("영상 제작 완료", "제작 완료 즉시", False),
        ("리뷰등록 연장 신청", "리뷰어가 연장 신청하면", False), ("리뷰등록 연장 완료", "연장 승인 즉시", False)]


def tab_verify():
    return ('<div class="form-c">'
            '<p class="okline"><span class="st st-green">인증 완료</span> 자동문자 사후인증 — 대표 이정민 · 휴대폰 본인인증 · 2026-10-02</p>'
            '<p class="help">자동으로 나가는 문자는 보낸 뒤 본인인증 기록으로 발신자를 확인합니다. 인증한 사람이 바뀌면 다시 인증해 주세요.</p>'
            + K.btn("다시 인증하기", "시안: 휴대폰 본인인증 창") + "</div>"
            + addbox("인증은 대행사 하나에 1번 — 업체마다 하지 않습니다."))


def auto_row(i, sit, when, always):
    use = '<input type="checkbox" checked disabled aria-label="사용">' if always else \
        f'<input type="checkbox"{" checked" if i in (2, 3, 4, 5) else ""} aria-label="{sit} 사용">'
    ch = '<span class="muted">알림톡(뷰마 부담)</span>' if always else \
        '<select aria-label="보낼 방법"><option>문자</option><option selected>알림톡</option><option>메일(무료)</option></select>'
    text = f"[{{업체명}}] {sit} — {{리뷰어}}님, {{캠페인}} 관련 안내드립니다."
    return ("", [use, f"<b>{sit}</b><br><small>{when}</small>",
                 f'<div class="msgc"><p class="dflt"><small>기본 문구(운영자 지정)</small><br>{esc(text)}</p>{ch}</div>'])


def tab_auto():
    price = " · ".join(f"{n} {p}P" for n, p in SMS_PRICE) + " · 메일 무료"
    hours = "".join(f"<option{' selected' if h == 10 else ''}>{h}시</option>" for h in range(8, 21))
    rows = [auto_row(i, *a) for i, a in enumerate(AUTO)]
    return (f'<h2 class="sec-t">{AGENCY}님의 자동발송 설정</h2>'
            + kv([("단가", price), ("보유 포인트", won(D.BALANCE)),
                  ("발송 시각", f'<select aria-label="발송 시각">{hours}</select> <small class="muted">즉시 발송이 아닌 안내는 이 시각에 보냅니다</small>')], "kv row")
            + addbox("문구의 <code>{업체명}</code>은 캠페인 업체 이름으로 바뀝니다 — 리뷰어에게는 업체 이름으로 보입니다. "
                     "1차는 설정이 대행사 하나(Q15) · 업체마다 다른 문구는 2차.")
            + K.table([("사용", "ck"), ("상황", ""), ("보낼 문구", "")], rows)
            + K.btn("저장", "시안: 자동발송 설정을 저장했습니다", "btn primary"))


SENDERS = [(True, "대표번호", "이정민", "02-***-1234", "회사", -60, "등록완료"),
           (False, "1팀 김지은", "김지은", "010-****-5678", "본인", -21, "등록완료"),
           (False, "2팀 업무폰", "박서준", "010-****-9012", "타인", -2, "심사중"),
           (False, "옛 번호", "이정민", "031-***-3456", "본인", -90, "반려")]
SENDER_ST = {"등록완료": "st-green", "심사중": "st-blue", "심사대기": "st-gray", "본인확인": "st-orange", "반려": "st-red", "삭제됨": "st-gray"}


def tab_sender():
    trs = []
    for rep, nick, name, num, own, off, st in SENDERS:
        acts = (K.btn("재제출", "시안: 서류를 다시 제출합니다") if st == "반려" else "") + \
            K.btn("이름변경", "시안: 별명을 바꿉니다") + K.btn("삭제", "시안: 삭제했습니다")
        trs.append(("", [f'<input type="radio" name="rep" aria-label="대표"{" checked" if rep else ""}>', esc(nick), name, num, own,
                         f"{P.d_of(off):%Y-%m-%d}", K.badge(SENDER_ST[st], st), f'<div class="acts">{acts}</div>']))
    heads = [("대표", "ck"), ("발신번호명(별명)", ""), ("실명", ""), ("번호", ""), ("명의", ""), ("등록일", ""), ("상태", ""), ("관리", "")]
    return ('<p class="help">리뷰어에게 문자를 보낼 때 표시될 번호입니다. 등록·승인된 번호로만 보낼 수 있습니다.</p>'
            + K.fbar(f"등록된 번호 <b>{len(SENDERS)}</b>개", '<span class="sp"></span>', K.btn("발신번호 추가", pop="pop-sender", cls="btn sm primary"))
            + K.table(heads, trs)
            + addbox("발신번호는 대행사 하나에 등록 — 직원 누구나 등록된 번호로 보낼 수 있습니다(업체별 번호는 2차)."))


def sender_pop():
    owners = [("me-m", "본인 휴대폰인증"), ("me-t", "본인 일반전화"), ("ot-m", "타인 휴대전화"), ("ot-t", "타인 일반전화"), ("co", "회사 모든전화")]
    docs = "".join(file_in(d) for d in ["통신서비스 이용증명원", "위임장", "신분증 사본", "사업자등록증", "재직증명"])
    return (f'<div id="pop-sender" class="pop" popover><header><h2>발신번호 추가</h2>'
            '<button type="button" class="btn sm" popovertarget="pop-sender" popovertargetaction="hide">닫기</button></header>'
            f'<div class="pop-b"><div class="fl">명의{radios("own", owners)}</div>'
            '<label class="fl">발신번호<input type="tel" placeholder="- 없이 숫자만"></label>'
            '<label class="fl">별명<input type="text" placeholder="예: 대표번호"></label>'
            f'<div class="fl">서류 <small>명의에 따라 필요한 서류만 올립니다(본인 휴대폰인증은 서류 없음)</small>{docs}</div></div>'
            '<footer><button type="button" class="btn js-flash" data-msg="시안: 이전 단계">이전</button>'
            '<button type="button" class="btn" popovertarget="pop-sender" popovertargetaction="hide">취소</button>'
            f'{K.btn("등록 신청", "시안: 발신번호 등록을 신청했습니다", "btn primary")}</footer></div>')


def msg_cards(seed, kind):
    """발송함 카드 줄 — kind: sms · mail · inbox · sent"""
    r = random.Random(f"acc-box-{seed}")
    out = []
    for _i in range(6):
        c = r.choice([x for x in D.CAMPS if x["group"] in D.ACTIVE])
        auto = kind in ("sms", "mail") and r.random() < .6
        sit = r.choice([a[0] for a in AUTO[1:]]) if auto else "직접 보냄"
        nick = r.choice(G.REVIEWERS)
        cost = ("메일 무료" if kind == "mail" else "뷰마 부담" if sit == "선정 안내" else f"{r.choice([20, 50, 15])}P 차감") \
            if kind in ("sms", "mail") else ""
        who = "자동 발송" if auto else r.choice(["대표", "김지은", "박서준"])
        out.append(f'<div class="mcard"><div class="mh"><b>{nick}</b><span class="add-tag">{esc(c["b"]["name"])}</span>'
                   f'<span class="muted">{esc(c["name"])}</span><span class="sp"></span><span class="muted">{dt(-r.randint(0, 20), "14:0" + str(r.randint(0, 9)))}</span></div>'
                   f'<p>[{esc(c["b"]["name"])}] {sit} — {nick}님, 캠페인 일정 안내드립니다.</p>'
                   f'<div class="mf"><span class="chip">{who}</span>{f"<span class=chip>{cost}</span>" if cost else ""}<span class="sp"></span>'
                   f'{K.btn("다시 보내기", "시안: 다시 보냈습니다") if kind in ("sms", "mail") else K.btn("답장", "시안: 쪽지 창")}</div></div>')
    return f'<div class="mcards">{"".join(out)}</div>'


def tab_sent():
    f = K.fbar(K.dates(), K.select("검색 항목", ["리뷰어명", "내용", "아이디", "이메일·핸드폰"]), K.search("검색어"),
               K.select("구분", ["전체", "내가 보낸 것", "자동 발송"]), K.select("비용", ["전체", "내 부담", "뷰마 부담"]),
               K.select("업체", ["업체 전체"] + [b["name"] for b in P.BIZS[:8]]))
    boxes = [("받은쪽지함", msg_cards("in", "inbox")), ("보낸쪽지함", msg_cards("out", "sent")),
             ("문자발송함", msg_cards("sms", "sms")), ("메일발송함", msg_cards("mail", "mail"))]
    return (f + addbox("카드마다 업체 이름표 · 업체 거르기 = 대행사 추가분") + K.tabs("mb", boxes, checked=2))


def sms_page():
    tabs = [("자동문자 사후인증", tab_verify()), ("자동발송 설정", tab_auto()), ("발신번호 관리", tab_sender()),
            (f"문자·메일 발송내역{K.add_tag('광고주는 메뉴')}", tab_sent())]
    body = (K.head("문자설정", "자동문자 사후인증 · 자동발송 설정 · 발신번호 관리 — 설정은 대행사 하나(업체마다 아님)")
            + K.tabs("sm", tabs) + sender_pop())
    write("sms.html", "문자설정", "sms", body)


# ════════════════ 4. 패널티(penalty.html) ════════════════
RULES = [(5, "경고 알림(메일·문자)"), (10, "7일간 새 캠페인 등록 제한"), (20, "30일간 새 캠페인 등록 제한"), (30, "서비스 이용 정지(1:1 문의로 해제 요청)")]
PEN_REASON = [("자동", "선정 마감 3일 지남 — 미선정", 2), ("자동", "리뷰 검수 7일 넘김", 1), ("자동", "리뷰어 지급 확정 지연", 2),
              ("운영자", "캠페인 무단 중단", 3), ("자동", "체험 제공 누락 신고 확인", 2)]


def pen_rows():
    r = random.Random("acc-pen")
    out = []
    for i, (kind, why, pt) in enumerate(PEN_REASON):
        c = r.choice([x for x in D.CAMPS if x["dts"]])
        out.append((kind, why, c, pt, -r.randint(3, 80), "취소됨" if i == 3 else "적용중"))
    out.sort(key=lambda x: x[4], reverse=True)
    return out


def penalty_page():
    rows = pen_rows()
    total = sum(pt for *_x, pt, _o, st in rows if st == "적용중")
    cur = max((p for p, _t in RULES if total >= p), default=0)
    band = ('<div class="pband ok">누적 패널티 <b>' + f"{total}점</b> — 지금은 이용 제한이 없습니다. "
            f'다음 기준 {next((p for p, _t in RULES if p > total), "—")}점</div>'
            '<div class="pband bad eg">이용 제한 — 현재 서비스 이용이 제한된 상태입니다. <small>(제한될 때 보이는 빨간 띠 · 예시)</small></div>')
    rule_rows = [("", [f"{p}점 이상", t, K.badge("st-red", "해당") if p == cur else ""]) for p, t in RULES]
    heads = [("구분", ""), ("사유", ""), (addh("업체"), "add-c"), ("캠페인", ""), ("점수", "num"), ("부과일", ""), ("상태", "")]
    trs = [("", [k, why, esc(c["b"]["name"]), f'{esc(c["name"])} <small class="rnd">{c["round"]}회차</small>', f"{pt}점",
                 f"{P.d_of(off):%Y-%m-%d}", K.badge("st-orange" if st == "적용중" else "st-gray", st)])
           for k, why, c, pt, off, st in rows]
    body = (K.head("패널티", "광고주 패널티 화면 그대로 — 점수·제재는 대행사 하나 단위")
            + band + addbox("패널티는 대행사에 쌓입니다(Q16 확인 필요) — 어느 업체 캠페인에서 생겼는지 업체 칸으로 보입니다.")
            + '<h2 class="sec-t">패널티 점수별 제재 기준</h2>'
            + K.table([("누적 점수", ""), ("제재 내용", ""), ("현재", "")], rule_rows)
            + '<p class="help">기준 점수·제재 내용은 예시 — 운영 DB 값을 씁니다.</p>'
            + '<h2 class="sec-t">나에게 부여된 패널티</h2>' + K.table(heads, trs))
    write("penalty.html", "패널티", "pen", body)


# ════════════════ 5. 대행사 정보(info.html) ════════════════
def sec_agency():
    pairs = [("상호", AGENCY), ("로고", f'<span class="logo-ph">A</span> {K.btn("로고 올리기", "시안: 파일 고르기")} '
                                    f'<span class="add">{K.add_tag()} 보고서 공개 화면 머리에 나옵니다</span>'),
             ("대표자명", "이정민"), ("사업자번호", "123-45-*****"), ("담당자명", "대표(이정민)"), ("담당자 연락처", "010-****-1234"),
             ("이메일", "contact@anyline.kr"), ("주소", "서울시 ○○구 ○○로 00, 0층(더미)"),
             ("플레이스/오픈마켓", '<span class="muted">업체마다 — <a href="biz.html">업체 화면</a>에서 등록</span>')]
    return (f'<section class="isec" id="s-info"><h2 class="sec-t">대행사 정보</h2><p class="hi">{AGENCY}님, 반갑습니다!</p>'
            '<div class="strip"><span>무료 이용 중 · D-142</span><a class="btn sm" href="plan.html">플랜 보기</a></div>'
            f'<div class="strip"><span>사용 가능 포인트 <b>{won(D.BALANCE)}</b></span><a class="btn sm" href="point.html">포인트 충전</a></div>'
            + kv(pairs) + f'<p class="btns">{K.btn("내정보 수정", pop="pop-edit")} {K.btn("비밀번호 변경", pop="pop-edit")}</p></section>')


def sec_me():
    pairs = [("이름", "김지은"), ("역할", "팀장 · 1팀"), ("이메일", "jieun@anyline.kr"), ("전화", "010-****-5678"),
             ("알림 수신", '<label><input type="checkbox" checked> 메일</label> <label><input type="checkbox" checked> 문자</label> '
                        '<label><input type="checkbox"> 알림톡</label> <small class="muted">담당 업체 이슈만</small>')]
    return ('<section class="isec add" id="s-me"><h2 class="sec-t">내 계정' + K.add_tag() + '</h2>'
            '<p class="help">직원 개인 로그인 계정 — 위 대행사 정보는 모든 직원이 함께 봅니다.</p>'
            + kv(pairs) + f'<p class="btns">{K.btn("비밀번호 변경", "시안: 비밀번호 변경 메일을 보냈습니다")}</p></section>')


def sec_refund_acc():
    bank, acc, holder = REG_ACC
    hist = K.table([("변경일", ""), ("은행", ""), ("계좌번호", ""), ("예금주", ""), ("바꾼 사람", "add-c")],
                   [("", ["2026-10-02", bank, acc, holder, "대표"]), ("", ["2026-03-15", "국민은행", "123-**-****-567", holder, "대표"])])
    return ('<section class="isec" id="s-acc"><h2 class="sec-t">환불계좌</h2>'
            f'<p>현재 계좌 <b>{bank} {acc}</b> · 예금주 {holder}</p><div class="form-c">'
            '<label class="fl">은행<select><option>은행 선택</option><option>국민</option><option selected>신한</option><option>우리</option></select></label>'
            '<label class="fl">계좌번호<input type="text" placeholder="- 없이 숫자만"></label>'
            '<label class="fl">예금주 <small>사업자 명의가 아니면 환불이 거절될 수 있습니다.</small><input type="text"></label>'
            '<label class="fl">비밀번호 확인<input type="password" autocomplete="off"></label>'
            + K.btn("계좌 변경", "시안: 환불계좌를 바꿨습니다", "btn primary") + "</div>"
            + '<h3 class="sub-t">변경 기록</h3>' + hist + "</section>")


def sec_leave():
    n_camp = sum(1 for c in D.CAMPS if c["group"] in D.ACTIVE)
    todo = [f'진행 캠페인 <b>{n_camp}개</b> — 모두 완료·중단해야 합니다 <a href="campaigns.html">캠페인 리스트</a>',
            f'예치 중 포인트 <b>{won(HELD)}</b> — 캠페인이 끝나 사용 가능으로 돌아온 뒤 환불 <a href="point.html">통포인트</a>',
            f'업체 <b>{len(P.BIZS)}곳</b> — 업체 고객 계정으로 이전하거나 보관 <a href="biz.html">업체</a>']
    return ('<section class="isec" id="s-leave"><h2 class="sec-t">대행사 해지 <small class="muted">(광고주: 회원 탈퇴)</small></h2>'
            '<ul class="warn"><li>해지하면 모든 직원 계정이 함께 닫힙니다.</li><li>남은 포인트는 환불 신청 후 해지해야 합니다 — 해지 뒤에는 돌려받을 수 없습니다.</li>'
            '<li>캠페인·리뷰 기록과 보고서 링크는 다시 볼 수 없습니다.</li></ul>'
            f'<div class="add"><h3 class="sub-t">먼저 정리할 것{K.add_tag()}</h3><ul class="todo">{"".join(f"<li>{x}</li>" for x in todo)}</ul></div>'
            '<div class="form-c"><label class="fl">해지 사유<select><option>선택</option><option>서비스를 더 이상 쓰지 않음</option>'
            '<option>비용 부담</option><option>다른 서비스 이용</option><option>기타</option></select></label>'
            '<label class="fl">남기실 말씀<textarea></textarea></label>'
            + K.btn("해지 신청", "시안: 먼저 정리할 것이 남아 있어 해지할 수 없습니다", "btn ghost-danger") + "</div></section>")


def edit_pop():
    basic = ('<label class="fl">담당자명<input type="text" value="이정민"></label>'
             '<label class="fl">이메일<input type="email" value="contact@anyline.kr"></label>'
             '<label class="fl">전화번호<input type="tel" value="010-****-1234"></label>'
             f'<label class="fl">상호명<input type="text" value="{AGENCY}"></label>')
    cats = "".join(f'<label><input type="checkbox"{" checked" if i < 2 else ""}> {x}</label>' for i, x in enumerate(["맛집", "뷰티", "숙박", "육아", "생활"]))
    detail = (f'<div class="fl">관심 카테고리<div class="radios">{cats}</div></div>'
              '<label class="fl">지역<select><option>서울</option><option>경기</option><option>전국</option></select></label>'
              f'<div class="fl">유형{radios("ety", [("v", "방문"), ("s", "배송"), ("p", "기자단")])}</div>')
    pw = ('<label class="fl">지금 비밀번호<input type="password" autocomplete="off"></label>'
          '<label class="fl">새 비밀번호<input type="password" autocomplete="new-password"></label>'
          '<label class="fl">새 비밀번호 확인<input type="password" autocomplete="new-password"></label>')
    return K.pop("pop-edit", "내 정보 수정", K.tabs("ed", [("기본정보", basic), ("상세정보", detail), ("비밀번호변경", pw)]),
                 "저장", "시안: 저장했습니다")


def info_page():
    nav = ('<nav class="anchors"><a href="#s-info">대행사 정보</a><a href="#s-me">내 계정</a>'
           '<a href="#s-acc">환불계좌</a><a href="#s-leave">대행사 해지</a></nav>')
    body = (K.head("대행사 정보", "광고주 마이페이지(내정보 · 환불계좌 · 회원 탈퇴)를 한 화면에 — 정보는 대행사 하나")
            + nav + sec_agency() + sec_me() + sec_refund_acc() + sec_leave() + edit_pop())
    write("info.html", "대행사 정보", "info", body)


# ════════════════ 6. 고객센터(help.html) ════════════════
def tab_alarm():
    r = random.Random("acc-alarm")
    msgs = ["캠페인 신청자가 새로 들어왔습니다", "리뷰가 등록되어 검수를 기다립니다", "포인트 충전이 완료되었습니다",
            "발신번호 심사 결과가 나왔습니다", "1:1 문의에 답변이 등록되었습니다", "리뷰 마감이 3일 남았습니다"]
    trs = []
    for i in range(10):
        c = r.choice([x for x in D.CAMPS if x["group"] in D.ACTIVE])
        unread = i < 4
        trs.append((f'class="{"unread" if unread else ""}"', [f'{"<b>" if unread else ""}[{esc(c["b"]["name"])}] {r.choice(msgs)}'
                                                            f'{"</b>" if unread else ""} <small>{esc(c["name"])}</small>', dt(-i * 2, "09:30")]))
    return (K.fbar(f"알림 (<b>{len(trs)}</b>)", '<span class="muted">90일이 지난 알림은 자동으로 정리 됩니다</span>',
                   '<span class="sp"></span>', K.btn("전체읽음 처리", "시안: 모두 읽음으로 바꿨습니다"))
            + K.fbar(K.select("기간", ["전체", "1주", "1개월", "3개월"]), K.select("읽음", ["전체", "읽음", "안 읽음"]), K.search("제목·내용"))
            + K.table([("알림 내용", ""), ("날짜", "")], trs, ck=True, bulk=K.btn("선택 삭제", "시안: 고른 알림을 지웠습니다")))


def tab_notice():
    items = [("점검", "11월 15일(일) 새벽 2시~4시 서버 점검 안내", -1), ("업데이트", "대행사 대시보드 v0.8 — 계정 메뉴 정리", -2),
             ("안내", "자동발송 알림톡 단가 변경 안내", -6), ("이벤트", "연말 충전 10% 추가 적립 이벤트", -9),
             ("안내", "개인정보처리방침 개정 안내", -15), ("업데이트", "검색결과 리포트 PDF 내려받기", -22),
             ("점검", "10월 25일 결제 시스템 점검", -30), ("안내", "리뷰어 지급 일정 변경(주 2회)", -41)]
    trs = [("", [str(len(items) - i), f'<span class="chip">{k}</span> {t}{" <b class=newb>N</b>" if off >= -3 else ""}', f"{P.d_of(off):%Y-%m-%d}"])
           for i, (k, t, off) in enumerate(items)]
    return K.table([("번호", "num"), ("제목", ""), ("날짜", "")], trs)


QNA_ST = {"접수중": "st-gray", "답변대기": "st-orange", "답변중": "st-blue", "답변완료": "st-green"}


def tab_qna():
    rows = [("포인트", "가상계좌 입금했는데 충전이 안 됐어요", "답변중", -1, "김지은"), ("캠페인", "추가모집 요청 기준이 궁금합니다", "답변완료", -5, "박서준"),
            ("계정", "직원 계정 추가 가능 수", "답변완료", -12, "대표"), ("기타", "보고서 링크에 로고 넣기", "접수중", 0, "김지은")]
    trs = [("", [t, q, K.badge(QNA_ST[s], s), f"{P.d_of(off):%Y-%m-%d}", w]) for t, q, s, off, w in rows]
    form = ('<label class="fl">문의유형<select><option>계정</option><option>캠페인</option><option>포인트</option><option>리뷰</option><option>기타</option></select></label>'
            '<label class="fl">제목<input type="text"></label>'
            '<label class="fl">문의내용 <small>2000자까지</small><textarea maxlength="2000"></textarea></label>'
            f'{file_in("첨부파일")}'
            f'<label class="fl add">관련 업체{K.add_tag()}<select><option>업체 없음(대행사 전체)</option>'
            f'{"".join(f"<option>{esc(b["name"])}</option>" for b in P.BIZS[:8])}</select></label>')
    return (K.fbar(f"1:1 문의 (<b>{len(rows)}</b>)", '<span class="sp"></span>', K.btn("✎ 문의하기", pop="pop-qna", cls="btn sm primary"))
            + K.table([("유형", ""), ("제목", ""), ("상태", ""), ("등록일", ""), (addh("문의한 직원"), "add-c")], trs)
            + K.pop("pop-qna", "1:1 문의하기", form, "문의 등록", "시안: 문의를 등록했습니다"))


FAQ = [("acc", "계정", "비밀번호를 잊었어요", "로그인 화면의 [비밀번호 찾기]에서 이메일로 재설정 링크를 받을 수 있습니다."),
       ("acc", "계정", "직원 계정은 몇 개까지 만들 수 있나요?", "등급별 직원 수 한도까지 만들 수 있습니다(사용료 화면 비교표)."),
       ("camp", "캠페인", "캠페인 승인은 얼마나 걸리나요?", "영업일 기준 1일 안에 검토합니다."),
       ("camp", "캠페인", "모집 인원을 늘릴 수 있나요?", "진행 중 캠페인은 [추가모집 요청]으로 늘릴 수 있습니다."),
       ("pt", "포인트", "예치 중 포인트는 무엇인가요?", "캠페인 시작 때 묶어 두는 포인트입니다. 캠페인이 끝나면 남은 만큼 사용 가능으로 돌아옵니다."),
       ("pt", "포인트", "환불은 언제 되나요?", "승인 후 영업일 3일 안에 등록 계좌로 입금됩니다."),
       ("rv", "리뷰", "리뷰 수정 요청은 몇 번 할 수 있나요?", "리뷰 1건에 2번까지 요청할 수 있습니다."),
       ("etc", "기타", "세금계산서 발행은 어떻게 하나요?", "충전할 때 증빙 신청에서 세금계산서를 고르면 됩니다."),
       ("ag", "대행사", "업체 고객도 로그인할 수 있나요?", "1차는 보고서 링크로만 봅니다. 업체 계정 이전은 해지·이전 때만 합니다.")]


def tab_faq():
    chips = [("all", "전체"), ("acc", "계정"), ("camp", "캠페인"), ("pt", "포인트"), ("rv", "리뷰"), ("etc", "기타"), ("ag", "대행사")]
    ins = "".join(f'<input type="radio" name="fq" id="fq-{v}" value="{v}" class="hr"{" checked" if v == "all" else ""}>' for v, _l in chips)
    labs = "".join(f'<label for="fq-{v}" class="fchip{" add" if v == "ag" else ""}">{lab}</label>' for v, lab in chips)
    acc = "".join(f'<details class="faq-i fq-{k}{" add" if k == "ag" else ""}"><summary><span class="chip">{cat}</span> {q}</summary><p>{a}</p></details>'
                  for k, cat, q, a in FAQ)
    return f'<div class="faq">{ins}<div class="fchips" role="group" aria-label="분류">{labs}</div>{acc}</div>'


HELPS = [("캠페인 등록하기", "유형 고르기부터 승인까지", False), ("신청자 선정", "선정 근거 보는 법", False),
         ("리뷰 검수", "승인 · 수정 요청 · 반려", False), ("포인트 충전·환불", "충전 신청 · 환불 계좌", False),
         ("자동발송 설정", "상황별 문구와 발송 시각", False), ("발신번호 등록", "명의별 필요한 서류", False),
         ("업체 범위", "맨 위 \"전체 업체 ▾\"로 한 업체만 보기", True), ("담당자 배정", "업체마다 담당자 1명 · 알림 받는 사람", True),
         ("보고서 링크", "업체 고객에게 공개 화면 보내기 · 끄기", True), ("팀·역할 권한", "관리자 · 팀장 · 담당자 · 조회", True)]


def tab_help():
    cards = "".join(f'<div class="card{" add" if ag else ""}"><h3>{t}{K.add_tag() if ag else ""}</h3><p class="muted">{d}</p>'
                    f'<p>{K.btn("↗ 전체 도움말에서 보기", "시안: 도움말 새 탭")}</p></div>' for t, d, ag in HELPS)
    return ('<p class="help">화면마다 "?" 버튼 → 도움말 창([↗ 전체 도움말에서 보기][닫기]). 여기는 전체 도움말 목록입니다.</p>'
            f'<div class="cards">{cards}</div>')


def help_page():
    tabs = [("알림", tab_alarm()), ("공지사항", tab_notice()), ("1:1 문의", tab_qna()), ("자주묻는 질문", tab_faq()), ("도움말", tab_help())]
    body = K.head("고객센터", "알림 · 공지사항 · 1:1 문의 · 자주묻는 질문 · 도움말 — 광고주 사이드바 항목을 한 화면에") + K.tabs("hp", tabs)
    write("help.html", "고객센터", "help", body)


if __name__ == "__main__":
    point_page()
    plan_page()
    sms_page()
    penalty_page()
    info_page()
    help_page()
