# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 계정 층 6화면 — 광고주 계정 화면을 "대행사 하나" 단위로 옮김
  point.html 포인트(pay) · plan.html 사용료(plan) · sms.html 문자설정(sms)
  penalty.html 패널티(pen) · info.html 대행사 정보(info) · help.html 고객센터(help)
[2026-11-11 v0.9] 본문 마크업을 광고주 조각 그대로 옮김(같은 요소·같은 class·같은 순서·같은 문구, PHP 빼고 더미값)
  point   ← U:\\admin\\inc\\point.inc.html (+ termPayment.inc.html · index.html #termPayment 껍데기)
  plan    ← planPurchase.inc.html
  sms     ← messageSettingTabs + verifyIdentity(reason=autoSend) + autoSend + sendNumber .inc.html
  penalty ← penalty.inc.html
  info    ← mypage\\mypage.inc.html + mypage\\profile.inc.html(내 정보 수정 창)
  help    ← notice\\notifications · notice · inquiry · faq .inc.html + help.html(전체 도움말 · pageHelp 글 틀)
  광고주가 JS 로 하던 것(탭 · 창 · 거르기 · 펼치기) = 숨은 라디오/체크 + :has() · popover — css/v9-account.css
  광고주 화면에 없는 대행사 추가분 = class="add"(점선) · K.add_tag() · 업체 칸 = col-biz
  실행: python -I build/gen_account.py
"""
import random
import re
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
TAG_RE = re.compile(r'<span class="add-tag">.*?</span>|<[^>]+>')      # 표 머리 글자 → data-label(대행사 표시 떼고)
AGENCY = "애니라인 마케팅"
REG_ACC = ("신한은행", "110-***-**1234", "(주)애*****")      # 더미 · 가림 표시(광고주 acctMask · ownerMask 모양)
# [2026-11-10] 은행 = 실서버 $BANKLIST(core\inc\define.inc.php · 자주 쓰는 순)
BANKS = ["국민은행", "신한은행", "우리은행", "하나은행", "농협은행", "기업은행", "카카오뱅크", "토스뱅크", "케이뱅크", "SC제일은행",
         "새마을금고", "신협", "우체국", "수협은행", "산업은행", "부산은행", "대구은행", "경남은행", "광주은행", "전북은행", "제주은행"]
# 1:1 문의 유형(광고주) = 실서버 taxonomy(inquiryAd)
QNA_TYPES = ["캠페인 등록/심사", "리뷰어/선정", "리뷰 검수", "포인트/정산", "결제/이용권", "계정/기타"]
# [2026-11-11 v0.9] ops.css(.add · .add-tag · 상태 배지) + 이 화면들 붙임 CSS
EXTRA = K.CSS + '<link rel="stylesheet" href="css/v9-account.css">'
WEEK = "월화수목금토일"


# ════════════════ 공통 ════════════════
def write(fname, title, active, body):
    """[2026-11-11 v0.9] 본문 = 광고주 조각 뿌리(.cmp-layout · .page-container …)를 .work 바로 아래에"""
    out = P.page(title, active, body, None, EXTRA, "ops.js")
    (K.ROOT / fname).write_text(out, encoding="utf-8")
    print(f"written {fname} ({len(out.encode('utf-8')) / 1024:.0f} KB)")


def dt(off, hm="10:00"):
    """광고주 표기 Y.m.d H:i"""
    return f"{P.d_of(off):%Y.%m.%d} {hm}"


def dw(off):
    """광고주 표기 Y-m-d(요일)"""
    d = P.d_of(off)
    return f"{d:%Y-%m-%d}({WEEK[d.weekday()]})"


def num(n):
    return f"{n:,}"


def tag(text="대행사"):
    return K.add_tag(text)


def flash(label, msg, cls, style=""):
    """저장·이동하는 버튼 자리 — 누르면 안내 한 줄(js/ops.js) · style = 광고주 인라인 style 그대로"""
    st = f' style="{style}"' if style else ""
    return f'<button type="button" class="{cls} js-flash" data-msg="{esc(msg)}"{st}>{label}</button>'


def hide_btn(mid, inner, cls, label=""):
    aria = f' aria-label="{label}"' if label else ""
    return f'<button type="button" class="{cls}" popovertarget="{mid}" popovertargetaction="hide"{aria}>{inner}</button>'


def tab_bar(name, labels, checked=0, btn="cmp-tab-btn", bar="cmp-top-tabs", extra=""):
    """[2026-11-11 v0.9] 광고주 탭 버튼 → 숨은 라디오 + <label class="(광고주 버튼 class) v9l">
    labels = [(글자, 대행사 추가분?)] · 돌려줌 (라디오 html, 탭 줄 html) — 라디오는 .v9t 의 바로 아래에 둔다"""
    radios = "".join(f'<input type="radio" name="{name}" id="{name}-{i}" class="v9r"{" checked" if i == checked else ""}>'
                     for i in range(len(labels)))
    labs = "".join(f'<label for="{name}-{i}" class="{btn} v9l{" add" if add else ""}">{lab}{tag() if add else ""}</label>'
                   for i, (lab, add) in enumerate(labels))
    return radios, f'<div class="{bar}">{labs}{extra}</div>'


def modal(mid, title, body, footer, cls="pm-refund-modal", content="pm-refund-content"):
    """[2026-11-11 v0.9] 광고주 .modal-wrap 껍데기 그대로 + popover(열기 = popovertarget)"""
    return (f'<div class="modal-wrap {cls}" id="{mid}" popover>'
            f'{hide_btn(mid, "", "modal-dim", "닫기")}'
            f'<div class="modal-content {content}"><div class="modal-header"><h3 class="modal-title">{title}</h3>'
            f'{hide_btn(mid, CLOSE_ICON, "btn-close", "닫기")}</div>'
            f'<div class="modal-body">{body}</div><div class="modal-footer">{footer}</div></div></div>')


CLOSE_ICON = '<span class="material-symbols-outlined">close</span>'


def detail_list(pairs):
    return '<dl class="pm-detail-list">' + "".join(
        f'<div class="pm-detail-row"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in pairs) + "</dl>"


def camp_link(c):
    return f'<a href="campaigns.html#c-{c["id"]}">{esc(c["name"])}</a> <small class="rnd">{c["round"]}회차</small>'


# ════════════════ 1. 포인트(point.html) ← point.inc.html ════════════════
LEDGER = S.ledger()          # (off, hm, kind, b, c, amt, bal) — 정산 화면과 같은 줄
PRESETS = [10000, 50000, 100000, 300000, 500000]
CHARGE_AMT = 100000          # 입력칸에 채워 둔 예시 금액(광고주는 0 — 계산 미리보기를 보이려고)
CHARGE_ST = {"결제대기": "st-wait", "입금대기(가상계좌)": "st-wait", "입금대기": "st-wait", "확인중": "st-wait",
             "완료": "st-done", "거절": "st-cancel", "취소": "st-cancel"}


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


def pm_table(heads, rows, empty, extra_cls=""):
    """광고주 .pm-table — heads = [(이름, th class)] · rows = [(tr 속성, [(td 속성, html)])]"""
    th = "".join(f'<th{f" class={chr(34)}{c}{chr(34)}" if c else ""}>{h}</th>' for h, c in heads)
    if not rows:
        body = f'<tr><td colspan="{len(heads)}" style="text-align:center;color:#0e0e0e;padding:24px 0;">{empty}</td></tr>'
    else:
        body = "".join(f'<tr{(" " + a) if a else ""}>' + "".join(
            f'<td data-label="{TAG_RE.sub("", heads[i][0])}"{(" " + ta) if ta else ""}>{v}</td>' for i, (ta, v) in enumerate(cells)) + "</tr>"
            for a, cells in rows)
    return (f'<div class="pm-history-list"><table class="pm-table{(" " + extra_cls) if extra_cls else ""}">'
            f'<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')


def gray_box(title, lines):
    """광고주 '상태 안내 · 증빙 안내' 회색 글상자(인라인 style 그대로)"""
    return ('<div class="pm-section"><div style="padding:12px 14px;background:#f7f7fa;border-radius:8px;font-size:12.5px;'
            f'line-height:1.8;color:#0e0e0e;"><strong style="color:#3a3a3c;">{title}</strong><br>' + "<br>".join(lines) + "</div></div>")


def panel_charge():
    v = CHARGE_AMT
    pre = "".join(flash(f"+ {p // 10000}만", f"시안: {p:,}P 를 더합니다", "pm-preset-btn") for p in PRESETS)
    pre += flash("초기화", "시안: 금액을 0 으로 돌립니다", "pm-preset-btn pm-btn-reset")
    row = 'style="display:flex;justify-content:space-between;'
    brk = (f'<div class="pm-terms-box" id="chargeBreak" style="margin-top:14px;" data-vat-rate="0.1">'
           '<div class="pm-terms-content" style="line-height:2;">'
           f'<div {row}"><span>적립 포인트</span><b id="cbPoint">{num(v)} P</b></div>'
           f'<div {row}color:#666;"><span>공급가액</span><span id="cbSupply">{num(v)} 원</span></div>'
           f'<div {row}color:#666;"><span>부가세 <i>10%</i></span><span id="cbVat">{num(v // 10)} 원</span></div>'
           f'<div {row}border-top:1px solid #e5e7eb;margin-top:6px;padding-top:6px;"><span><b>결제 금액</b></span>'
           f'<b id="cbPay" style="color:#5b4cf5;">{num(v * 11 // 10)} 원</b></div></div>'
           '<p style="margin:8px 0 0;font-size:13px;line-height:1.8;color:#777;">입력하신 금액이 <b>적립되는 포인트</b>이고, '
           '결제는 <b>부가세를 더한 금액</b>으로 이루어집니다. 세금계산서·현금영수증은 결제 금액 기준으로 발행됩니다.</p></div>')
    amount = ('<div class="pm-section"><h3 class="pm-section-title">충전 금액 선택</h3>'
              f'<div class="pm-amount-presets">{pre}</div>'
              f'<div class="pm-amount-input-wrap"><input type="text" class="pm-amount-input charge-amount" data-format="number" '
              f'placeholder="충전할 포인트를 입력해주세요" value="{num(v)}" inputmode="numeric" aria-label="충전 포인트">'
              '<span class="pm-amount-unit">P</span></div>'
              '<p class="pm-amount-notice">* 최소 충전 포인트는 10,000P입니다.</p>' + brk + "</div>")
    notice = lambda t: (f'<p class="pm-card-notice"><span class="material-symbols-outlined">info</span>'  # noqa: E731
                        f'<span class="pm-card-notice__text">{t}</span></p>')
    method = ('<div class="pm-section"><h3 class="pm-section-title">결제 방법</h3><div class="pm-payment-methods">'
              '<label class="pm-method-item"><input type="radio" name="payMethod" value="CARD" checked>'
              '<div class="pm-method-box"><span class="material-symbols-outlined">credit_card</span><span>신용카드</span></div></label>'
              '<label class="pm-method-item"><input type="radio" name="payMethod" value="VBANK">'
              '<div class="pm-method-box"><span class="material-symbols-outlined">account_balance_wallet</span><span>가상계좌</span></div></label>'
              '</div><div class="pm-method-detail pm-card-info active">'
              + notice("충전 신청 시 나이스페이(NicePay) 카드 결제창이 열리며, 결제 승인이 완료되면 포인트가 즉시 충전됩니다.")
              + '</div><div class="pm-method-detail pm-vbank-info">'
              + notice("충전 신청 시 나이스페이(NicePay)가 입금 전용 가상계좌를 발급합니다. <b>계좌 발급만으로는 포인트가 충전되지 않으며</b>, "
                       "발급된 계좌로 실제 입금을 완료해야 포인트가 충전됩니다. 입금기한은 발급 후 <b>3일(72시간)</b>이며, "
                       "기한 안에 입금하지 않으면 신청이 자동으로 만료됩니다.")
              + "</div></div>")
    req = '<span style="color:#c62828;">*</span>'
    grp = lambda lab, fid, val, mx, ph="": (  # noqa: E731
        f'<div class="pm-form-group"><label for="{fid}">{lab} {req}</label><input type="text" class="p-input" id="{fid}" '
        f'name="{fid}" maxlength="{mx}"{f" placeholder={chr(34)}{ph}{chr(34)}" if ph else ""} value="{val}"></div>')
    gray = 'style="margin:10px 0 0;font-size:13px;line-height:1.8;color:#777;"'
    evidence = ('<div class="pm-section pm-evidence-section"><h3 class="pm-sub-title">증빙 신청 '
                '<span style="font-weight:400;color:#888;font-size:13px;">(선택)</span></h3><div class="pm-evidence-tabs">'
                + "".join(f'<label class="pm-ev-tab"><input type="radio" name="evType" value="{k}"{" checked" if k == "none" else ""}>'
                          f'<span>{lab}</span></label>' for k, lab in [("none", "신청 안 함"), ("tax", "세금계산서"), ("cash", "현금영수증")])
                + '</div><div class="pm-ev-fields" id="evFieldsTax"><div class="pm-form-grid">'
                + grp("사업자등록번호", "evBizNo", "123-45-*****", 20, "숫자만") + grp("상호", "evBizName", AGENCY, 100)
                + grp("대표자", "evCeo", "이정민", 50) + grp("받으실 이메일", "evEmail", "tax@anyline.kr", 100)
                + f'</div><p {gray}>가입하실 때 등록하신 사업자 정보를 채워 두었습니다. 다르면 고쳐 주세요 — <b>여기 적으신 정보 그대로 발행</b>됩니다.</p>'
                f'<p class="add" {gray}>{tag()} 세금계산서는 대행사 명의 1장으로 발행됩니다(업체별로 나누지 않음).</p></div>'
                '<div class="pm-ev-fields" id="evFieldsCash"><div class="pm-form-group" style="max-width:320px;">'
                f'<label for="evCashPhone">휴대폰 번호 {req}</label><input type="text" class="p-input" id="evCashPhone" name="evCashPhone" '
                'maxlength="20" placeholder="숫자만" value="010-****-1234"></div>'
                f'<p {gray}><b>소득공제용</b>으로 발행됩니다. 사업자 지출증빙이 필요하시면 세금계산서를 선택해 주세요.</p></div>'
                '<p style="margin:12px 0 0;font-size:13px;line-height:1.8;color:#777;">· 증빙은 <b>결제 금액(부가세 포함)</b> 기준으로 발행됩니다.<br>'
                '· 결제가 완료된 뒤 운영자가 확인해 발행하며, 발행되면 위 이메일·번호로 전달됩니다.<br>'
                '· 나중에 필요해지셨다면 1:1 문의로 요청하셔도 됩니다.</p></div>')
    terms = ('<div class="pm-section"><div class="pm-terms-box"><div class="pm-terms-content"><p>충전된 포인트는 뷰마 내 유료 서비스 결제 시 사용 가능합니다. '
             '계좌이체·카드결제는 결제 승인이 완료되면 포인트가 즉시 충전됩니다. 가상계좌는 계좌가 발급된 뒤 <b>실제 입금이 확인된 시점</b>에 '
             '포인트가 충전됩니다(입금기한 3일). 결제 취소 및 환불은 고객센터를 통해 문의해 주세요.</p></div>'
             '<div class="pm-agreement-row"><label class="pm-terms-check" for="agreeCharge">'
             '<input type="checkbox" id="agreeCharge" class="agree-charge"><span class="pm-check-box"></span>'
             '<span class="pm-check-text">위 결제 안내 및 약관에 동의합니다.</span></label>'
             '<button type="button" class="btn-view-terms" popovertarget="termPayment">약관보기</button></div></div>'
             + flash("포인트 충전 신청하기", "시안: 나이스페이 결제창으로 이동합니다", "pm-btn-submit") + "</div>")
    # 대행사: 지갑 1개를 모든 업체가 함께 씀 · 충전은 관리자만
    who = (f'<p class="pm-amount-notice add">{tag()} 지갑 1개를 모든 업체가 함께 씁니다. 충전은 <b>관리자</b>만 — 담당자는 '
           + flash("관리자에게 충전 요청", "시안: 관리자에게 충전 요청을 보냈습니다", "pm-preset-btn") + "</p>")
    return f'<div class="pm-panel pm-panel-charge v9p">{who}{amount}{method}{evidence}{terms}</div>'


def panel_charge_hist():
    r = random.Random("acc-req")
    rows = [(dt(0, "09:40"), "가상계좌", 2000000, "tax", "입금대기(가상계좌)", "김지은(팀장) 요청 → 대표"),
            (dt(-1, "16:22"), "카드", 500000, "", "취소", "대표")]
    rows += [(dt(off, hm), r.choice(["카드", "가상계좌"]), amt, "tax", "완료", "대표") for off, hm, amt in CHARGES]
    trs = []
    for d, m, a, ev, st, who in rows:
        money = (f'{num(a)} P<div style="font-size:12px;color:#555;margin-top:2px;">결제 {num(a * 11 // 10)}원 '
                 f'<span style="color:#888;">(부가세 {num(a // 10)})</span></div>')
        trs.append(("", [("", d), ("", m), ("", money), ("", {"tax": "세금계산서", "cash": "현금영수증"}.get(ev, "-")),
                         ("", f'<span class="{CHARGE_ST[st]}">{st}</span>'), ('class="add"', who)]))
    heads = [("신청일시", ""), ("결제수단", ""), ("금액", ""), ("증빙", ""), ("상태", ""), ("신청·요청자" + tag(), "add")]
    st = lambda k, t: f"· <strong>{k}</strong> : {t}"  # noqa: E731
    guide = gray_box("상태 안내", [
        st("결제대기", "계좌이체·카드결제·가상계좌 신청이 접수됐지만 아직 결제(발급) 승인 전인 상태입니다. 정상적으로는 잠시 후 자동으로 상태가 바뀝니다."),
        st("입금대기(가상계좌)", "가상계좌가 발급되어 계좌번호를 안내받은 상태입니다. 안내받은 계좌로 <b>3일(72시간)</b> 이내에 입금을 완료해야 "
           "포인트가 충전되며, 기한을 넘기면 자동으로 만료(거절)됩니다."),
        st("입금대기 / 확인중", "예전 방식인 무통장입금으로 접수된 건에서만 나타납니다. 입금 확인 후 운영자가 최종 승인(결재)하면 포인트가 충전됩니다."),
        st("완료", "포인트가 정상적으로 충전되었습니다."),
        st("거절", "입금 확인이 안 되었거나 사유가 있어 신청이 반려되었습니다. 포인트는 충전되지 않습니다."),
        st("취소", "결제가 결제 자체에서 취소된 경우입니다."),
        "예전 방식인 무통장입금 신청은 접수 후 <strong>7일</strong> 안에 입금이 확인되지 않으면 자동으로 삭제됩니다. 계좌이체(실시간)와 카드결제는 "
        "결제창에서 결제가 완료되는 즉시 포인트가 반영되므로 별도로 기다리실 필요가 없습니다."])
    return ('<div class="pm-panel pm-panel-chargeHistory v9p"><div class="pm-section"><h3 class="pm-section-title">충전 신청 내역</h3>'
            '<p class="pm-amount-notice">계좌이체·카드결제는 결제 승인 즉시 포인트가 충전됩니다. 가상계좌는 발급 후 <strong>3일(72시간)</strong> 이내 '
            '입금이 확인되면 포인트가 충전되고, 기한 안에 입금이 없으면 자동으로 만료(거절)됩니다. (예전 방식인 무통장입금으로 접수된 건은 '
            '신청 후 <strong>7일</strong> 이상 미입금 시 자동 삭제됩니다.)</p>'
            + pm_table(heads, trs, "충전 신청 내역이 없습니다.") + "</div>" + guide + "</div>")


def panel_refund():
    bank, acc, owner = REG_ACC
    ro = lambda lab, v: (f'<div class="pm-form-group"><label>{lab}</label>'  # noqa: E731
                         f'<input type="text" class="pm-input" value="{v}" readonly aria-label="{lab}"></div>')
    return ('<div class="pm-panel pm-panel-refund v9p"><div class="pm-section"><h3 class="pm-section-title">환불 신청</h3>'
            f'<p class="pm-amount-notice">환불 가능 포인트 <strong>{num(D.BALANCE)}</strong> P <span style="color:#888;">(보유 {num(D.BALANCE)} P)</span> '
            '중 환불받을 금액을 신청합니다. 관리자 승인 후 입력하신 계좌로 환불되며, <b>승인 시점에 포인트가 차감</b>됩니다. '
            '캠페인에 예치된 보증금은 환불 대상이 아닙니다.</p>'
            f'<p class="pm-amount-notice add">{tag()} 예치 중 <strong>{num(HELD)}</strong> P 는 환불할 수 없습니다 — 캠페인이 끝나 남은 예치가 '
            '보유 포인트로 돌아온 뒤 환불할 수 있습니다.</p>'
            '<div class="pm-amount-input-wrap"><input type="text" class="pm-amount-input" id="refundAmount" data-format="number" '
            f'placeholder="환불 신청 금액을 입력해주세요" value="0" inputmode="numeric" data-refundable="{D.BALANCE}" aria-label="환불 포인트">'
            '<span class="pm-amount-unit">P</span>'
            + flash("전액", "시안: 환불 가능 포인트 전액을 넣었습니다", "pm-preset-btn", "margin-left:8px;")
            + '</div></div>'
            '<div class="pm-section"><h3 class="pm-section-title">환불 받을 계좌</h3><p class="pm-amount-notice">마이페이지에 등록하신 계좌로 환불됩니다. '
            '다른 계좌로 받으시려면 <a href="info.html#s-acc">마이페이지 → 환불계좌</a>에서 먼저 바꿔 주세요.</p>'
            f'<div class="pm-form-grid">{ro("은행", bank)}{ro("계좌번호", acc)}{ro("예금주", owner)}</div></div>'
            '<div class="pm-section"><h3 class="pm-section-title">환불 요청 사유 <span style="color:#e53e3e;">*</span></h3>'
            '<textarea id="refundReason" class="pm-input" rows="3" maxlength="255" placeholder="환불을 요청하는 사유를 입력해주세요. (필수)" '
            'style="width:100%;resize:vertical;" aria-label="환불 요청 사유"></textarea></div>'
            '<div class="pm-section">' + flash("포인트 환불 신청하기", "시안: 환불 신청을 접수했습니다", "pm-btn-submit") + "</div></div>")


REFUNDS = [(-2, "14:10", 300000, "승인대기", "", "", "남은 포인트 정리"),
           (-19, "11:02", 500000, "승인완료", dt(-17, "15:00"), "확인 후 환불 처리", "캠페인 종료 후 잔액 환불"),
           (-33, "10:30", 200000, "거절", dt(-32, "09:20"), "사업자 명의 계좌가 아님 — 계좌 변경 후 다시 신청", "남은 포인트 정리")]
REFUND_ST = {"승인대기": "st-wait", "승인완료": "st-done", "거절": "st-cancel"}


def panel_refund_hist():
    bank, acc, owner = REG_ACC
    trs, pops = [], []
    for i, (off, hm, amt, st, done, memo, why) in enumerate(REFUNDS):
        mid = f"refundDetailModal{i}"
        money = (f'-{num(amt)}<div style="font-size:12px;color:#555;margin-top:2px;font-weight:400;">부가세 +{num(amt // 10)}원<br>'
                 f'환급 {num(amt * 11 // 10)}원</div>')
        trs.append(("", [("", dt(off, hm)), ('class="minus"', money), ("", f"{bank} {acc} ({owner})"),
                         ("", f'<span class="{REFUND_ST[st]}">{st}</span>'),
                         ("", f'<button type="button" class="pm-detail-btn" popovertarget="{mid}">상세내용보기</button>')]))
        body = (detail_list([("신청일시", dt(off, hm)), ("처리상태", st), ("환불 금액", f"{num(amt)} P"), ("환불 계좌", f"{bank} {acc} ({owner})"),
                             ("예금주", "-"), ("요청 사유", why), ("처리일시", done or "-")])
                + '<div class="pm-detail-memo"><h4 class="pm-detail-memo-title"><span class="material-symbols-outlined">sticky_note_2</span>관리자 메모</h4>'
                f'<p class="pm-detail-memo-text">{memo or "-"}</p></div>')
        pops.append(modal(mid, "환불 신청 상세", body, hide_btn(mid, "확인", "btn btn-primary")))
    heads = [("신청일시", ""), ("금액", ""), ("환불계좌", ""), ("상태", ""), ("상세", "")]
    return ('<div class="pm-panel pm-panel-refundHistory v9p"><div class="pm-section"><h3 class="pm-section-title">환불 신청 내역</h3>'
            + pm_table(heads, trs, "환불 신청 내역이 없습니다.") + "</div></div>", "".join(pops))


L_KIND = {"charge": "충전", "dep": "캠페인 예치", "pay": "리뷰 지급", "back": "잔액 환불", "sms": "서비스 이용", "talk": "서비스 이용"}
L_CAT = {"charge": "charge", "dep": "campaign", "pay": "campaign", "back": "campaign", "sms": "sms", "talk": "sms"}


def ledger_rows():
    """정산 ledger() + 문자·알림톡 사용(서비스 이용) 몇 줄 — 새 것부터 (off, hm, kind, b, c, amt, bal)"""
    r = random.Random("acc-ledger")
    rows = list(LEDGER)
    for _i in range(8):
        kind = r.choice(["sms", "talk"])
        c = r.choice([x for x in D.CAMPS if x["group"] in D.ACTIVE])
        n = r.randint(3, 25)
        rows.append((-r.randint(0, 30), f"{r.randint(9, 18):02d}:{r.randint(0, 59):02d}", kind, c["b"], c,
                     -n * (20 if kind == "sms" else 15), None))
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


HIST_CATS = [("all", "전체"), ("sms", "문자·알림톡"), ("campaign", "캠페인"), ("charge", "충전·환불")]


def panel_history():
    rows = ledger_rows()
    filt = ('<div class="pm-hist-filter" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">'
            + "".join(f'<input type="radio" name="phf" id="phf-{k}" class="v9r"{" checked" if k == "all" else ""}>' for k, _l in HIST_CATS)
            + "".join(f'<label for="phf-{k}" class="pm-preset-btn" data-cat="{k}">{lab}</label>' for k, lab in HIST_CATS)
            + f'<span id="pmHistSum" style="margin-left:auto;align-self:center;font-size:13px;color:#0e0e0e;">{len(rows)}건</span></div>')
    trs, pops = [], []
    for i, (off, hm, kind, b, c, amt, bal) in enumerate(rows):
        mid = f"pointDetailModal{i}"
        memo = ledger_text(kind, c, amt)
        sign = "+" if amt >= 0 else "-"
        attrs = f'class="js-pm-hist" data-cat="{L_CAT[kind]}" data-amt="{amt}"' + (f' data-biz="{b["id"]}"' if b else "")
        trs.append((attrs, [("", dt(off, hm)), ("", L_KIND[kind]), ("", memo),
                            ('class="col-biz add"', esc(b["name"]) if b else "-"), ('class="col-biz add"', camp_link(c) if c else "-"),
                            (f'class="{"plus" if amt >= 0 else "minus"}"', f"{sign}{num(abs(amt))}"),
                            ("", '<span class="st-done">완료</span>'),
                            ("", f'<button type="button" class="pm-detail-btn" popovertarget="{mid}">상세보기</button>')]))
        pops.append(modal(mid, "포인트 내역 상세", detail_list(
            [("일시", dt(off, hm)), ("구분", L_KIND[kind]), ("내역", memo), ("금액", f"{sign}{num(abs(amt))} P"),
             ("처리 후 잔액", f"{num(bal)} P" if bal is not None else "-"), ("상태", "완료")]
            + ([(f"업체{tag()}", esc(b["name"]))] if b else [])), hide_btn(mid, "확인", "btn btn-primary")))
    heads = [("일시", ""), ("구분", ""), ("내역", ""), ("업체" + tag(), "col-biz add"), ("캠페인" + tag(), "col-biz add"),
             ("금액", ""), ("상태", ""), ("상세", "")]
    return ('<div class="pm-panel pm-panel-history v9p">' + filt + pm_table(heads, trs, "포인트 내역이 없습니다.") + "</div>",
            "".join(pops))


def panel_ledger():
    rows = [(dt(off, hm), "포인트 충전", "포인트 충전 · 신용카드", num(amt * 11 // 10), ("plus", f"+{num(amt)}"),
             flash("영수증", "시안: 영수증 새 창", "pm-detail-btn")) for off, hm, amt in CHARGES]
    off, hm, amt = REFUNDS[1][:3]
    back = amt * 11 // 10
    rows.append((dt(off, hm), "포인트 환불", "포인트 환불 · 승인완료", f'<span style="color:#c0392b;">-{num(back)}</span>', ("minus", f"-{num(amt)}"),
                 flash("영수증", "시안: 영수증 새 창", "pm-detail-btn")))
    rows.sort(key=lambda x: x[0], reverse=True)
    paid = sum(a * 11 // 10 for _o, _h, a in CHARGES)
    trs = [("", [("", d), ("", k), ("", t), ("", w), (f'class="{pc}"', pv), ("", rc)]) for d, k, t, w, (pc, pv), rc in rows]
    heads = [("일시", ""), ("구분", ""), ("내용", ""), ("금액(원)", ""), ("포인트", ""), ("영수증", "")]
    period = (f'<div class="pm-section"><h3 class="pm-section-title">조회 기간</h3>'
              '<form style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;" onsubmit="return false;">'
              f'<input type="date" class="pm-input" name="stFrom" value="{P.d_of(-40):%Y-%m-%d}" style="width:170px;" aria-label="시작일">'
              '<span style="color:#0e0e0e;">~</span>'
              f'<input type="date" class="pm-input" name="stTo" value="{P.d_of(0):%Y-%m-%d}" style="width:170px;" aria-label="끝일">'
              + flash("조회", "시안: 기간을 다시 조회합니다", "pm-preset-btn")
              + flash('<span class="material-symbols-outlined" style="font-size:17px;">print</span>거래내역서 인쇄', "시안: 거래내역서 새 창",
                      "pm-preset-btn", "margin-left:auto;display:inline-flex;align-items:center;gap:4px;")
              + "</form></div>")
    body = ('<div class="pm-section"><h3 class="pm-section-title">거래 내역 <span style="font-weight:400;font-size:13px;color:#0e0e0e;margin-left:6px;">'
            f'실제 결제 <strong style="color:#3a3a3c;">{num(paid - back)}</strong>원 <span style="color:#c0392b;">(환불 −{num(back)}원 차감)</span></span></h3>'
            '<p class="pm-amount-notice">결제가 <strong>끝난 건만</strong> 보여 드립니다. 결제대기·입금대기·거절된 신청은 [충전 신청 내역] 에서 확인해 주세요. '
            '금액(원)은 실제로 오간 현금이고, 포인트(P)는 사이트 안에서 쓰인 적립금이라 서로 더하지 않습니다.</p>'
            + pm_table(heads, trs, "이 기간에 거래 내역이 없습니다.") + "</div>")
    guide = gray_box("증빙 안내", [
        "· <strong>영수증 / 거래내역서</strong> 는 거래 사실을 확인해 드리는 서류입니다. <strong style=\"color:#c0392b;\">세금계산서·현금영수증이 아닙니다.</strong>",
        "· <strong>세금계산서·현금영수증</strong> 은 포인트 충전 시 증빙 구분을 선택하신 건에 한해 별도로 발행됩니다. 신청하지 않으셨다면 1:1 문의로 요청해 주세요.",
        "· 유료등급 구매 건의 이용 기간은 [유료등급 구매 → 결제내역] 에서 확인하실 수 있습니다."])
    return f'<div class="pm-panel pm-panel-ledger v9p">{period}{body}{guide}</div>'


def panel_held():
    """[대행사 추가] 예치 중 — 진행 캠페인마다 묶인 포인트"""
    hl = sorted(held_list(), key=lambda x: -x[2])
    trs = [(f'data-biz="{c["bid"]}"', [('class="col-biz"', K.biz_cell(c["b"])), ("", camp_link(c)),
                                       ("", K.badge(D.STATE_CLS[c["state"]], c["state"])), ("", num(c["deposit"])),
                                       ("", num(paid)), ("", f"<b>{num(left)}</b>")]) for c, paid, left in hl]
    trs.append(("", [('class="col-biz"', "<b>합계</b>"), ("", ""), ("", ""), ("", num(sum(c["deposit"] for c, _p, _l in hl))),
                     ("", num(sum(p for _c, p, _l in hl))), ("", f"<b>{num(HELD)}</b>")]))
    heads = [("업체", "col-biz"), ("캠페인", ""), ("상태", ""), ("예치", ""), ("지급됨", ""), ("남은 예치", "")]
    return ('<div class="pm-panel pm-panel-held v9p add"><div class="pm-section"><h3 class="pm-section-title">예치 중' + tag() + "</h3>"
            f'<p class="pm-amount-notice">진행 캠페인 <strong>{len(hl)}</strong>개에 <strong>{num(HELD)}</strong> P 가 묶여 있습니다. '
            f'캠페인 시작 = 보유 → 예치, 리뷰 지급 = 예치에서 차감(지급액 + 수수료 {int(D.FEE * 100)}%), 완료·중단 = 남은 예치 → 보유.</p>'
            + pm_table(heads, trs, "예치 중인 포인트가 없습니다.") + "</div></div>")


def panel_use():
    """[대행사 추가] 업체별 사용내역 — 기간 고르기(라디오 + :has)"""
    radios = "".join(f'<input type="radio" name="upp" id="upp-{k}" class="v9r"{" checked" if i == 0 else ""}>'
                     for i, (k, _l) in enumerate(S.PERIODS))
    labs = "".join(f'<label for="upp-{k}" class="pm-preset-btn">{lab}</label>' for k, lab in S.PERIODS)
    tables = []
    for k, _lab in S.PERIODS:
        rows = S.usage_rows(k)
        trs = [(f'data-biz="{b["id"]}"', [('class="col-biz"', K.biz_cell(b)), ('class="col-biz"', S.OWNER[b["id"]]), ("", n),
                                          ("", pays), ("", f"<b>{num(u)}</b>")]) for b, n, pays, u in rows]
        trs.append(("", [('class="col-biz"', "<b>합계</b>"), ('class="col-biz"', ""), ("", sum(x[1] for x in rows)),
                         ("", sum(x[2] for x in rows)), ("", f"<b>{num(sum(x[3] for x in rows))}</b>")]))
        heads = [("업체", "col-biz"), ("담당자", "col-biz"), ("캠페인 수", ""), ("지급 건수", ""), ("사용액(지급 + 수수료)", "")]
        tables.append(f'<div class="v9-use v9-use-{k}">' + pm_table(heads, trs, "사용 내역이 없습니다.") + "</div>")
    return ('<div class="pm-panel pm-panel-use v9p add"><div class="pm-section"><h3 class="pm-section-title">업체별 사용내역' + tag() + "</h3>"
            f'<div class="pm-hist-filter" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">{radios}{labs}'
            + flash("엑셀", "시안: 업체별 사용내역 엑셀을 내려받습니다", "pm-preset-btn", "margin-left:auto;")
            + "</div>" + "".join(tables)
            + '<p class="pm-amount-notice">업체별로 나눠 청구할 때 쓰는 표입니다. 보고서(업체 고객용)에는 금액이 나오지 않습니다.</p></div></div>')


def terms_modal():
    """index.html 의 #termPayment 껍데기 + termPayment.inc.html — 약관 원문은 운영 DB(더미 몇 줄)"""
    mid = "termPayment"
    text = ("<p>시안 — 약관 원문은 운영 사이트(terms 테이블 · advertiser_payment)의 글을 씁니다.</p>"
            "<ol><li>충전한 포인트는 뷰마 서비스(캠페인 예치·리뷰어 지급·문자 발송·등급 이용) 안에서만 씁니다.</li>"
            "<li>환불은 본인확인 후 사업자 명의 계좌로만 가능합니다.</li><li>예치 중인 포인트는 캠페인이 끝난 뒤 환불할 수 있습니다.</li>"
            "<li>마지막 사용일로부터 5년이 지난 포인트는 소멸됩니다.</li></ol>")
    foot = ('<button type="button" class="js-flash" data-msg="시안: 개정 이력 새 창" style="margin-right:auto;align-self:center;font-size:13px;'
            'color:#5b3ecf;text-decoration:underline;background:none;border:0;cursor:pointer;">개정 이력 보기</button>'
            + hide_btn(mid, "확인", "btn btn-primary btn-confirm"))
    return (f'<div class="modal-wrap terms-modal-payment" id="{mid}" popover>{hide_btn(mid, "", "modal-dim", "닫기")}'
            '<div class="modal-content terms-modal-content"><div class="modal-header"><h3 class="modal-title">뷰마 광고주 결제(포인트 충전) 약관</h3>'
            + hide_btn(mid, CLOSE_ICON, "btn-close", "닫기")
            + f'</div><div class="modal-body terms-modal-body"><div class="terms-text-content">{text}</div></div>'
            f'<div class="modal-footer terms-modal-footer">{foot}</div></div></div>')


def point_page():
    labels = [("포인트 충전", False), ("충전 신청 내역", False), ("포인트 환불", False), ("환불 신청 내역", False),
              ("포인트 내역", False), ("결제·거래내역", False), ("예치 중", True), ("업체별 사용내역", True)]
    radios, bar = tab_bar("pmt", labels, bar="cmp-top-tabs pm-tabs")
    refund_hist, rf_pops = panel_refund_hist()
    history, pd_pops = panel_history()
    head = ('<div class="pm-header text-center"><h2 class="pm-title">포인트</h2>'
            f'<p class="pm-desc">보유 포인트 <strong id="pmBalanceText">{num(D.BALANCE)}</strong> P'
            f'<span class="add v9-held">{tag()} 예치 중 <strong>{num(HELD)}</strong> P · 합계 {num(D.BALANCE + HELD)} P</span></p></div>')
    body = (f'<div class="cmp-layout pm-layout v9t">{radios}{bar}<div class="cmp-page-card pm-page-card">{head}<div class="pm-body">'
            + panel_charge() + panel_charge_hist() + panel_refund() + refund_hist + history + panel_ledger() + panel_held() + panel_use()
            + "</div></div>" + rf_pops + pd_pops + "</div>" + terms_modal())
    write("point.html", "포인트", "pay", body)


# ════════════════ 2. 사용료(plan.html) ← planPurchase.inc.html ════════════════
FEATS = [("campaignLoad", "이전 캠페인 불러오기"), ("keywordSuggest", "연관키워드 검색"), ("directSend", "문자·메일 직접 발송"),
         ("photoManage", "리뷰 사진 관리·내려받기"), ("searchReport", "검색결과 리포트"), ("autoSend", "자동발송 설정"),
         ("resultExcel", "캠페인 결과 엑셀 다운"), ("videoRequest", "영상 제작 요청"), ("rerecruitRequest", "추가모집 요청"),
         ("sendNumber", "발신번호 관리")]
LIMITS = [("캠페인당 모집인원", "명"), ("한 달 등록 캠페인 수", "개"), ("동시 진행 캠페인 수", "개")]
ADD_LIMITS = [("관리 업체 수", "곳"), ("직원 수", "명")]
# [2026-11-10] 등급 = 실서버 advertiserGrade seed(_sql\advertiserGrade.sql · advFeature.sql)
#   (키, 이름, 월 요금 — None = 운영 DB 값(seed 0 = 판매 안 함), 한도 — None = 비어 있음(=무제한), 기능, 승급 조건 완료 건수, 유료)
#   seed 는 추가모집 요청(rerecruitRequest)만 빼고 모든 등급에 기능을 다 연다 — 등급별로 나누는 것은 DB 값
SEED_FEATS = [f for f, _l in FEATS if f != "rerecruitRequest"]
GRADES = [("bronze", "브론즈", 0, None, SEED_FEATS, 0, False), ("silver", "실버", 0, None, SEED_FEATS, 5, False),
          ("gold", "골드", 0, None, SEED_FEATS, 20, False), ("platinum", "플래티넘", None, None, SEED_FEATS, 50, True),
          ("vip", "VIP", None, None, SEED_FEATS, 100, True)]
CUR_GRADE = "bronze"
MONTHS = [1, 3, 6, 12]                            # 광고주 $ppMonths — 기간 할인 없음(월 비용 × 개월)
SKINS = ["standard", "deluxe", "premium"]


def lim_text(lims, i, unit):
    """광고주 ppLimitText — 0/없음 = 무제한"""
    v = lims[i] if lims else 0
    return "무제한" if not v else f"{v:,}{unit}"


def add_lim_text(lims, i):
    v = lims[3 + i] if lims and len(lims) > 3 else None
    return "운영 DB 값" if v is None else ("무제한" if v == 0 else f"{v:,}{ADD_LIMITS[i][1]}")


def plan_card(idx, g):
    key, name, fee, lims, feats, _done, _paid = g
    li = lambda icon, t, cls="": f'<li{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}><span class="material-symbols-outlined">{icon}</span>{t}</li>'  # noqa: E731
    items = (li("group", f'캠페인당 모집인원 <strong class="color-blue">{lim_text(lims, 0, "명")}</strong>')
             + li("campaign", f'한 달 등록 <strong class="color-blue">{lim_text(lims, 1, "개")}</strong>')
             + li("dashboard", f'동시 진행 <strong class="color-blue">{lim_text(lims, 2, "개")}</strong>')
             + li("storefront", f'관리 업체 수 <strong class="color-blue">{add_lim_text(lims, 0)}</strong>{tag()}', "add")
             + li("badge", f'직원 수 <strong class="color-blue">{add_lim_text(lims, 1)}</strong>{tag()}', "add"))
    labs = [lab for code, lab in FEATS if code in feats]
    items += "".join(f'<li><span class="material-symbols-outlined color-blue">check_circle</span>{x}</li>' for x in labs[:3])
    if len(labs) > 3:
        items += (f'<li><span class="material-symbols-outlined color-blue">more_horiz</span>그 외 '
                  f'<strong class="color-blue">{len(labs) - 3}개</strong> 기능</li>')
    price = "—" if fee is None else num(fee)
    return (f'<div class="plan-card"><div class="plan-card-badge target">등급 혜택 안내는 1:1 문의로 요청해 주세요.</div>'
            f'<div class="plan-card-inner"><div class="plan-badge {SKINS[idx % 3]}">{key}</div><h3 class="plan-name">{name}</h3>'
            f'<ul class="plan-features">{items}</ul><div class="plan-duration">사용기간 <span class="gp-month-text">1</span>개월</div>'
            f'<div class="plan-price"><strong class="gp-total" data-fee="0">{price}</strong> 원 <span class="vat">(VAT 포함)</span>'
            f'<p class="gp-permonth">월 {price}원</p><p class="gp-permonth add">{tag()} 대행사 금액은 운영 DB 값(Q3 결정 대기)</p></div>'
            + flash("이 등급으로 결제", f"시안: {name} 카드 결제창으로 이동합니다", "btn-plan-select") + "</div></div>")


def compare_table():
    cell = lambda nm, v: f'<div class="pct-cell" data-label="{nm}">{v}</div>'  # noqa: E731
    cat = lambda t: f'<div class="pct-row pct-category"><div class="pct-cell-full">{t}</div></div>'  # noqa: E731
    rows = ['<div class="pct-row pct-header"><div class="pct-cell pct-title">구분</div>'
            + "".join(f'<div class="pct-cell">{g[1]}</div>' for g in GRADES) + "</div>", cat("이용 요금"),
            '<div class="pct-row"><div class="pct-cell pct-title">월 비용</div>'
            + "".join(cell(g[1], "준비중" if g[6] else "무료") for g in GRADES) + "</div>", cat("한도")]
    for i, (lab, unit) in enumerate(LIMITS):
        rows.append(f'<div class="pct-row"><div class="pct-cell pct-title">{lab}</div>'
                    + "".join(cell(g[1], lim_text(g[3], i, unit)) for g in GRADES) + "</div>")
    for i, (lab, _unit) in enumerate(ADD_LIMITS):
        rows.append(f'<div class="pct-row add"><div class="pct-cell pct-title">{lab}{tag()}</div>'
                    + "".join(cell(g[1], add_lim_text(g[3], i)) for g in GRADES) + "</div>")
    rows.append(cat("기능"))
    for code, lab in FEATS:
        rows.append(f'<div class="pct-row"><div class="pct-cell pct-title">{lab}</div>' + "".join(
            cell(g[1], '<span class="material-symbols-outlined color-blue">check</span>' if code in g[4] else '<span class="gp-mute">-</span>')
            for g in GRADES) + "</div>")
    return ('<div class="plan-compare-section"><div class="plan-compare-header"><span>등급별 한도 · 기능</span></div>'
            f'<div class="plan-compare-table">{"".join(rows)}</div><div class="plan-compare-footer"><span class="text-mute">'
            "* 한도의 '무제한' 은 등급에 상한을 두지 않았다는 뜻입니다. 포인트 등 다른 조건은 별도로 적용됩니다.</span></div></div>")


def view_purchase():
    status = ('<div class="gp-status"><div class="gp-status-item"><span class="gp-status-label">현재 등급</span>'
              f'<strong class="gp-status-value">{dict((g[0], g[1]) for g in GRADES)[CUR_GRADE]}</strong></div>'
              '<div class="gp-status-item"><span class="gp-status-label">이용 기간</span>'
              '<strong class="gp-status-value gp-mute">이용 중인 유료등급이 없습니다</strong></div></div>')
    months = ('<div class="gp-section"><h3 class="gp-section-title"><span class="gp-step-num">1</span> 이용 기간 선택</h3><div class="gp-month-grid">'
              + "".join(f'<label class="gp-month-card"><input type="radio" name="gpMonths" value="{m}"{" checked" if m == 1 else ""}>'
                        f'<span class="gp-mc-inner"><strong>{m}</strong>개월</span></label>' for m in MONTHS)
              + '</div><p class="gp-month-note">* 이용 기간이 남아 있을 때 같은 등급을 결제하면 남은 기간에 이어서 더해집니다.</p></div>')
    paid = [g for g in GRADES if g[6]]
    cards = ('<div class="gp-section"><h3 class="gp-section-title"><span class="gp-step-num">2</span> 등급 선택 후 결제</h3>'
             f'<div class="plan-cards-container">{"".join(plan_card(i, g) for i, g in enumerate(paid))}</div></div>')
    notice = ('<div class="plan-notice"><h4>유의사항</h4><ul><li>표시된 금액이 <strong>실제 결제 금액</strong>입니다. (부가세 포함)</li>'
              '<li>결제가 완료되면 등급이 <strong>즉시</strong> 적용됩니다.</li><li>이용 기간이 남아 있을 때 같은 등급을 결제하면 남은 기간에 이어서 더해집니다.</li>'
              '<li>이용 기간이 끝나면 기본 등급으로 조정되며, 그 등급의 한도·기능이 적용됩니다.</li>'
              '<li>결제 수단은 <strong>신용카드</strong>만 지원합니다.</li><li>환불·등급 변경은 1:1 문의로 요청해 주세요.</li>'
              f'<li class="add">사용료는 대행사 하나에 매깁니다(업체마다 아님).{tag()}</li></ul></div>')
    return ('<div class="plan-view-section active view-plan-purchase v9p"><div class="plan-header text-center"><h2 class="plan-title">유료등급 이용권</h2>'
            '<p class="plan-desc">등급을 올리면 캠페인 한도와 기능이 함께 열립니다.<br>결제가 완료되면 즉시 적용됩니다.</p></div>'
            + status + months + cards + notice + compare_table() + "</div>")


def view_history():
    trs = ('<tr><td data-label="번호">1</td><td data-label="등급"><span class="badge-plan standard">플래티넘</span></td>'
           f'<td data-label="결제일시">{dt(-3, "11:20")}</td><td data-label="결제수단">신용카드</td>'
           '<td data-label="결제금액"><span><strong>0</strong>원</span></td><td data-label="이용기간">1개월</td>'
           '<td data-label="만료일">-</td><td data-label="상태">결제실패</td><td data-label="영수증"><span class="gp-mute">-</span></td></tr>')
    heads = "".join(f"<th>{h}</th>" for h in ["번호", "등급", "결제일시", "결제수단", "결제금액", "이용기간", "만료일", "상태", "영수증"])
    return ('<div class="plan-view-section view-plan-history v9p"><h3 class="ph-title">내 결제내역 목록</h3><div class="ph-table-wrap">'
            f'<table class="ph-table"><thead><tr>{heads}</tr></thead><tbody>{trs}</tbody></table></div>'
            '<p class="ph-note">* 결제·환불 관련 문의는 1:1 문의로 남겨 주세요. 주문번호를 함께 적어 주시면 빠르게 확인할 수 있습니다.</p></div>')


def plan_page():
    radios, bar = tab_bar("plt", [("구매하기", False), ("결제내역", False)], bar="cmp-top-tabs plan-tabs")
    body = (f'<div class="cmp-layout plan-layout v9t">{radios}{bar}<div class="cmp-page-card plan-page-card">'
            + view_purchase() + view_history() + "</div></div>")
    write("plan.html", "사용료", "plan", body)


# ════════════════ 3. 문자설정(sms.html) ← messageSettingTabs · verifyIdentity · autoSend · sendNumber ════════════════
# [2026-11-10] 단가 = 실서버 advPrice 기본값(문자 단문 20P · 장문 50P · 알림톡 15P · 메일 무료)
SMS_SHORT, SMS_LONG, ALIM = 20, 50, 15
# 상황 · 설명 · 시점 · 항상 발송 = 실서버 autoSend.class.php $TRIGGER, 기본 문구 = _sql\autoSend_seed*.sql
AUTO = [("선정 안내", "리뷰어를 선정하는 순간, 선정됐다고 알립니다. 비용은 뷰마이 부담하며 항상 나갑니다.", "선정 확정 즉시", True,
         "[{업체명}] {닉네임}님, {캠페인명} 체험단에 선정되셨습니다. 자세한 내용은 뷰마에서 확인해 주세요."),
        ("미선정 안내", "아쉽게 선정되지 않은 분께 알립니다. 다음 캠페인 참여로 이어집니다.", "캠페인 시작일 (매일 오전)", False,
         "[{업체명}] {닉네임}님, {캠페인명} 선정 결과 아쉽게 이번에는 모시지 못했습니다. 다음 기회에 뵙겠습니다."),
        ("방문 하루 전 안내", "방문형 캠페인에서 약속한 방문일 하루 전에 알려 노쇼를 줄입니다.", "방문일 1일 전 (매일 오전)", False,
         "[{업체명}] {닉네임}님, 내일({방문일}) 방문 예정입니다. 일정 확인 부탁드립니다."),
        ("리뷰 마감 임박 안내", "리뷰 마감 3일 전에 알립니다. 미등록 패널티를 줄이는 데 가장 효과가 큽니다.", "리뷰 마감일 3일 전 (매일 오전)", False,
         "[{업체명}] {닉네임}님, {캠페인명} 리뷰 마감일이 {마감일}입니다. 등록 부탁드립니다."),
        ("리뷰 미등록 안내", "마감이 지났는데 리뷰가 없는 분께 알립니다.", "리뷰 마감일 다음날 (매일 오전)", False,
         "[{업체명}] {닉네임}님, {캠페인명} 리뷰가 아직 등록되지 않았습니다. 확인 부탁드립니다."),
        ("리뷰 감사 인사", "리뷰가 승인되면 감사 인사를 보냅니다. 재참여로 이어집니다.", "리뷰 검수 승인 즉시", False,
         "[{업체명}] {닉네임}님, {캠페인명} 리뷰 감사합니다. 다음에도 좋은 기회로 뵙겠습니다."),
        ("영상 제작 완료", "운영자가 영상을 올리면 리뷰어에게는 내려받아 올려 달라고, 광고주에게는 등록이 끝났다고 알립니다. 비용은 뷰마이 부담하며 항상 나갑니다.",
         "운영자가 영상을 올린 즉시", True,
         "[뷰마] 요청하신 {영상종류} 영상 제작이 완료되었습니다. 영상 제작 요청 화면에서 내려받으실 수 있습니다."),
        ("리뷰등록 연장 신청", "리뷰어가 리뷰등록기간 연장을 요청하면 광고주에게 알립니다.", "연장 요청 즉시", False,
         "[뷰마] {캠페인명}에서 {닉네임}님이 리뷰등록 기간 연장을 요청했습니다. 리뷰어 관리에서 처리해 주세요."),
        ("리뷰등록 연장 완료", "리뷰등록기간이 연장되면 알립니다. 광고주가 연장하면 리뷰어에게만(광고주 부담), 운영자가 연장하면 리뷰어·광고주 양쪽에(뷰마 부담) 나갑니다.",
         "연장 승인 즉시", False,
         "[뷰마] {닉네임}님, {캠페인명} 리뷰등록 기간이 {연장마감일}까지 연장되었습니다. 기한 내 등록 부탁드립니다.")]
AUTO_ON = (3, 4, 5)


def hour_text(h):
    return f"오전 {h}시" if h < 12 else ("낮 12시" if h == 12 else f"오후 {h - 12}시")


def pane_verify():
    """verifyIdentity.inc.html — reason=autoSend · 인증 전(사후인증 필요) 상태"""
    return ('<div class="viWrap viWrap--tabbed v9p"><div class="viCard"><div class="viIcon"><span class="material-symbols-outlined">verified_user</span></div>'
            '<h2 class="viTitle">자동문자 사후인증이 필요합니다</h2><p class="viDesc">캠페인 자동 알림(선정 안내 등)이 자동으로 발송되었습니다.<br>'
            '전송자격인증제에 따라 <b>72시간 안에</b> 휴대폰 본인인증을 마치고,<br>아래에서 발송 내역을 확인해 승인해 주세요.<br>'
            '기한을 넘기면 승인 전까지 다른 화면을 이용할 수 없습니다.</p><ul class="viList">'
            '<li>본인인증을 마치면 이 화면에 발송 내역이 뜨고, 건을 체크해 승인합니다.</li>'
            '<li>이미 계정 인증을 마친 경우에도, 자동발송이 있었으면 다시 인증해야 합니다.</li></ul>'
            f'<p class="viMeta">자동발송 12건 · 최초 발생 {P.d_of(-1):%Y-%m-%d} 10:00</p>'
            + flash("휴대폰 본인인증 시작", "시안: 휴대폰 본인인증 창", "viBtn js-verify-start")
            + f'<p class="viNote"></p><p class="viDesc add" style="margin:14px 0 0;">{tag()} 인증은 대행사 하나에 1번 — 업체마다 하지 않습니다. '
            '인증한 직원 이름이 기록됩니다.</p></div></div>')


def auto_row(i, sit, desc, when, fixed, text):
    if fixed:
        use = '<span class="ri-badge" style="font-size:12px;color:#d46b08;">항상 발송</span>'
        base = ('<div class="ri-muted" style="line-height:1.7;margin-bottom:8px;padding:8px 10px;background:#fff7e6;border-radius:6px;">'
                '<b>뷰마이 비용을 부담합니다.</b> 이 안내는 모든 캠페인에서 나갑니다.<br>기준은 <b>기본 안내</b>(알림톡)입니다. '
                '이보다 <b>비싼 수단</b>으로 바꾸시면 그 발송 비용은 <b>광고주님 부담</b>이며, 바꾸실 때 금액을 알려 드립니다.</div>')
    else:
        on = i in AUTO_ON
        use = (f'<label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;"><input type="checkbox" class="js-au-use"'
               f'{" checked" if on else ""} aria-label="{sit} 사용"><span style="font-size:13px;">{"사용" if on else "안 함"}</span></label>')
        base = ""
    sel = ('<select class="cmp-select js-au-tpl" style="width:100%;" aria-label="보낼 문구"><option value="0">기본 문구 (운영자 지정)</option>'
           '<optgroup label="문자"><option>정중한 안내</option><option>짧게</option></optgroup>'
           '<optgroup label="메일 (무료)"><option>기본 안내</option></optgroup></select>')
    return (f'<tr><td class="ri-col-center">{use}</td><td><span class="ri-camp__name">{sit}</span><span class="ri-camp__code">{when}</span>'
            f'<div class="ri-muted" style="font-size:12px;margin-top:4px;">{desc}</div></td>'
            f'<td>{base}{sel}<div class="ri-muted js-au-preview" style="font-size:12px;margin-top:6px;white-space:pre-wrap;line-height:1.6;">{esc(text)}</div>'
            '<div class="ri-muted" style="font-size:12px;margin-top:4px;">고를 수 있는 문구 3개</div></td></tr>')


def pane_auto():
    hours = "".join(f'<option value="{h}"{" selected" if h == 10 else ""}>{hour_text(h)}</option>' for h in range(8, 22))
    return ('<div class="cmp-page-card v9p"><div class="cmp-page-header">'
            f'<h2 class="cmp-page-title">{AGENCY}님의 자동발송 설정</h2></div>'
            '<div class="ri-filter" style="flex-wrap:wrap;gap:14px;">'
            f'<span class="ri-filter__hint">문자 <b>{SMS_SHORT}P</b> (장문 {SMS_LONG}P)</span><span class="ri-filter__hint">알림톡 <b>{ALIM}P</b></span>'
            '<span class="ri-filter__hint">메일 <b>무료</b></span>'
            f'<span class="ri-filter__hint" style="margin-left:auto;">보유 포인트 <b>{num(D.BALANCE)}P</b></span></div>'
            '<div class="ri-filter" style="align-items:center;gap:10px;margin-bottom:14px;padding:12px 14px;background:#f7f7f8;border-radius:8px;">'
            '<span style="font-size:14px;font-weight:600;">발송 시각</span>'
            f'<select class="cmp-select" id="auHour" style="width:150px;" aria-label="발송 시각">{hours}</select>'
            '<span class="ri-filter__hint">날짜로 정해지는 안내(미선정·방문·리뷰마감)가 이 시각에 나갑니다. <b>선정·리뷰 감사</b>는 그 순간 바로 나갑니다.</span></div>'
            '<p class="ri-modal-notice" style="margin:0 0 18px;">※ 켜 두시면 해당 상황이 올 때 <b>자동으로</b> 나갑니다. 문자·알림톡은 보낸 만큼 포인트가 차감되고, '
            '메일은 무료입니다.<br>※ 같은 사람에게 <b>같은 상황으로 두 번 보내지 않습니다.</b><br>※ 문구를 고르시면 <b>보내는 수단(문자·메일)도 함께 정해집니다.</b></p>'
            f'<p class="ri-modal-notice add" style="margin:0 0 18px;">{tag()} 문구의 <code>{{업체명}}</code>은 캠페인 업체 이름으로 바뀝니다 — '
            '리뷰어에게는 업체 이름으로 보입니다. 1차는 설정이 대행사 하나(Q15) · 업체마다 다른 문구는 2차.</p>'
            '<div class="ri-table-wrap"><table class="ri-table"><thead><tr><th style="width:90px;">사용</th><th style="width:38%;">상황</th>'
            '<th>보낼 문구</th></tr></thead><tbody>' + "".join(auto_row(i, *a) for i, a in enumerate(AUTO)) + "</tbody></table></div></div>")


SENDERS = [(True, "대표번호", "이정민", "계정 본인인증 정보", "02-***-1234", "회사", -60, "Y", ""),
           (False, "1팀 김지은", "김지은", "변경 불가", "010-****-5678", "본인", -21, "Y", ""),
           (False, "2팀 업무폰", "", "", "010-****-9012", "타인", -2, "W", ""),
           (False, "옛 번호", "", "", "031-***-3456", "본인", -90, "R", "통신서비스 이용증명원의 명의가 신청자와 다릅니다.")]
SN_ST = {"Y": ("snTag--ok", "등록완료"), "W": ("snTag--wait", "심사중"), "R": ("snTag--bad", "반려")}
SN_TYPES = [("본인 (휴대폰인증)", "내 명의의 휴대전화를 발신번호로 씁니다."), ("본인 (일반전화)", "내 명의의 유선전화를 발신번호로 씁니다."),
            ("타인 (휴대전화)", "다른 사람 명의의 휴대전화를 발신번호로 씁니다."), ("타인 (일반전화)", "다른 사람 명의의 유선전화를 발신번호로 씁니다."),
            ("회사 (모든전화)", "법인·사업자 명의의 전화를 발신번호로 씁니다.")]


def pane_sender():
    trs = []
    for main, nick, real, real_src, number, own, off, st, rej in SENDERS:
        tcls, ttxt = SN_ST[st]
        name = (f"<strong>{esc(nick)}</strong>" + (' <span class="snTag snTag--main">대표</span>' if main else "")
                + (f'<p class="snReject">반려 사유 : {rej} ({P.d_of(off + 1):%Y-%m-%d})</p>' if rej else ""))
        realc = f'{real}<p class="snDocHint" style="margin:2px 0 0;">{real_src}</p>' if real else '<span style="color:#0e0e0e;">-</span>'
        acts = (flash("재제출", "시안: 서류를 다시 제출합니다", "pm-detail-btn") if st == "R" else "") + \
            '<button type="button" class="pm-detail-btn" popovertarget="snRenameModal">이름변경</button>' + \
            flash("삭제", f"시안: {number} 를 삭제합니다", "pm-detail-btn")
        trs.append(f'<tr><td data-label="대표" style="text-align:center;"><input type="radio" name="snMainPick"{" checked" if main else ""}'
                   f'{"" if st == "Y" else " disabled"} aria-label="대표 지정"></td><td data-label="발신번호명(별명)">{name}</td>'
                   f'<td data-label="실명">{realc}</td><td data-label="번호">{number}</td><td data-label="명의">{own}</td>'
                   f'<td data-label="등록일">{P.d_of(off):%Y-%m-%d} 10:20</td><td data-label="상태"><span class="snTag {tcls}">{ttxt}</span></td>'
                   f'<td data-label="관리"><div class="snRowActions">{acts}</div></td></tr>')
    widths = [("대표", 70), ("발신번호명(별명)", 160), ("실명", 110), ("번호", 140), ("명의", 80), ("등록일", 180), ("상태", 100), ("관리", 230)]
    heads = "".join(f'<th style="width:{w}px;">{h}</th>' for h, w in widths)
    help_ = ('<div class="snHelp"><h4>발신번호 등록 안내</h4><ul><li><strong>본인 휴대전화</strong>는 휴대폰 본인인증만 하면 바로 등록됩니다. 서류가 필요 없습니다.</li>'
             '<li>그 밖의 번호는 <strong>통신서비스 이용증명원</strong> 등 서류 심사를 거칩니다 (평일 09:00~18:00, 보통 1~2일).</li>'
             '<li>어느 경우든 <strong>등록하시는 분의 휴대폰 본인인증</strong>이 필요합니다 — 누가 등록했는지가 기록되어야 하기 때문입니다.</li>'
             '<li>대표로 지정한 번호가 문자 보낼 때 기본으로 선택됩니다.</li>'
             f'<li class="add">발신번호는 대행사 하나에 등록 — 직원 누구나 등록된 번호로 보낼 수 있습니다(업체별 번호는 2차).{tag()}</li></ul></div>')
    return ('<div class="cmp-page-card v9p"><div class="pm-header text-center"><h2 class="pm-title">발신번호 관리</h2>'
            '<p class="pm-desc">리뷰어에게 문자를 보낼 때 표시될 번호입니다. <strong>등록·승인된 번호로만</strong> 보낼 수 있습니다.</p></div>'
            f'<div class="snBar"><span>등록된 번호 <strong>{len(SENDERS)}</strong>개</span>'
            '<button type="button" class="btn btn-primary" popovertarget="snAddModal">발신번호 추가</button></div>'
            f'<div class="snTableWrap"><table class="pm-table pm-table--sendnumber"><thead><tr>{heads}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
            + help_ + "</div>")


def sender_modals():
    types = "".join(flash(f"<strong>{lab}</strong><span>{d}</span>", f"시안: {lab} — 번호·본인인증·서류 단계로 넘어갑니다", "snTypeItem")
                    for lab, d in SN_TYPES)
    add_body = ('<div id="snStep1"><p style="margin:0 0 12px;font-size:13px;color:#0e0e0e;line-height:1.7;">등록할 번호가 <strong>누구 명의</strong>인지 '
                f'골라 주세요. 명의에 따라 필요한 서류가 다릅니다.</p><div class="snTypeList">{types}</div></div>')
    add = modal("snAddModal", "발신번호 추가", add_body, hide_btn("snAddModal", "취소", "btn btn-cancel"), "rev-msg-modal", "rev-msg-content")
    ren_body = ('<label class="form-label" for="snRenameName">발신번호명 (별명)</label>'
                '<input type="text" class="rev-msg-input" name="name" id="snRenameName" maxlength="30">'
                '<p class="snDocHint">목록에서 구분하려고 붙이는 이름입니다.<br><strong>명의자 이름과 전화번호는 바뀌지 않습니다</strong> — '
                '인증으로 확정된 값이라 고칠 수 없습니다.</p>')
    ren = modal("snRenameModal", "발신번호명(별명) 변경", ren_body,
                hide_btn("snRenameModal", "취소", "btn btn-cancel") + flash("저장", "시안: 별명을 바꿨습니다", "btn btn-primary"),
                "rev-msg-modal", "rev-msg-content")
    return add + ren


def sms_page():
    radios, bar = tab_bar("mst", [("자동문자 사후인증", False), ("자동발송 설정", False), ("발신번호 관리", False)],
                          extra=f'<a class="cmp-tab-btn add" href="messages.html">문자·메일 발송함{tag("광고주는 메뉴")}</a>')
    body = (f'<div class="cmp-layout v9t">{radios}{bar}' + pane_verify() + pane_auto() + pane_sender() + "</div>" + sender_modals())
    write("sms.html", "문자설정", "sms", body)


# ════════════════ 4. 패널티(penalty.html) ← penalty.inc.html ════════════════
# [2026-11-10] 실서버 penaltyRule — 광고주 사유는 "모집완료 후 캠페인 숨김/취소" 2점(자동) 하나.
#   광고주 누적 기준은 seed 없음(DB 값) → 구간은 리뷰어 seed(fix_penaltyThreshold_20261029: 20 · 30 · 50점)를 빌려 표시
#   (점수, 제한 일수(-1 = 영구), 설명)
RULES = [(20, 7, "7일간 새 캠페인 등록 제한"), (30, 30, "30일간 새 캠페인 등록 제한"), (50, -1, "영구 이용 제한")]
PEN_REASON = [("모집완료 후 캠페인 숨김/취소", "리뷰어가 신청·선정된 캠페인을 모집완료 이후 숨김/취소", 2),
              ("모집완료 후 캠페인 숨김/취소", "리뷰어가 신청·선정된 캠페인을 모집완료 이후 숨김/취소", 2),
              ("관리자 차감", "소명 확인 — 업체 폐업으로 인한 취소", -2),
              ("모집완료 후 캠페인 숨김/취소", "리뷰어가 신청·선정된 캠페인을 모집완료 이후 숨김/취소", 2)]


def restrict_text(days):
    return "영구 제한" if days < 0 else ("제한 없음" if days == 0 else f"{days:,}일 신청 제한")


def pen_rows():
    r = random.Random("acc-pen")
    out = []
    for i, (kind, why, pt) in enumerate(PEN_REASON):
        c = r.choice([x for x in D.CAMPS if x["dts"]])
        out.append((kind, why, c, pt, -r.randint(3, 80), i != 1))
    out.sort(key=lambda x: x[4], reverse=True)
    return out


def penalty_page():
    rows = pen_rows()
    total = max(0, sum(pt for *_x, pt, _o, on in rows if on))
    nxt = next(((p, d) for p, d, _t in RULES if p > total), None)
    hot = total > 0
    th = 'style="padding:10px 8px;'
    band = (f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;border-radius:10px;padding:16px 20px;margin-bottom:20px;'
            f'{"background:#fff4f4;border:1px solid #ffd4d4;" if hot else "background:#f5f7fa;border:1px solid #e5e7eb;"}">'
            f'<span style="font-size:14px;font-weight:600;{"color:#c0392b;" if hot else "color:#0e0e0e;"}">'
            f'{"현재 적용 중인 패널티가 있습니다." if hot else "현재 적용 중인 패널티가 없습니다."}</span>'
            f'<span style="font-size:15px;font-weight:800;{"color:#c0392b;" if hot else "color:#0e0e0e;"}">누적 패널티 {total}점</span></div>')
    rule_trs = ""
    for p, days, desc in RULES:
        hit = total >= p
        col = "color:#c0392b;" if hit else "color:#3a3a3c;"
        mark = ('<span style="display:inline-block;padding:3px 8px;border-radius:20px;background:#c0392b;color:#fff;font-size:11px;font-weight:700;">해당</span>'
                if hit else '<span style="color:#0e0e0e;">-</span>')
        rule_trs += (f'<tr style="border-bottom:1px solid #f4f4f6;{"background:#fff4f4;" if hit else ""}">'
                     f'<td style="padding:12px 8px;font-weight:700;{col}">{p:,}점 이상</td>'
                     f'<td style="padding:12px 8px;line-height:1.7;"><span style="font-weight:600;{col}">{restrict_text(days)}</span>'
                     f'<br><span style="color:#0e0e0e;">{desc}</span></td><td style="padding:12px 8px;text-align:center;">{mark}</td></tr>')
    gap = (f'<p style="margin:14px 0 0;padding:12px 14px;background:#f5f7fa;border-radius:8px;font-size:13px;line-height:1.7;color:#0e0e0e;">'
           f'현재 누적 <strong>{total}점</strong> 입니다. <strong>{nxt[0] - total:,}점</strong> 이 더 쌓이면 <strong>{restrict_text(nxt[1])}</strong> 가 적용됩니다.</p>'
           if nxt else "")
    rules = ('<div style="border-top:1px solid #ececf0;padding:20px 0 0;margin-bottom:20px;">'
             '<h3 style="font-size:16px;font-weight:700;margin:0 0 4px;">패널티 점수별 제재 기준</h3>'
             '<p style="font-size:13px;color:#0e0e0e;line-height:1.6;margin:0 0 14px;">누적 패널티가 아래 점수에 도달하면 해당 제재가 적용됩니다. '
             '제재 기간은 <strong>가장 최근 패널티 부과일</strong>부터 계산됩니다.</p>'
             '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;"><thead>'
             f'<tr style="text-align:left;color:#0e0e0e;border-bottom:1px solid #ececf0;"><th {th}width:110px;">누적 점수</th>'
             f'<th {th}">제재 내용</th><th {th}text-align:center;width:90px;">현재</th></tr></thead><tbody>{rule_trs}</tbody></table></div>'
             + gap + '<p class="add" style="margin:10px 0 0;font-size:12px;color:#0e0e0e;">' + tag("시안")
             + ' 광고주 누적 기준은 운영 DB 값(seed 없음) — 점수 구간은 리뷰어 기준(20 · 30 · 50점)을 빌려 보여 줍니다.</p></div>')
    trs = ""
    for kind, why, c, pt, off, on in rows:
        minus = pt < 0
        td = 'style="padding:10px 8px;'
        trs += (f'<tr data-biz="{c["bid"]}" style="border-bottom:1px solid #f4f4f6;{"" if on else "opacity:.45;"}">'
                f'<td {td}font-weight:600;">{kind}</td><td {td}color:#0e0e0e;">{why}</td>'
                f'<td class="col-biz add" {td}color:#0e0e0e;">{K.biz_cell(c["b"])}</td>'
                f'<td {td}color:#0e0e0e;">{camp_link(c)}</td>'
                f'<td {td}text-align:center;font-weight:700;{"color:#2563eb;" if minus else ""}">{"" if minus else "+"}{pt}점</td>'
                f'<td {td}color:#0e0e0e;">{P.d_of(off):%y.%m.%d}</td><td {td}text-align:center;">'
                + ('<span style="color:#c0392b;font-weight:600;">적용중</span>' if on else '<span style="color:#0e0e0e;">취소됨</span>') + "</td></tr>")
    mine = ('<div style="border-top:1px solid #ececf0;padding:20px 0 0;"><h3 style="font-size:16px;font-weight:700;margin:0 0 12px;">나에게 부여된 패널티</h3>'
            '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;"><thead>'
            f'<tr style="text-align:left;color:#0e0e0e;border-bottom:1px solid #ececf0;"><th {th}">구분</th><th {th}">사유</th>'
            f'<th class="col-biz add" {th}">업체{tag()}</th><th {th}">캠페인</th><th {th}text-align:center;">점수</th><th {th}">부과일</th>'
            f'<th {th}text-align:center;">상태</th></tr></thead><tbody>{trs}</tbody></table></div></div>')
    body = ('<div class="page-container"><div class="pn-page"><h2 style="font-size:22px;font-weight:800;margin:0 0 4px;">패널티</h2>'
            '<p style="font-size:13px;color:#0e0e0e;line-height:1.6;margin-bottom:20px;">· 아래 목록은 운영자가 나에게 부여하거나 차감·취소한 패널티 내역입니다.<br>'
            '· 패널티 점수가 변동되면 알림으로 안내되며, 취소된 내역도 기록으로 함께 남습니다.</p>'
            f'<p class="add" style="font-size:13px;color:#0e0e0e;line-height:1.6;margin:-8px 0 20px;">{tag()} 패널티는 대행사에 쌓입니다(Q16 확인 필요) — '
            '어느 업체 캠페인에서 생겼는지 업체 칸으로 보입니다.</p>'
            + band + rules + mine + "</div></div>")
    write("penalty.html", "패널티", "pen", body)


# ════════════════ 5. 대행사 정보(info.html) ← mypage.inc.html + profile.inc.html ════════════════
# 로고 자리 — 이미지 파일이 없어 글자 한 자 그림(data URI)으로
LOGO = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Crect width='80' height='80' fill='%23f0edff'/%3E"
        "%3Ctext x='40' y='52' font-size='36' font-weight='700' text-anchor='middle' fill='%237346f3' font-family='sans-serif'%3EA%3C/text%3E%3C/svg%3E")


