# -*- coding: utf-8 -*-
"""
[2026-11-10] 수시 알림 — 대시보드 시안 v0.4 (기획서 v0.4 6-11 · 8-5)
  순차 흐름(격자 = 기한 있는 일)과 따로, 언제 올지 모르고 바로 봐야 하는 일.
  등급 3단: 즉시(u) · 확인(c) · 참고(i). 즉시·확인은 읽기만 해서는 안 사라지고 [처리] 또는 [나중에]가 있어야 빠진다.
  근거(기존 뷰마): 선정자 취소 요청(cancelReq) · 리뷰어→광고주 신고 사유 · 지급 상태 · 쪽지 · 문의 유형
  gen_dashboard.py 가 불러 쓴다. 메인 난수(rnd)를 건드리지 않게 별도 시드를 쓴다.
"""
import html
import random

esc = html.escape
rng = random.Random(1110)

LEVEL = {"u": "즉시", "c": "확인", "i": "참고"}
KINDS = {
    # 종류: (등급, 이름)
    "cancel":   ("u", "취소 요청"),
    "report":   ("u", "신고 접수"),
    "payfail":  ("u", "지급 실패"),
    "deleted":  ("u", "리뷰 삭제·비공개"),
    "msg":      ("c", "쪽지·문의"),
    "rereview": ("c", "리뷰 재등록"),
    "assigned": ("c", "담당 배정"),
    "paid":     ("i", "입금 완료"),
    "charged":  ("i", "충전 완료"),
}
TIMES = ["방금", "4분 전", "12분 전", "38분 전", "1시간 전", "2시간 전", "3시간 전", "어제 18:20", "어제 11:05"]
REVIEWERS = ["맛집탐방러", "하늘빛일상", "도토리기록", "서울먹방일기", "주말산책", "봄날의리뷰", "카페투어링", "육아맘일기"]
SNOOZE = (("1시간 뒤", "1시간 뒤 다시 알림"), ("오늘 오후 6시", "오늘 오후 6시에 다시 알림"), ("내일 오전 9시", "내일 오전 9시에 다시 알림"))


def _acts(kind, rev):
    """종류별 바로 처리 버튼 — data-adone = 처리 후 남길 글자"""
    b = lambda label, done, cls="": f'<button type="button" class="btn sm {cls}" data-adone="{done}">{label}</button>'
    if kind == "cancel":
        return b("취소 승인", "취소 승인함 · 빈자리 1", "primary") + b("거절", "취소 거절함")
    if kind == "report":
        return '<a class="btn sm" href="#">신고 내용 보기 ↗</a>' + b("소명 보냄", "소명 보냄", "primary")
    if kind == "payfail":
        return b("계좌 재등록 요청", "계좌 재등록 요청 보냄", "primary") + b("다시 지급", "다시 지급함")
    if kind == "deleted":
        return b("리뷰어에게 쪽지", "쪽지 보냄", "primary") + b("패널티 부여", "패널티 부여함", "ghost-danger")
    if kind == "msg":
        return ('<input class="input al-reply" placeholder="답장 쓰기" aria-label="답장">'
                + b("답장", "답장 보냄", "primary"))
    if kind == "rereview":
        return b("검수하러 가기", "검수 칸으로 이동", "primary js-al-go")
    return b("확인", "확인함", "primary")


def _text(kind, rev, camp):
    return {
        "cancel":   f"<b>{rev}</b>님이 선정 취소를 요청했습니다 · 사유 “갑자기 일정이 생겼어요”",
        "report":   f"<b>{rev}</b>님이 신고했습니다 · <b>제공내역 다름</b>",
        "payfail":  f"<b>{rev}</b>님 지급 실패 · 계좌 정보 불일치 (10,000P)",
        "deleted":  f"<b>{rev}</b>님 리뷰가 <b>비공개</b>로 바뀌었습니다 (검수 승인 3일 뒤)",
        "msg":      f"<b>{rev}</b>님 쪽지 · “주차 가능한가요? 아이 동반도 되나요?”",
        "rereview": f"<b>{rev}</b>님이 수정 요청한 리뷰를 다시 올렸습니다",
        "assigned": "관리자가 이 업체를 <b>김지은</b>님에게 배정했습니다",
        "paid":     f"<b>{rev}</b> 외 3명 입금 완료 (11/10)",
        "charged":  "포인트 500,000P 충전 완료",
    }[kind]


def card(a, demo=False):
    kind, lv = a["kind"], KINDS[a["kind"]][0]
    tb = a.get("ty", "")
    camp = (f' · <span class="ty ty-{tb}">{a["tyname"]}</span> {esc(a["camp"])}' if a.get("camp") else "")
    esc_tag = (f'<p class="al-esc">처리 안 된 지 2시간이 넘어 <b>팀장 {a["lead"]}</b>님에게도 알렸습니다</p>' if a.get("esc") else "")
    snooze = "" if lv == "i" else (
        '<details class="snooze"><summary>나중에</summary><div class="sz">'
        + "".join(f'<button type="button" class="btn sm" data-snooze="{msg}">{lab}</button>' for lab, msg in SNOOZE)
        + "</div></details>")
    done_btn = "" if lv == "i" or kind in ("assigned",) else '<button type="button" class="btn sm ghost" data-adone="처리 완료">처리 완료</button>'
    attrs = f' data-demo hidden' if demo else ""
    return (f'<article class="alert lv-{lv} is-new" data-aid="{a["id"]}" data-biz="{a["bid"]}" data-lv="{lv}" data-kind="{kind}"'
            f'{f" data-go=\"{a["go"]}\"" if a.get("go") else ""}{attrs}>'
            f'<div class="al-h"><span class="lvb lv-{lv}">{LEVEL[lv]}</span><b>{KINDS[kind][1]}</b>'
            f'<span class="al-t">{a["time"]}</span><i class="new-dot" aria-label="새 알림"></i></div>'
            f'<p class="al-biz">{esc(a["biz"])}{camp}</p>'
            f'<p class="al-txt">{_text(kind, a["rev"], a.get("camp"))}</p>{esc_tag}'
            f'<div class="al-acts">{_acts(kind, a["rev"])}{done_btn}{snooze}</div></article>')