def info_row(k, v):
    return f'<dl class="mp-info-row"><dt>{k}</dt><dd>{v}</dd></dl>'


def sec_agency():
    """내정보 섹션 → 대행사 정보(이름만 바꿈) · 프로필 사진 자리 = 대행사 로고"""
    rows = [("담당자명", "이정민"), ("닉네임", "애니라인"), ("이메일", "contact@anyline.kr"), ("전화번호", "010-****-1234"),
            ("상호명", AGENCY), ("대표자명", "이정민"), ("사업자번호", "123-45-*****"),
            ("플레이스 / 오픈마켓", '<span class="add">업체마다 — <a href="biz.html">업체 화면</a>에서 등록' + tag() + "</span>"),
            ("주소", "04524 서울시 ○○구 ○○로 00, 0층(더미)")]
    return ('<section class="mp-section" id="s-info"><div class="mp-section-header"><span class="material-symbols-outlined icon-mid">account_box</span>'
            '<h3 class="mp-section-title">대행사 정보</h3></div><div class="mp-profile-top"><div class="mp-avatar-wrap">'
            f'<img src="{LOGO}" alt="대행사 로고" class="mp-avatar-img" id="previewImage">'
            '<label class="mp-btn-camera"><span class="material-symbols-outlined">camera_alt</span>'
            '<input type="file" accept="image/*" name="advertiserPhoto" hidden></label></div>'
            f'<div class="mp-profile-greet"><strong>{AGENCY}님</strong> 안녕하세요!'
            f'<p class="add" style="margin:4px 0 0;font-size:12px;font-weight:400;">{tag()} 사진 = 대행사 로고 — 보고서 공개 화면 머리에 나옵니다</p></div></div>'
            '<div class="mp-banner-grid"><div class="mp-mini-banner plan"><div class="banner-top"><div class="banner-label">이용 중인 플랜</div>'
            '<div class="banner-value">브론즈</div></div><div class="banner-bottom"><div class="banner-label">만료일 없음 · 무료 플랜</div>'
            '<a class="banner-btn" href="plan.html"><span class="material-symbols-outlined">update</span> 플랜 보기</a></div></div>'
            '<div class="mp-mini-banner point"><div class="banner-top"><div class="banner-label">나의 보유 포인트</div>'
            f'<div class="banner-value" id="mpBalanceText">{num(D.BALANCE)} P</div></div><div class="banner-bottom">'
            '<a class="banner-btn" href="point.html"><span class="material-symbols-outlined">add_circle</span> 포인트 충전</a></div></div></div>'
            '<div class="mp-info-list">' + "".join(info_row(k, v) for k, v in rows) + "</div>"
            '<div class="mp-action-wrap"><button type="button" class="mp-btn-edit" popovertarget="profileEditModal">'
            '<span class="material-symbols-outlined">edit</span> 내정보 수정</button>'
            '<button type="button" class="mp-btn-edit" popovertarget="profileEditModal">'
            '<span class="material-symbols-outlined">lock_reset</span> 비밀번호 변경</button></div></section>')


def sec_me():
    """[대행사 추가] 직원 개인 로그인 계정"""
    noti = ('<label class="p-tag-label"><input type="checkbox" checked><span>메일</span></label>'
            '<label class="p-tag-label"><input type="checkbox" checked><span>문자</span></label>'
            '<label class="p-tag-label"><input type="checkbox"><span>알림톡</span></label>')
    rows = [("이름", "김지은"), ("역할", "팀장 · 1팀"), ("이메일", "jieun@anyline.kr"), ("전화번호", "010-****-5678"),
            ("알림 수신", f'<div class="p-tag-list">{noti}</div><span style="color:#777;font-size:13px;">담당 업체 이슈만</span>')]
    return ('<section class="mp-section add" id="s-me"><div class="mp-section-header"><span class="material-symbols-outlined icon-mid">badge</span>'
            f'<h3 class="mp-section-title">내 계정{tag()}</h3></div>'
            '<div style="padding:0 0 8px;font-size:13px;color:#777;">직원 개인 로그인 계정 — 위 대행사 정보는 모든 직원이 함께 봅니다.</div>'
            '<div class="mp-info-list">' + "".join(info_row(k, v) for k, v in rows) + "</div>"
            '<div class="mp-action-wrap">' + flash('<span class="material-symbols-outlined">lock_reset</span> 비밀번호 변경',
                                                   "시안: 비밀번호 변경 메일을 보냈습니다", "mp-btn-edit") + "</div></section>")