def make(bizs, camp_meta, type_name, staff_lead):
    """업체 목록에서 알림 더미를 만든다. 반환: (보이는 알림, 나중에 미룬 알림, 시연용 새 알림)"""
    plan = ["cancel", "cancel", "report", "payfail", "deleted", "msg", "msg", "msg", "rereview",
            "assigned", "msg", "cancel", "paid", "charged", "paid"]
    out = []
    pool = [b for b in bizs if b["issues"]] or bizs
    for i, kind in enumerate(plan):
        b = rng.choice(pool)
        camp = rng.choice(b["camps"])
        ty = camp_meta[camp][0]
        a = {"id": f"a{i}", "kind": kind, "bid": b["id"], "biz": b["name"], "rev": rng.choice(REVIEWERS),
             "time": TIMES[min(i // 2, len(TIMES) - 1)], "camp": camp if kind not in ("charged", "assigned") else "",
             "ty": ty, "tyname": type_name[ty]}
        if kind == "rereview" and "review" in b["issues"]:
            a["go"] = f'{b["id"]}-review'
        if KINDS[kind][0] == "u" and i in (2, 4) and b["owner"]:
            a["esc"] = True
            a["lead"] = staff_lead.get(b["owner"][3], "관리자")
        out.append(a)
    snoozed = out[10:11]          # 미리 '나중에'로 미뤄 둔 것 하나
    shown = out[:10] + out[11:]
    demo_b = rng.choice(pool)
    demo_c = rng.choice(demo_b["camps"])
    demo = {"id": "a-demo", "kind": "cancel", "bid": demo_b["id"], "biz": demo_b["name"], "rev": "소소한하루",
            "time": "방금", "camp": demo_c, "ty": camp_meta[demo_c][0], "tyname": type_name[camp_meta[demo_c][0]]}
    return shown, snoozed, demo


def pane(shown, snoozed, demo):
    """오른쪽 패널의 '받은 알림' 화면"""
    chips = ('<div class="alvs" role="group" aria-label="알림 등급">'
             '<button type="button" class="alv on" data-alv="">전체 <em class="js-alv-all"></em></button>'
             '<button type="button" class="alv" data-alv="u"><span class="lvb lv-u">즉시</span><em class="js-alv-u"></em></button>'
             '<button type="button" class="alv" data-alv="c"><span class="lvb lv-c">확인</span><em class="js-alv-c"></em></button>'
             '<button type="button" class="alv" data-alv="i"><span class="lvb lv-i">참고</span><em class="js-alv-i"></em></button></div>')
    later = "".join(card(a) for a in snoozed).replace('class="alert ', 'class="alert is-snoozed ', 1)
    later = later.replace('<div class="al-acts">', '<p class="al-sz">오늘 오후 6시에 다시 알림</p><div class="al-acts">', 1)
    return (
        '<section class="pane pane-alert" data-panel="alerts" hidden>'
        '<header class="pane-h"><p class="pane-biz">받은 알림 <span>순차 처리와 별개로 수시로 오는 일</span></p>'
        '<h2>처리할 알림 <em class="js-al-open"></em></h2>'
        '<p class="pane-camp">읽기만 해서는 사라지지 않습니다 — [처리] 또는 [나중에]를 누르세요</p>'
        f'{chips}<p class="al-bizf" hidden><span class="js-al-bizname"></span> 알림만 보는 중 '
        '<button type="button" class="btn link js-al-allbiz">모든 업체</button></p></header>'
        '<div class="pane-b">'
        '<p class="al-morning">☀ 어제 못 끝낸 알림 <b>2건</b>이 남아 있어요 — 위에서부터 처리하세요</p>'
        f'<div class="al-list js-al-list">{"".join(card(a) for a in shown)}{card(demo, demo=True)}</div>'
        f'<details class="al-fold js-al-later"><summary>나중에 <em>{len(snoozed)}</em></summary><div class="al-list">{later}</div></details>'
        '<details class="al-fold js-al-done"><summary>처리됨 <em>0</em></summary><div class="al-list"></div></details>'
        '</div>'
        '<footer class="pane-f"><a href="#" class="btn ghost">알림 설정 →</a>'
        '<button type="button" class="btn primary js-close-alerts">격자로 돌아가기</button></footer></section>')


def bar():
    """대시보드 맨 위 '받은 알림' 띠 — 격자를 스크롤해도 같은 자리"""
    return ('<div class="alertbar" role="region" aria-label="받은 알림">'
            '<b class="ab-title">🔔 받은 알림</b>'
            '<button type="button" class="ab ab-u" data-open-alerts="u"><span class="lvb lv-u">즉시</span><em class="js-ab-u">0</em>'
            '<span class="ab-kinds js-ab-ukinds"></span></button>'
            '<button type="button" class="ab ab-c" data-open-alerts="c"><span class="lvb lv-c">확인</span><em class="js-ab-c">0</em>'
            '<span class="ab-kinds js-ab-ckinds"></span></button>'
            '<button type="button" class="ab ab-i" data-open-alerts="i"><span class="lvb lv-i">참고</span><em class="js-ab-i">0</em></button>'
            '<button type="button" class="btn sm ab-all" data-open-alerts="">모두 보기</button></div>')