def sec_refund_acc():
    bank, acc, owner = REG_ACC
    opts = '<option value="">은행을 선택하세요</option>' + "".join(f'<option{" selected" if b == bank else ""}>{b}</option>' for b in BANKS)
    row = lambda lab, fid, inner: (f'<div class="profile-form-row"><label class="p-label" for="{fid}">{lab}</label>'  # noqa: E731
                                   f'<div class="p-input-wrap">{inner}</div></div>')
    hint = lambda t: f'<span class="p-help-text" style="display:block;margin-top:6px;color:#777;font-size:13px;">{t}</span>'  # noqa: E731
    form = ('<div class="profile-form-grid" style="display:flex;flex-direction:column;gap:16px;margin-top:4px;">'
            + row("은행", "mpBankName", f'<select name="bankName" id="mpBankName" class="p-input">{opts}</select>')
            + row("계좌번호", "mpBankAccount", '<input type="text" name="bankAccount" id="mpBankAccount" class="p-input" value="" '
                  'placeholder="숫자와 - 만 입력해주세요" maxlength="30" autocomplete="off">')
            + row("예금주", "mpBankOwner", '<input type="text" name="bankOwner" id="mpBankOwner" class="p-input" value="" placeholder="예금주 성함" '
                  'maxlength="20" autocomplete="off">' + hint("사업자 명의가 아니면 환불이 거절될 수 있습니다."))
            + row("비밀번호 확인", "mpBankPw", '<input type="password" name="currentPassword" id="mpBankPw" class="p-input" value="" '
                  'placeholder="로그인 비밀번호" autocomplete="current-password">' + hint("돈이 오가는 칸이라 본인이 맞는지 한 번 더 확인합니다."))
            + '</div><div class="mp-action-wrap">'
            + flash('<span class="material-symbols-outlined">save</span> 계좌 변경', "시안: 환불계좌를 바꿨습니다", "mp-btn-edit") + "</div>")
    log = [(P.d_of(-40), bank, acc, owner, True, "self"), (P.d_of(-240), "국민은행", "123-**-****-567", owner, False, "self")]
    logs = "".join(f'<div style="font-size:13px;line-height:1.9;color:#444;">{d:%Y.%m.%d} · {bk} {ac} ({ow})'
                   f'{"<strong> — 사용 중</strong>" if now else ""}<span class="add" style="color:#777;"> · 바꾼 사람 대표(이정민){tag()}</span></div>'
                   for d, bk, ac, ow, now, _w in log)
    return ('<section class="mp-section" id="s-acc"><div class="mp-section-header"><span class="material-symbols-outlined icon-mid">account_balance</span>'
            '<h3 class="mp-section-title">환불계좌</h3></div><div class="mp-info-list"><dl class="mp-info-row"><dt>현재 계좌</dt><dd>'
            f'<strong>{bank}</strong> {acc} ({owner}) <span style="color:#777;font-size:13px;">· {P.d_of(-40):%Y.%m.%d} 등록</span></dd></dl></div>'
            + form + '<div style="margin-top:14px;padding-top:14px;border-top:1px solid #eee;"><div style="font-size:13px;color:#777;margin-bottom:8px;">변경 기록</div>'
            + logs + "</div>"
            '<div style="margin-top:14px;padding:12px 14px;background:#f7f8fb;border-radius:8px;font-size:13px;line-height:1.8;color:#555;">'
            '계좌번호와 예금주는 <strong>암호화해 보관</strong>합니다. 화면에는 가린 값만 보입니다.<br>'
            '포인트 환불을 신청하면 여기 등록된 계좌가 자동으로 적힙니다 — 신청할 때 다시 입력하지 않아도 됩니다.<br>'
            '바꾼 날짜는 위 <strong>변경 기록</strong>에 남습니다.</div></section>')


def sec_leave():
    """회원 탈퇴 → 대행사 해지 · 먼저 정리할 것이 있으면 사유 칸 대신 빨간 상자(광고주와 같은 분기)"""
    n_camp = sum(1 for c in D.CAMPS if c["group"] in D.ACTIVE)
    block = [f'진행 중인 캠페인 {n_camp}개 — 모두 완료·중단해야 합니다 (<a href="campaigns.html">캠페인 리스트</a>)',
             f'보유 포인트 {num(D.BALANCE)} P — 환불 신청 후 해지해 주세요 (<a href="point.html">포인트</a>)',
             f'<span class="add">예치 중 포인트 {num(HELD)} P — 캠페인이 끝나 보유로 돌아온 뒤 환불{tag()}</span>',
             f'<span class="add">업체 {len(P.BIZS)}곳 — 업체 고객 계정으로 이전하거나 보관 (<a href="biz.html">업체</a>){tag()}</span>']
    return ('<section class="mp-section" id="s-leave"><div class="mp-section-header"><span class="material-symbols-outlined icon-mid">person_remove</span>'
            '<h3 class="mp-section-title">대행사 해지 <span style="font-size:13px;font-weight:400;color:#777;">(광고주: 회원 탈퇴)</span></h3></div>'
            '<div style="padding:16px 0;font-size:14px;line-height:1.9;color:#0e0e0e;">'
            '· 상호명 · 대표자명 · 사업자번호 · 담당자 연락처 · 이메일 · 주소가 <strong>즉시 지워집니다.</strong><br>'
            '· 다시 로그인하실 수 없습니다. <strong>되돌릴 수 없습니다.</strong><br>'
            '· 지난 캠페인 · 결제 기록은 정산과 세금계산서 처리를 위해 남습니다 (누구인지 알아볼 수 없는 형태입니다).<br>'
            f'<span class="add">· 해지하면 모든 직원 계정이 함께 닫히고, 보고서 링크도 더 열리지 않습니다.{tag()}</span></div>'
            '<div style="padding:16px;background:#fff4f4;border:1px solid #f3c5c5;border-radius:8px;font-size:14px;line-height:1.9;color:#8a2b2b;">'
            '<strong>먼저 정리하실 것이 있습니다</strong><br>' + "".join(f"· {x}<br>" for x in block) + "</div></section>")


def profile_modal():
    """profile.inc.html — 기본정보 · 상세정보 · 비밀번호변경 탭(숨은 라디오)"""
    req = ' <span class="req-mark">*</span>'

    def row(lab, inner, start=False, need=False):
        return (f'<div class="profile-form-row{" align-start" if start else ""}"><label class="p-label">{lab}{req if need else ""}</label>'
                f'<div class="p-input-wrap">{inner}</div></div>')

    inp = lambda name, val, ph, extra="": f'<input type="text" class="p-input" name="{name}" value="{val}" placeholder="{ph}" aria-label="{name}"{extra}>'  # noqa: E731
    chk = lambda name, lab, on: f'<label class="p-tag-label"><input type="checkbox" name="{name}"{" checked" if on else ""}><span>{lab}</span></label>'  # noqa: E731
    basic = ('<div class="profile-tab-content profile-tab-basic v9p"><div class="profile-form-grid">'
             + row("담당자명", inp("name", "이정민", "이름을 입력해주세요"), need=True)
             + row("닉네임", '<div class="p-input-group">' + inp("nickName", "애니라인", "닉네임을 입력해주세요")
                   + flash("중복확인", "시안: 쓸 수 있는 닉네임입니다", "p-btn-sub") + "</div>")
             + row("이메일", inp("email", "contact@anyline.kr", "이메일을 입력해주세요"), need=True)
             + row("수신동의", '<div class="p-tag-list">' + chk("mailAgree", "이메일 수신", True) + chk("smsAgree", "SMS(문자) 수신", True)
                   + chk("marketingAgree", "마케팅 정보 수신", False) + '</div><p class="zipcode-search-guide" style="margin-top:6px;">'
                   '마케팅 정보 수신은 프로모션·이벤트 등 광고성 정보 수신 여부입니다.</p>', start=True)
             + row("전화번호", inp("hphone", "010-****-1234", "010-0000-0000"), need=True)
             + row("회사명 / 브랜드명", inp("company", AGENCY, "회사명 또는 브랜드명을 입력해주세요"), need=True)
             + row("대표자명", inp("ceoName", "이정민", "대표자명을 입력해주세요"), need=True)
             + row("사업자번호", inp("bizNum", "123-45-*****", "000-00-00000"), need=True)
             + row("플레이스 / 오픈마켓 URL", inp("brandUrl", "", "네이버 플레이스 또는 오픈마켓 상품 페이지 URL을 입력해주세요"))
             + row("주소", '<div class="p-input-group cc-mb-10">' + inp("zipCode", "04524", "", ' readonly style="width:120px; flex:none;"')
                   + flash("우편번호", "시안: 우편번호 찾기", "p-btn-sub") + "</div>"
                   + inp("addr1", "서울시 ○○구 ○○로 00", "", ' style="margin-bottom:8px;"') + inp("addr2", "0층(더미)", ""), start=True)
             + "</div></div>")
    cats = ["맛집", "뷰티", "숙박", "육아", "생활", "반려동물", "디지털"]
    types = ["방문형", "배송형", "기자단"]
    detail = ('<div class="profile-tab-content profile-tab-detail v9p"><div class="profile-form-grid">'
              + row("관심 카테고리", '<div class="p-tag-list">' + "".join(chk("category[]", x, i < 2) for i, x in enumerate(cats)) + "</div>", start=True)
              + row("관심지역", '<div class="p-tag-list">' + "".join(chk("interestArea[]", x, x == "서울") for x in ["전국 전체", "서울", "경기", "인천", "부산"])
                    + "</div>", start=True)
              + row("관심유형", '<div class="p-tag-list">' + "".join(chk("interestType[]", x, i == 0) for i, x in enumerate(types)) + "</div>", start=True)
              + "</div></div>")
    pw = lambda name, ph: f'<input type="password" class="p-input" name="{name}" placeholder="{ph}" aria-label="{ph}" autocomplete="off">'  # noqa: E731
    password = ('<div class="profile-tab-content profile-tab-password v9p"><div class="profile-form-grid">'
                + row("현재 비밀번호", pw("currentPw", "현재 비밀번호를 입력해주세요."))
                + row("새 비밀번호", pw("regPw", "새 비밀번호를 입력해주세요."))
                + row("새 비밀번호 확인", pw("regPwConfirm", "새 비밀번호를 다시 입력해주세요.")) + "</div></div>")
    radios, bar = tab_bar("pet", [("기본정보", False), ("상세정보", False), ("비밀번호변경", False)],
                          btn="profile-tab-btn", bar="profile-modal-tabs")
    mid = "profileEditModal"
    return (f'<div class="modal-wrap profile-edit-modal" id="{mid}" popover><form name="registerForm" class="v9-form" onsubmit="return false;">'
            + hide_btn(mid, "", "modal-dim", "닫기")
            + f'<div class="profile-modal-content modal-content v9t">{radios}<div class="profile-modal-header"><h3 class="modal-title">내 정보 수정</h3>'
            + hide_btn(mid, CLOSE_ICON, "btn-profile-close", "닫기") + "</div>"
            + bar + f'<div class="profile-modal-body">{basic}{detail}{password}</div>'
            '<div class="profile-modal-footer">' + flash("저장", "시안: 저장했습니다", "btn-p-save") + "</div></div></form></div>")


def info_page():
    body = ('<div class="page-container mp-container"><div class="mp-card">'
            + sec_agency() + sec_me() + sec_refund_acc() + sec_leave() + "</div></div>" + profile_modal())
    write("info.html", "대행사 정보", "info", body)


# ════════════════ 6. 고객센터(help.html) ← notifications · notice · inquiry · faq · help.html ════════════════
def pane_alarm():
    r = random.Random("acc-alarm")
    msgs = ["캠페인 신청자가 새로 들어왔습니다", "리뷰가 등록되어 검수를 기다립니다", "포인트 충전이 완료되었습니다",
            "발신번호 심사 결과가 나왔습니다", "1:1 문의에 답변이 등록되었습니다", "리뷰 마감이 3일 남았습니다"]
    trs = ""
    for i in range(10):
        c = r.choice([x for x in D.CAMPS if x["group"] in D.ACTIVE])
        trs += (f'<tr class="notif-row{" unread" if i < 4 else ""}" data-biz="{c["bid"]}">'
                '<td class="notif-check"><label class="custom-checkbox"><input type="checkbox" class="notif-chk" aria-label="고르기"><span class="checkmark"></span></label></td>'
                f'<td data-label="알림 내용"><span class="add">[{esc(c["b"]["name"])}]</span> {r.choice(msgs)} — {esc(c["name"])}</td>'
                f'<td data-label="날짜">{dw(-i * 2)}</td></tr>')
    return ('<div class="notifications-container cmp-page-card"><div class="notif-header"><div class="notif-header-left">'
            '<h2 class="notif-title">알림 <span style="color:#dc2f02;font-size:16px;">(4)</span></h2>'
            '<p class="notif-notice">총 10건 · 90일이 지난 알림은 자동으로 정리 됩니다</p></div><div class="notif-header-right">'
            + flash("전체읽음 처리", "시안: 모두 읽음으로 바꿨습니다", "btn-notif-all-read") + "</div></div>"
            '<form class="msg-search" onsubmit="return false;"><div class="msg-search__group msg-search__group--period">'
            '<span class="msg-search__label">기간</span><input type="date" name="from" class="rev-msg-input msg-search__date" aria-label="시작일">'
            '<span class="msg-search__label msg-search__sep">~</span><input type="date" name="to" class="rev-msg-input msg-search__date" aria-label="끝일"></div>'
            '<div class="msg-search__group msg-search__group--query"><span class="msg-search__label">검색</span>'
            '<select name="read" class="rev-msg-input" aria-label="읽음"><option value="">읽음 전체</option><option value="unread">안 읽음</option>'
            '<option value="read">읽음</option></select><input type="text" name="q" placeholder="제목·내용" class="rev-msg-input msg-search__q" aria-label="제목·내용"></div>'
            '<div class="msg-search__actions">' + flash("검색", "시안: 조건으로 찾습니다", "msg-search__submit")
            + flash("초기화", "시안: 조건을 지웠습니다", "msg-search__reset") + "</div></form>"
            f'<div class="notif-list-wrap"><table class="notif-table"><tbody>{trs}</tbody></table></div>'
            '<div class="notif-footer-actions" style="display:flex;justify-content:flex-end;margin-top:16px;">'
            + flash("선택 삭제", "시안: 고른 알림을 지웠습니다", "p-btn-sub", "width:auto;padding:0 16px;height:36px;font-size:13px;")
            + "</div></div>")


NOTICES = [("inspect", "11월 15일(일) 새벽 2시~4시 서버 점검 안내", -1), ("update", "대행사 대시보드 v0.9 — 계정 메뉴 정리", -2),
           ("info", "자동발송 알림톡 단가 변경 안내", -6), ("event", "연말 충전 10% 추가 적립 이벤트", -9),
           ("info", "개인정보처리방침 개정 안내", -15), ("update", "검색결과 리포트 PDF 내려받기", -22),
           ("inspect", "10월 25일 결제 시스템 점검", -30), ("info", "리뷰어 지급 일정 변경(주 2회)", -41)]
NV_CATE = {"info": "안내", "event": "이벤트", "update": "업데이트", "inspect": "점검"}


def pane_notice():
    rows = "".join(f'<a class="nv-row js-flash" data-msg="시안: 공지 상세 — {esc(t)}"><span class="nv-row__num">{len(NOTICES) - i}</span>'
                   f'<span class="nv-row__title"><span class="nv-badge nv-badge--{k}">{NV_CATE[k]}</span>{t}'
                   f'{"<span class=" + chr(34) + "nv-new" + chr(34) + ">N</span>" if off >= -3 else ""}</span>'
                   f'<span class="nv-row__date">{P.d_of(off):%y.%m.%d}</span></a>' for i, (k, t, off) in enumerate(NOTICES))
    return ('<div class="page-container"><div class="nv-wrap"><div class="nv-head"><h2 class="nv-head__title">공지사항</h2></div>'
            '<form class="nv-search" onsubmit="return false;"><input type="search" name="kw" placeholder="제목 · 내용 검색" maxlength="50" aria-label="공지 검색">'
            + flash('<span class="material-symbols-outlined">search</span><span class="nv-search__label">검색</span>', "시안: 공지를 찾습니다", "v9-nv-btn")
            + f'</form><div class="nv-list">{rows}</div></div></div>')


QNA_DONE = 999
QNA = [("포인트/정산", "가상계좌 입금했는데 충전이 안 됐어요", 3, -1, "김지은", None),
       ("캠페인 등록/심사", "추가모집 요청 기준이 궁금합니다", 999, -5, "박서준", "모집 마감 후 선정 인원이 모자랄 때 캠페인 상세에서 [추가모집 요청]을 누르시면 됩니다."),
       ("계정/기타", "직원 계정 추가 가능 수", 999, -12, "대표", "등급별 직원 수 한도까지 추가할 수 있습니다. 사용료 화면 비교표를 확인해 주세요."),
       ("리뷰 검수", "미션 미충족 리뷰 승인해도 되나요", 1, 0, "김지은", None)]
QNA_STEP = {1: "접수중", 2: "답변대기", 3: "답변중", 999: "답변완료"}


def pane_qna():
    trs = ""
    for i, (t, q, st, off, who, ans) in enumerate(QNA):
        done = st == QNA_DONE
        a = (f'<div class="inquiry-detail-a"><span class="inquiry-detail-label inquiry-detail-label--a">답변</span>'
             f'<div class="inquiry-detail-text">{ans}</div><div class="inquiry-detail-date">{P.d_of(off + 1):%Y-%m-%d} 14:20</div></div>'
             if done else '<div class="inquiry-detail-a inquiry-detail-a--wait">답변을 준비중입니다. 답변이 등록되면 알림으로 알려드립니다.</div>')
        trs += (f'<tr class="inquiry-row"><td data-label="유형"><span class="inquiry-type">{t}</span></td>'
                f'<td data-label="제목" class="inquiry-subject"><input type="checkbox" id="iqOpen{i}" class="v9r"><label for="iqOpen{i}">{q}</label>'
                f'<span class="add v9-who">{who}{tag()}</span></td>'
                f'<td data-label="상태"><span class="inquiry-state{" inquiry-state--done" if done else ""}">{QNA_STEP[st]}</span></td>'
                f'<td data-label="등록일" class="inquiry-date">{dw(off)}</td></tr>'
                f'<tr class="inquiry-detail"><td colspan="4"><div class="inquiry-detail-box"><div class="inquiry-detail-q">'
                f'<span class="inquiry-detail-label">문의</span><div class="inquiry-detail-text">{q} — 확인 부탁드립니다.</div></div>{a}</div></td></tr>')
    mid = "inquiryModal"
    opts = "".join(f"<option>{t}</option>" for t in QNA_TYPES)
    bizs = "".join(f'<option>{esc(b["name"])}</option>' for b in P.BIZS[:8])
    form = ('<form class="inquiry-modal__form" onsubmit="return false;">'
            f'<div class="inquiry-field"><label class="inquiry-label" for="inquiryType">문의유형</label><select class="inquiry-input" name="inquiryType" id="inquiryType">{opts}</select></div>'
            f'<div class="inquiry-field add"><label class="inquiry-label" for="inquiryBiz">관련 업체{tag()}</label><select class="inquiry-input" id="inquiryBiz">'
            f'<option>업체 없음(대행사 전체)</option>{bizs}</select></div>'
            '<div class="inquiry-field"><label class="inquiry-label" for="inquiryTitle">제목</label><input type="text" class="inquiry-input" name="title" '
            'id="inquiryTitle" maxlength="100" placeholder="제목을 입력해 주세요."></div>'
            '<div class="inquiry-field"><label class="inquiry-label" for="inquiryContent">문의내용</label><textarea class="inquiry-textarea" name="content" '
            'id="inquiryContent" maxlength="2000" placeholder="문의하실 내용을 자세히 적어주시면 더 정확하게 답변드릴 수 있습니다."></textarea></div>'
            '<div class="inquiry-field"><label class="inquiry-label" for="inquiryFile">첨부파일</label><input type="file" class="inquiry-file-input" '
            'name="inquiryFile[]" id="inquiryFile" multiple><p class="cell-sub" style="margin:6px 0 0;line-height:1.6;">한 파일당 최대 10MB 까지 올릴 수 있습니다.</p></div>'
            '<div class="inquiry-modal__foot">' + hide_btn(mid, "취소", "inquiry-btn inquiry-btn--cancel")
            + flash("등록", "시안: 문의를 등록했습니다", "inquiry-btn inquiry-btn--send") + "</div></form>")
    pop = (f'<div class="inquiry-modal" id="{mid}" popover>' + hide_btn(mid, "", "inquiry-modal__dim", "닫기")
           + '<div class="inquiry-modal__box" role="dialog" aria-modal="true"><div class="inquiry-modal__head"><h3 class="inquiry-modal__title">1:1 문의하기</h3>'
           + hide_btn(mid, "&times;", "inquiry-modal__close", "닫기") + "</div>" + form + "</div></div>")
    return ('<div class="content-wrapper"><div class="inquiry-container"><div class="inquiry-header"><div class="inquiry-header-left">'
            f'<h2 class="inquiry-title">1:1 문의 <span class="inquiry-title-cnt">({len(QNA)})</span></h2>'
            '<p class="inquiry-notice">운영자에게 직접 문의하실 수 있습니다. 답변이 등록되면 알림으로 알려드립니다.</p></div>'
            f'<div class="inquiry-header-right"><button type="button" class="btn-inquiry-write" popovertarget="{mid}">'
            '<span class="material-symbols-outlined">edit_square</span>문의하기</button></div></div>'
            '<div class="inquiry-list-wrap"><table class="inquiry-table"><colgroup><col style="width:110px"><col><col style="width:120px"><col style="width:130px"></colgroup>'
            f'<thead><tr><th>유형</th><th>제목</th><th>상태</th><th>등록일</th></tr></thead><tbody>{trs}</tbody></table></div></div></div>', pop)


# FAQ 분류 = 실서버 faq.class $CATE (account · campaign · point · review · etc) + 대행사(agency)
FAQ_CATE = [("account", "계정"), ("campaign", "캠페인"), ("point", "포인트"), ("review", "리뷰"), ("etc", "기타"), ("agency", "대행사")]
FAQ = [("account", "비밀번호를 잊었어요", "로그인 화면의 [비밀번호 찾기]에서 이메일로 재설정 링크를 받을 수 있습니다."),
       ("account", "직원 계정은 몇 개까지 만들 수 있나요?", "등급별 직원 수 한도까지 만들 수 있습니다(사용료 화면 비교표)."),
       ("campaign", "캠페인 승인은 얼마나 걸리나요?", "영업일 기준 1일 안에 검토합니다."),
       ("campaign", "모집 인원을 늘릴 수 있나요?", "진행 중 캠페인은 [추가모집 요청]으로 늘릴 수 있습니다."),
       ("point", "예치 중 포인트는 무엇인가요?", "캠페인 시작 때 묶어 두는 포인트입니다. 캠페인이 끝나면 남은 만큼 사용 가능으로 돌아옵니다."),
       ("point", "환불은 언제 되나요?", "승인 후 영업일 3일 안에 등록 계좌로 입금됩니다."),
       ("review", "리뷰 수정 요청은 몇 번 할 수 있나요?", "리뷰 1건에 2번까지 요청할 수 있습니다."),
       ("etc", "세금계산서 발행은 어떻게 하나요?", "충전할 때 증빙 신청에서 세금계산서를 고르면 됩니다."),
       ("agency", "업체 고객도 로그인할 수 있나요?", "1차는 보고서 링크로만 봅니다. 업체 계정 이전은 해지·이전 때만 합니다.")]
ARROW = ('<svg width="14" height="8" viewBox="0 0 14 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round"><polyline points="1 1 7 7 13 1"></polyline></svg>')


def pane_faq():
    cats = [("all", "전체")] + FAQ_CATE
    radios = "".join(f'<input type="radio" name="fqc" id="fqc-{k}" class="v9r"{" checked" if k == "all" else ""}>' for k, _l in cats)
    btns = "".join(f'<label for="fqc-{k}" class="faq-cate__btn{" add" if k == "agency" else ""}">{lab}</label>' for k, lab in cats)
    items = "".join(f'<details class="faq-item{" add" if k == "agency" else ""}" data-cate="{k}"><summary class="faq-item__question">'
                    f'<div class="faq-item__q-icon">Q</div><div class="faq-item__title">{q}</div><div class="faq-item__arrow">{ARROW}</div></summary>'
                    f'<div class="faq-item__answer">{a}</div></details>' for k, q, a in FAQ)
    return ('<div class="faq-page">' + radios + '<div class="faq-page__header"><h2 class="faq-page__title">자주묻는 질문 (FAQ)</h2>'
            '<p class="faq-page__desc">광고주님들께서 자주 문의하시는 궁금증을 모아두었습니다.</p></div>'
            f'<div class="faq-cate">{btns}</div><div class="faq-accordion">{items}</div></div>')


# 도움말 — 실서버 help\help.data.php 의 글(분류 · 제목 · 요약) 중 계정 쪽 + 대행사 글(.add)
HELPS = [("이용권·포인트", "point-manage", "포인트 관리", "포인트를 충전·환불하고, 신청 내역과 사용 내역을 보고, 영수증·거래내역서를 받습니다.", False),
         ("이용권·포인트", "plan-purchase", "유료등급 구매", "유료등급을 카드로 결제해 캠페인 한도와 기능을 넓힙니다. 결제가 끝나면 즉시 적용됩니다.", False),
         ("이용권·포인트", "grade-feature", "등급에 따라 달라지는 것 (한도 · 기능)",
          "메뉴가 안 보이거나 캠페인 등록이 막힐 때 — 등급별 한도와 기능이 어떻게 적용되는지 설명합니다.", False),
         ("쪽지·발송함", "auto-send", "자동발송 설정",
          "캠페인 진행 중 특정 상황(선정, 방문 안내, 리뷰마감 등)이 오면 리뷰어에게 자동으로 문자·알림톡·메일을 보내도록 설정합니다.", False),
         ("인증·보안", "send-number", "발신번호 관리", "리뷰어에게 문자를 보낼 때 표시될 발신번호를 등록하고 심사받습니다.", False),
         ("인증·보안", "verify-identity", "본인인증", "전송자격인증제에 따라 휴대폰 본인인증을 진행하고, 자동발송 문자에 대한 사후 승인을 처리합니다.", False),
         ("마이페이지", "mypage", "마이페이지", "내 정보와 프로필 사진을 확인·수정하고, 보유 포인트·이용 플랜을 보고, 필요 시 회원 탈퇴를 진행합니다.", False),
         ("알림", "notifications", "알림", "캠페인 진행, 신고 처리 결과 등 시스템이 보낸 알림을 모아 보고 관리합니다.", False),
         ("공지·문의", "inquiry", "1:1 문의", "운영자에게 직접 문의를 등록하고 답변을 확인합니다.", False),
         ("패널티", "penalty", "패널티", "운영자가 나(광고주)에게 부여하거나 차감·취소한 패널티 내역과 누적 점수, 제재 기준을 확인합니다.", False),
         ("대행사", "ag-scope", "업체 범위", "맨 위 \"전체 업체 ▾\"로 한 업체만 보기 — 표·카드·알림이 그 업체 것만 남습니다.", True),
         ("대행사", "ag-owner", "담당자 배정", "업체마다 담당자 1명 · 그 업체 알림을 받는 사람입니다.", True),
         ("대행사", "ag-report", "보고서 링크", "업체 고객에게 공개 화면을 보내고, 필요 없으면 끕니다. 보고서에는 금액이 나오지 않습니다.", True),
         ("대행사", "ag-role", "팀·역할 권한", "관리자 · 팀장 · 담당자 · 조회 — 역할마다 볼 수 있는 업체와 할 수 있는 일이 다릅니다.", True)]


def pane_help():
    cats = []
    for cat, *_x in HELPS:
        if cat not in cats:
            cats.append(cat)
    toc = "".join(f'<div data-help-group{" class=" + chr(34) + "add" + chr(34) if cat == "대행사" else ""}><div class="help-toc__label">{cat}</div>'
                  + "".join(f'<a class="help-toc__item" href="#help-{k}">{t}</a>' for c, k, t, _s, _a in HELPS if c == cat) + "</div>"
                  for cat in cats)
    arts = "".join(f'<section class="help-article{" add" if ag else ""}" id="help-{k}"><span class="help-article__crumb">{c}</span>'
                   f'<h2 class="help-article__title">{t}{tag() if ag else ""}</h2><p class="help-article__summary">{s}</p>'
                   '<p class="help-text">화면마다 오른쪽 아래 <b>?</b> 버튼 → 그 화면의 도움말 창([전체 도움말에서 보기] [닫기]).</p></section>'
                   for c, k, t, s, ag in HELPS)
    return ('<div class="help-wrap"><aside class="help-toc"><div class="help-toc__search"><span class="material-symbols-outlined">search</span>'
            '<input type="text" id="helpSearch" placeholder="화면 이름으로 검색…" autocomplete="off" aria-label="도움말 검색"></div>'
            f'<nav id="helpTocNav">{toc}</nav></aside><div class="help-body" id="helpBody">{arts}</div></div>')


def help_page():
    radios, bar = tab_bar("hct", [("알림", False), ("공지사항", False), ("1:1 문의", False), ("자주묻는 질문", False), ("도움말", False)],
                          extra=f'<span class="v9-hint add">광고주는 사이드바 항목 5개 — 대행사는 고객센터 한 화면{tag()}</span>')
    qna, qna_pop = pane_qna()
    # 광고주 화면마다 뿌리 display 가 달라(flex 등) 탭 본문은 겉 <div class="v9p"> 로 한 겹 싼다
    panes = "".join(f'<div class="v9p">{x}</div>' for x in [pane_alarm(), pane_notice(), qna, pane_faq(), pane_help()])
    body = f'<div class="cmp-layout v9t v9-help">{radios}{bar}{panes}</div>{qna_pop}'
    write("help.html", "고객센터", "help", body)


if __name__ == "__main__":
    point_page()
    plan_page()
    sms_page()
    penalty_page()
    info_page()
    help_page()
