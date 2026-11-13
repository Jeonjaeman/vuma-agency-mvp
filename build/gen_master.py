"""뷰마 마스터(운영자) 대시보드 데모 — master/index.html   [2026-11-13]

근거: D:\\WORK\\후기닷컴\\조사\\20261113\\마스터대시보드_분석·기획.md
  · 레이아웃 = 실서버 anyline/inc/header.inc.html 마크업 + anyline/css/master.css 그대로(master/css/master.css, 고치지 않음)
  · 메뉴 = core/lib/anyline/master.class.php 의 $pages · $navGroups 를 읽어 둔 build/master_nav.json
  · 대시보드 추가 모양 = master/css/md.css (md- 접두사만)
  · JS 없음 — 역할 탭 = 라디오 + :has() · 큐 서랍/가운데 창/메뉴 안내 = popover
"""
import html
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "master" / "index.html"
NAV = json.loads((Path(__file__).parent / "master_nav.json").read_text(encoding="utf-8"))
rnd = random.Random(1113)
esc = html.escape

# 대행사 데모와 같은 세계관
BIZ = ["연남 헤어살롱", "망원 파스타바", "성수 브런치랩", "서촌 한옥카페", "강남 피부과의원", "제주 감귤농원",
       "익선동 와인바", "부산 해운대횟집", "광교 치과의원", "강릉 커피공장", "전주 한정식", "청담 속눈썹샵"]
CAMPS = ["11월 방문 체험단", "신메뉴 리뷰", "블로그 기자단", "신제품 배송 체험", "인스타 릴스 체험", "유튜브 쇼츠 체험"]
REVIEWERS = ["맛집탐방러", "하늘빛일상", "도토리기록", "서울먹방일기", "주말산책", "봄날의리뷰", "카페투어링", "뷰티로그"]
AGENCIES = ["애니라인 마케팅", "브릿지애드", "온길컴퍼니", "모아리뷰랩"]

# 역할 — master.class.php $roles (슈퍼·심사·정산·CS·콘텐츠)
ROLES = [("all", "전체"), ("review", "심사"), ("settle", "정산"), ("cs", "CS"), ("content", "콘텐츠")]
AREAS = [("camp", "캠페인"), ("member", "회원"), ("money", "돈"), ("talk", "소통"), ("safe", "신뢰·안전")]


def camp():
    return f"[{rnd.choice(BIZ).split()[0]}] {rnd.choice(CAMPS)}"


def Q(key, area, name, kind, n, age, roles, path, purpose, row, nav=None):
    """큐 1개. age = 가장 오래 기다린 건(시간, None=시간 기준 없음) · row() = 서랍 목록 한 줄 (대상, 설명)"""
    ages = sorted([age] + [max(0, age - rnd.randint(1, max(1, age))) for _ in range(min(n, 6) - 1)], reverse=True) if age is not None else [None] * min(n, 6)
    return {"key": key, "area": area, "name": name, "kind": kind, "n": n, "age": age, "roles": roles, "path": path,
            "purpose": purpose, "rows": [(*row(), a) for a in ages], "nav": nav}


# 처리 대기 · 감시 큐 33개 — 기획안 2장 표 그대로(조건·함수는 기획안 참고)
QUEUES = [
    Q("judge", "camp", "캠페인 심사", "act", 3, 26, "review", "/campaign/campaignJudge.html?sort=old", "심사 제출한 캠페인 승인·반려",
      lambda: (camp(), "심사 제출"), "campaign-review"),
    Q("rerecruit", "camp", "추가모집 요청", "act", 1, 5, "review", "/campaign/campaigns.html", "광고주 추가모집 요청 처리",
      lambda: (camp(), f"{rnd.randint(2, 5)}명 더 모집")),
    Q("delay", "camp", "선정 지연", "act", 2, 30, "review cs", "/campaign/matching.html?status=selecting", "발표일이 지났는데 선정 0명",
      lambda: (camp(), "발표일 지남 · 선정 0명")),
    Q("noshow", "camp", "리뷰 지연", "act", 4, 50, "review cs", "/campaign/matching.html?status=selecting", "체험 종료 + 7일 지났는데 리뷰 없음",
      lambda: (rnd.choice(REVIEWERS), camp())),
    Q("review", "camp", "리뷰 검수", "act", 18, 20, "review", "/system/reviews.html?st=wait", "리뷰 URL 미션 충족 확인 · 승인·반려",
      lambda: (rnd.choice(REVIEWERS), camp())),
    Q("recheck", "camp", "재검수 요청", "act", 1, 3, "review", "/system/reviews.html?st=recheck", "광고주가 검수 결과에 이의",
      lambda: (rnd.choice(REVIEWERS), camp() + " · 광고주 이의")),
    Q("video", "camp", "영상 제작 요청", "act", 2, 14, "content", "/campaign/videoRequests.html?st=0", "클립·릴스·쇼츠 제작 후 업로드",
      lambda: (camp(), rnd.choice(["릴스 1편", "쇼츠 2편", "클립 1편"]))),
    Q("overpay", "camp", "초과모집 결제 대기", "watch", 2, 40, "settle", "/campaign/overRecruits.html?step=waitpay", "광고주가 충전해야 끝나는 건 — 오래 머물면 연락",
      lambda: (camp(), "충전 대기"), "over-recruit"),
    Q("multi", "camp", "다중 선정", "watch", 1, None, "review", "/campaign/matching.html", "한 리뷰어가 진행 중 캠페인 3개 이상",
      lambda: (rnd.choice(REVIEWERS), "진행 중 3개 동시 선정")),

    Q("agency", "member", "대행사 신청", "act", 2, 31, "review", "/member/agencyApplies.html?step=todo", "대행사 모드 신청 심사",
      lambda: (rnd.choice(AGENCIES[1:]), rnd.choice(["접수", "심사 중"])), "agency-apply"),
    Q("influencer", "member", "인플루언서 확인", "act", 5, 22, "review", "/member/reviewers.html?inf=wait", "인플루언서 인증 확인",
      lambda: (rnd.choice(REVIEWERS), "팔로워 증빙 제출")),
    Q("insta", "member", "인스타 확인", "act", 3, 9, "review", "/member/reviewers.html?sns=instaWait", "인스타 계정 연결 확인",
      lambda: (rnd.choice(REVIEWERS), "인스타 연결")),
    Q("gradeup", "member", "등급 승급 대상", "act", 7, None, "review", "/member/reviewerGrades.html?tab=candidate", "조건을 채운 회원 수동 승급",
      lambda: (rnd.choice(REVIEWERS + BIZ), "승급 조건 충족")),
    Q("dormant", "member", "휴면 전환 예정", "watch", 41, None, "cs", "/member/dormant.html", "30일 안에 휴면 전환(안내 발송됨)",
      lambda: (rnd.choice(REVIEWERS), "마지막 접속 11개월 전")),
    Q("restrict", "member", "정지·이용 제한", "watch", 12, None, "review cs", "/member/reviewers.html?state=restrict", "패널티로 이용 제한 중",
      lambda: (rnd.choice(REVIEWERS), "리뷰 미제출 패널티")),
    Q("withdraw", "member", "이번 달 탈퇴", "watch", 23, None, "cs", "/member/withdrawn.html", "탈퇴 사유 분포 확인",
      lambda: (rnd.choice(["리뷰어", "광고주"]), rnd.choice(["이용 빈도 낮음", "다른 서비스 이용", "선정이 안 됨"]))),

    Q("bank", "money", "무통장 충전 승인", "act", 1, 4, "settle", "/payment/billing.html?tab=pending", "입금 확인 후 포인트 충전 승인",
      lambda: (rnd.choice(BIZ), f"{rnd.choice([30, 50, 100])}만 원 입금 대기"), "billing"),
    Q("refund", "money", "출금 요청", "act", 3, 28, "settle", "/payment/settleWithdrawal.html?st=wait", "리뷰어·광고주 출금 2인 결재",
      lambda: (rnd.choice(REVIEWERS), f"{rnd.randint(3, 25) * 10000:,}원"), "settlement"),
    Q("payout", "money", "리뷰어 지급 대기", "act", 41, 52, "settle", "/payment/settlement.html", "선정 확정 · 아직 지급 안 된 원고료",
      lambda: (rnd.choice(REVIEWERS), camp())),
    Q("close", "money", "캠페인 정산", "act", 6, 19, "settle", "/payment/settleClose.html?st=wait", "종료 + 10일 — 보증금 환불 · 수수료 확정",
      lambda: (camp(), "종료 + 10일")),
    Q("approval", "money", "내 결재 대기", "act", 2, 6, "settle review", "/system/approvals.html?f=mine", "2인 결재 — 여기서 막히면 지급·출금이 늦어짐",
      lambda: (rnd.choice(["출금", "정산", "충전 취소"]), rnd.choice(["정산관리자 박서윤 상신", "CS매니저 이도윤 상신"]))),
    Q("evidence", "money", "증빙 미발행", "act", 4, 70, "settle", "/payment/billing.html?tab=tax", "세금계산서·현금영수증 발행",
      lambda: (rnd.choice(BIZ), "세금계산서")),
    Q("hold", "money", "정산 보류", "watch", 1, 200, "settle", "/payment/settleHold.html", "자동 목록에서 빠져 잊히기 쉬움",
      lambda: (camp(), "보류 — 광고주 확인 중")),
    Q("rejected", "money", "반려·취소 충전", "watch", 2, None, "settle", "/payment/chargeRejected.html", "이번 달 반려·카드 취소",
      lambda: (rnd.choice(BIZ), "입금자명 불일치")),

    Q("inquiry", "talk", "1:1 문의", "act", 4, 18, "cs content", "/cs/inquiry.html?state=wait", "리뷰어·광고주 문의 답변",
      lambda: (rnd.choice(REVIEWERS + BIZ), rnd.choice(["포인트 지급 언제", "선정 기준 문의", "리뷰 수정 요청", "충전 영수증"])), "support"),
    Q("counsel", "talk", "상담 신청", "act", 1, 2, "cs content", "/cs/counsel.html?state=0", "비회원 무료 상담 — 연락",
      lambda: ("비회원", "체험단 도입 상담"), "counsel"),
    Q("note", "talk", "운영자 쪽지", "act", 3, 7, "review settle cs content", "/message/notes.html?box=received", "받은 쪽지(답장 등)",
      lambda: (rnd.choice(BIZ), "쪽지 답장"), "messages"),
    Q("autosend", "talk", "자동문자 사후인증", "act", 1, 63, "cs", "/system/verifyAutoSend.html", "72시간 넘으면 다른 화면으로 못 나감",
      lambda: ("SITE", "자동문자 18건 발송분"), "sms-box"),
    Q("sendfail", "talk", "발송 실패(24시간)", "watch", 9, None, "cs content", "/message/smsBox.html?state=2", "수신거부 · 마케팅 미동의 · 요청 실패",
      lambda: (rnd.choice(REVIEWERS), rnd.choice(["수신거부", "마케팅 미동의", "발송 요청 실패"]))),
    Q("sendnum", "talk", "발신번호 반려", "watch", 1, None, "cs", "/system/sendNumber.html", "반려된 발신번호 — 재등록 안내",
      lambda: (rnd.choice(AGENCIES), "서류 미비 반려")),
    Q("catalogoff", "talk", "꺼진 발송 항목", "watch", 2, None, "content", "/cs/notifications.html?st=off", "발송관리에서 꺼 둔 알림",
      lambda: ("알림톡", rnd.choice(["선정 안내", "리뷰 마감 3일 전"]))),

    Q("report", "safe", "신고", "act", 2, 27, "review cs", "/cs/penalty.html?tab=report&state=wait", "신고 처리 · 패널티 부과",
      lambda: (rnd.choice(REVIEWERS), rnd.choice(["노쇼 신고", "허위 리뷰 신고"])), "penalty"),
    Q("penalty", "safe", "적용 중 패널티", "watch", 12, None, "review cs", "/cs/penalty.html?tab=penalty&pstate=active", "만료일까지 신청 제한",
      lambda: (rnd.choice(REVIEWERS), "30일 신청 제한")),
]

# 핵심 크론 6개 (크론탭_전체_20261103) — 하나를 실패로 둬서 경고 띠를 보인다
CRON = [("campaignStepUpdate", "01:00", "01:00", "ok", "캠페인 단계 이동 — 멈추면 전부 멈춤"),
        ("blogIndexScan", "04:10", "04:12", "ok", "블로그 지수 수집 · 네이버 API 하루 25,000회"),
        ("memberPurgeScan", "04:05", "04:05", "ok", "회원 개인정보 파기(법적 의무)"),
        ("campaignPurgeScan", "04:20", "04:20", "ok", "캠페인 신청자 정보 파기(법적 의무)"),
        ("settlementScan", "05:00", "05:00", "fail", "정산 대상 등록 — 타임아웃(DB 연결)"),
        ("autoSendScan", "매시", "09:00", "ok", "자동문자 발송")]
SYS = [("오늘 실패한 자동화", "1건", "bad", "/system/automation.html?f=fail"),
       ("실제 문자 발송 (sms.live)", "켜짐", "ok", "/system/siteConfig.html?tab=sms"),
       ("개인정보 파기 기록", "04:20 정상", "ok", "/system/purgeLog.html"),
       ("DB 반영 점검", "누락 0", "ok", "/system/dbCheck.html"),
       ("오늘 로그인 실패", "3회", "ok", "/system/loginLog.html"),
       ("문자 잔액", "확인할 곳 없음(업체 API 연동 필요)", "na", "")]

NOTI = [("inquiry", "문의", "badge--info", "포인트 지급 언제 되나요?", "도토리기록", "8분 전"),
        ("refund", "출금", "badge--main", "출금 신청 150,000원", "하늘빛일상", "32분 전"),
        ("report", "신고", "badge--danger", "노쇼 신고 접수", "제주 감귤농원", "1시간 전"),
        ("delay", "매칭", "badge--warning", "선정 발표일 지남 — 선정 0명", "[서촌] 블로그 기자단", "2시간 전"),
        ("recheck", "재검수", "badge--warning", "광고주 재검수 요청", "[익선동] 신메뉴 리뷰", "3시간 전"),
        ("close", "캠페인", "badge--danger", "모집완료 후 광고주가 캠페인 숨김", "[강남] 11월 방문 체험단", "어제")]
UPCOMING = [("오늘", "모집마감 4건 · 선정 발표 2건", "/calendar.html"), ("11.14 (금)", "리뷰마감 6건", "/calendar.html"),
            ("11.15 (토)", "모집마감 3건", "/calendar.html"), ("11.17 (월)", "세금계산서 발행 (수동 일정)", "/payment/billing.html"),
            ("11.18 (화)", "선정 발표 5건 · 리뷰마감 2건", "/calendar.html"), ("11.20 (목)", "월 정산 결재 (수동 일정)", "/payment/settlement.html")]
AUDIT = [("09:08", "박서윤", "승인", "출금", "하늘빛일상 120,000원 1차 결재"), ("09:02", "이도윤", "답변", "문의", "충전 영수증 문의 답변"),
         ("08:51", "김운영", "변경", "사이트 설정", "sms.live N → Y"), ("08:40", "최하린", "승인", "캠페인", "[성수] 신메뉴 리뷰 심사 승인"),
         ("08:33", "최하린", "반려", "캠페인", "[망원] 겨울 시즌 체험 — 경품 표기 누락"), ("08:20", "박서윤", "보류", "정산", "[부산] 블로그 기자단 — 광고주 확인"),
         ("어제 18:12", "이도윤", "부과", "패널티", "봄날의리뷰 리뷰 미제출 30일"), ("어제 17:40", "김운영", "등록", "대행사", "온길컴퍼니 대행사 승인")]
MONEY = [("이번 달 충전", 48_200_000, "카드 41,700,000 · 무통장 6,500,000"), ("리뷰어 지급", 31_450_000, "1,284건"),
         ("수수료 매출", 6_290_000, "지급 기준 · 평균 20%"), ("출금·환불", 4_120_000, "출금 3,280,000 · 보증금 환불 840,000"),
         ("광고주 미사용 잔액", 128_900_000, "새 집계 필요 — 예시 값")]
RECON = [("6월", 31, 22, 4.4), ("7월", 36, 25, 5.0), ("8월", 39, 27, 5.4), ("9월", 42, 29, 5.8), ("10월", 51, 34, 6.8), ("11월", 48, 31, 6.3)]


# ── 조각 ─────────────────────────────────────────────
def age_txt(h):
    if h is None:
        return ""
    return f"{h}시간" if h < 48 else f"{h // 24}일"


def age_cls(h):
    return "" if h is None else "is-hot" if h >= 24 else "is-soon" if h >= 8 else "is-later"


def ms(i):
    return f'<span class="material-symbols-outlined" aria-hidden="true">{i}</span>'


def sidebar():
    badge = {q["nav"]: q["n"] for q in QUEUES if q["nav"]}
    badge["inbox"] = len(NOTI)
    out = []
    for g in NAV["groups"]:
        lab = f'<div class="nav-group__label">{g["label"]}</div>' if g["label"] else ""
        items = "".join(
            f'<button type="button" class="nav-item md-navbtn{" active" if k == "dashboard" else ""}" popovertarget="md-stub-{k}">'
            f'{ms(NAV["pages"][k]["icon"])}<span>{NAV["pages"][k]["label"]}</span>'
            + (f'<span class="nav-item__badge" title="처리 대기 {badge[k]}건">{badge[k] if badge[k] < 100 else "99+"}</span>' if badge.get(k) else "")
            + "</button>" for k in g["items"])
        out.append(f'<div class="nav-group">{lab}{items}</div>')
    return ('<aside class="sidebar" id="sidebar"><div class="sidebar-brand"><span class="brand-label">REVIEW.COM</span>'
            f'<span class="brand-name">{ms("shield_person")}MASTER</span></div><nav class="sidebar-nav">{"".join(out)}</nav>'
            '<div class="sidebar-footer">ⓒ ANYRIZE · 운영자 콘솔 · 데모</div></aside>')


def stubs():
    """메뉴 안내 — 데모에는 대시보드만 있다"""
    return "".join(
        f'<div class="md-stub" id="md-stub-{k}" popover><p class="md-stub-h">{ms(p["icon"])}<b>{p["crumb"]} / {p["label"]}</b></p>'
        f'<p>실서버 화면 <code>{esc(p["file"])}</code> — 데모에는 대시보드만 만들었습니다.</p>'
        f'<button type="button" class="btn btn--sm btn--outline" popovertarget="md-stub-{k}" popovertargetaction="hide">닫기</button></div>'
        for k, p in NAV["pages"].items() if k != "dashboard")


def topbar():
    return ('<header class="topbar" id="topbar"><div class="topbar__title"><span class="topbar__crumb">홈 / 대시보드</span>'
            '<span class="topbar__page">대시보드</span></div><div class="topbar__actions">'
            f'<button class="topbar__icon" title="전역 검색" popovertarget="md-stub-search">{ms("search")}</button>'
            f'<button class="topbar__icon" title="알림 센터 (미확인 {len(NOTI)}건)" popovertarget="md-stub-inbox">{ms("notifications")}<span class="badge-dot"></span></button>'
            '<div class="admin-chip"><span class="admin-chip__avatar">김</span><span class="admin-chip__meta">'
            '<span class="admin-chip__name">김운영</span><span class="admin-chip__role">슈퍼관리자</span></span></div>'
            f'<button class="topbar__icon" title="로그아웃">{ms("logout")}</button></div></header>')


def head_line():
    acts = [q for q in QUEUES if q["kind"] == "act"]
    total = sum(q["n"] for q in acts)
    late = sum(sum(1 for r in q["rows"] if r[2] is not None and r[2] >= 24) for q in acts)
    bad = sum(1 for c in CRON if c[3] != "ok") + sum(1 for s in SYS if s[2] == "bad")
    tabs = "".join(f'<input type="radio" name="md-role" id="md-role-{k}" class="md-role-in"{" checked" if k == "all" else ""}>'
                   f'<label for="md-role-{k}" class="md-role">{n}</label>' for k, n in ROLES)
    return ('<div class="page-header"><div><h2 class="page-header__title">운영 대시보드</h2>'
            f'<p class="page-header__desc">11월 13일 (목) <b>09:10 기준</b> · 처리할 일 <b>{total}건</b> · '
            f'<span class="md-hot">24시간 넘은 것 {late}</span> · <span class="md-hot">시스템 경고 {bad}</span></p></div>'
            f'<div class="md-roles" role="radiogroup" aria-label="역할별 보기"><span class="md-roles-l">보기</span>{tabs}</div></div>')


def sys_strip():
    fails = [c for c in CRON if c[3] != "ok"]
    msg = " · ".join(f'<b>{c[0]}</b> {c[1]} 실패' for c in fails)
    return (f'<div class="md-alert" role="alert">{ms("error")}<p>{msg} · 크론 핵심 {len(CRON)}개 중 {len(CRON) - len(fails)}개 정상 · '
            f'오늘 실패한 자동화 1건</p><button type="button" class="btn btn--sm btn--outline" popovertarget="md-dr-sys">자세히</button></div>')


def q_btn(q):
    """[2026-11-13] 한 줄 = 이름 · 가장 오래 기다린 시간 · 건수(오른쪽 맞춤 — 세로로 훑어 비교)
       지켜보기 항목의 시간은 색 없이 — 요청 "시간 표기와 회색의 의미"(같은 회색이 두 뜻으로 쓰여 헷갈림)"""
    zero = " is-zero" if q["n"] == 0 else ""
    cls = age_cls(q["age"]) if q["kind"] == "act" else ""
    age = f'<small class="md-age {cls}">{age_txt(q["age"])}</small>' if q["age"] is not None and q["n"] else "<small></small>"
    return (f'<li><button type="button" class="md-q md-{q["kind"]}{zero}" data-roles="{q["roles"]}" popovertarget="md-dr-{q["key"]}" '
            f'title="{esc(q["purpose"])}"><span>{q["name"]}</span>{age}<b>{q["n"]}</b></button></li>')


def board():
    """[2026-11-13] 요청 "구분 5개를 열(col)로, 항목들을 행(row)으로" — 영역 = 열, 큐 = 열 안의 줄"""
    cols = []
    for a, lab in AREAS:
        qs = [q for q in QUEUES if q["area"] == a]
        act = "".join(q_btn(q) for q in qs if q["kind"] == "act")
        watch = "".join(q_btn(q) for q in qs if q["kind"] == "watch")
        n = sum(q["n"] for q in qs if q["kind"] == "act")
        cols.append(f'<div class="md-col" data-area="{a}"><p class="md-area"><b>{lab}</b><em>{n}건</em></p>'
                    f'<ul class="md-qs">{act}</ul>'
                    + (f'<p class="md-wl">지켜보기</p><ul class="md-ws">{watch}</ul>' if watch else "") + '</div>')
    return ('<section class="card md-board" aria-label="처리 대기"><div class="card__head"><span class="card__title">처리 대기</span>'
            '<span class="md-legend">시간 = 가장 오래 기다린 건 · <i class="md-age is-hot">24시간 넘음</i>'
            '<i class="md-age is-soon">8시간 넘음</i><i class="md-age">8시간 안</i></span></div>'
            f'<div class="md-cols">{"".join(cols)}</div></section>')


def drawer(q):
    rows = "".join(f'<li><div><b>{esc(t)}</b><span>{esc(d)}</span></div>'
                   + (f'<small class="md-age {age_cls(a)}">{age_txt(a)}</small>' if a is not None else "")
                   + f'<button type="button" class="btn btn--sm btn--outline" popovertarget="md-cm-{q["key"]}">처리</button></li>'
                   for t, d, a in q["rows"])
    more = f'<p class="md-more">외 {q["n"] - len(q["rows"])}건 — 처리 화면에서 모두 보기</p>' if q["n"] > len(q["rows"]) else ""
    return (f'<aside class="md-dr" id="md-dr-{q["key"]}" popover aria-label="{q["name"]}">'
            f'<header><div><b>{q["name"]} {q["n"]}건</b><p>{esc(q["purpose"])}</p></div>'
            f'<button type="button" class="md-x" popovertarget="md-dr-{q["key"]}" popovertargetaction="hide" aria-label="닫기">✕</button></header>'
            f'<ul class="md-list">{rows}</ul>{more}'
            f'<footer><button type="button" class="btn btn--primary btn--sm" popovertarget="md-cm-{q["key"]}">처리 화면 열기</button>'
            f'<code>{esc(q["path"])}</code></footer></aside>')


def center(q):
    trs = "".join(f'<tr><td class="cell-strong">{esc(t)}</td><td>{esc(d)}</td><td>{age_txt(a) or "-"}</td>'
                  '<td class="text-right"><span class="btn btn--sm btn--outline">처리</span></td></tr>' for t, d, a in q["rows"])
    return (f'<div class="md-cm" id="md-cm-{q["key"]}" popover aria-label="{q["name"]} 처리 화면">'
            f'<header><b>{q["name"]} — 처리 화면</b><code>{esc(q["path"])}&amp;embed=1</code>'
            f'<button type="button" class="md-x" popovertarget="md-cm-{q["key"]}" popovertargetaction="hide" aria-label="닫기">✕</button></header>'
            '<div class="md-cm-b"><p class="md-cm-note">데모: 이 자리에 <b>실서버 처리 화면</b>이 embed 로 뜹니다(사이드바·탑바 없이). '
            '닫으면 대시보드가 그대로 있습니다.</p>'
            f'<table class="tbl"><thead><tr><th>대상</th><th>내용</th><th>경과</th><th></th></tr></thead><tbody>{trs}</tbody></table></div></div>')


def sys_drawer():
    trs = "".join(f'<li class="{"md-bad" if r == "fail" else ""}"><div><b class="mono">{n}</b><span>{esc(note)}</span>'
                  f'<span>예정 {at} · 마지막 {last}</span></div>'
                  f'<span class="badge {"badge--danger" if r == "fail" else "badge--success"}">{"실패" if r == "fail" else "정상"}</span></li>'
                  for n, at, last, r, note in CRON)
    sys_ = "".join(f'<li class="md-s-{st}"><span>{n}</span><b>{v}</b></li>' for n, v, st, _l in SYS)
    return ('<aside class="md-dr" id="md-dr-sys" popover aria-label="시스템 상태"><header><div><b>시스템 상태</b>'
            '<p>멈추면 아무도 모르는 것 — 10/27 크론이 소리 없이 멈춘 일이 있었습니다</p></div>'
            '<button type="button" class="md-x" popovertarget="md-dr-sys" popovertargetaction="hide" aria-label="닫기">✕</button></header>'
            '<p class="md-sub">핵심 크론 6개 — 예정 시각 · 마지막 실행 · 결과</p>'
            f'<ul class="md-list md-cron">{trs}</ul>'
            f'<p class="md-sub">그 밖의 신호</p><ul class="md-sys">{sys_}</ul>'
            '<footer><code>/system/automation.html · /system/automationLogView.html?code=settlementScan</code></footer></aside>')


def side_noti():
    trs = "".join(f'<li><span class="badge {cls}">{lab}</span><div><b>{esc(t)}</b><span>{esc(w)} · {tm}</span></div>'
                  f'<button type="button" class="btn btn--sm btn--outline" popovertarget="md-cm-{k}">처리</button></li>'
                  for k, lab, cls, t, w, tm in NOTI)
    up = "".join(f'<li><b>{d}</b><span>{esc(t)}</span></li>' for d, t, _l in UPCOMING)
    # [2026-11-13] 요청 "즉시 처리가 우측 패널에 고정되면 가운데 영역이 수시로 왔다갔다 하는 것을 막는다"
    #   실서버 오른쪽 패널(master.css 3859~ .modal-backdrop = 400px 판 + 본문 밀어내기) 마크업 그대로, 닫기 없이 늘 열림
    return (f'<aside class="modal-backdrop is-open md-pane" aria-label="즉시 처리 알림"><div class="modal">'
            f'<div class="modal__head"><span class="modal__title">즉시 처리 알림 <span class="badge badge--danger">{len(NOTI)}건</span></span>'
            f'<button type="button" class="btn btn--sm btn--ghost" popovertarget="md-stub-inbox">알림·작업 센터</button></div>'
            f'<div class="modal__body md-pane-b"><ul class="md-noti">{trs}</ul>'
            f'<div class="md-pane-h2"><b>다가오는 7일</b>'
            f'<button type="button" class="btn btn--sm btn--ghost" popovertarget="md-stub-calendar">운영 캘린더</button></div>'
            f'<ul class="md-up">{up}</ul></div></div></aside>')


def platform():
    steps = [("모집중", 86), ("모집완료", 12), ("선정완료", 31), ("체험중", 140), ("이번 달 완료", 64)]
    rows = [("가입", "오늘 <b>12</b> · 이번 달 <b>340</b>", "광고주 3 · 리뷰어 9 (오늘)"),
            ("대행사", "<b>18</b>곳 · 관리 업체 <b>412</b>", "신청 대기 2 · 이번 달 새 대행사 3"),
            ("캠페인", "오늘 등록 <b>9</b> · 심사 대기 3", " · ".join(f"{a} {b}" for a, b in steps)),
            ("리뷰어", "활동(30일) <b>3,214</b>명", "휴면 전환 예정 41 · 이용 제한 12"),
            ("광고주", "캠페인 진행 중 <b>187</b>곳", "이번 달 신규 28 · 정지 2")]
    trs = "".join(f'<tr><th scope="row">{a}</th><td>{b}<small class="md-kv-s">{c}</small></td></tr>' for a, b, c in rows)
    return (f'<section class="card md-half"><div class="card__head"><span class="card__title">플랫폼 현황</span>'
            f'<span class="cell-sub">요약 표 09:10 기준</span></div><table class="tbl md-kv"><tbody>{trs}</tbody></table></section>')


def money():
    rows = "".join(f'<tr><th scope="row">{a}</th><td><b>{v:,}</b>원<small class="md-kv-s">{esc(n)}</small></td></tr>' for a, v, n in MONEY)
    mx = max(r[1] for r in RECON)
    bars = "".join(f'<li><span>{m}</span><i class="md-b-in" style="width:{i / mx * 100:.0f}%" title="들어온 돈 {i}백만"></i>'
                   f'<i class="md-b-out" style="width:{o / mx * 100:.0f}%" title="나간 돈 {o}백만"></i>'
                   f'<em>수수료 {f}백만</em></li>' for m, i, o, f in RECON)
    return (f'<section class="card md-half"><div class="card__head"><span class="card__title">돈 흐름 · 11월</span>'
            f'<button type="button" class="btn btn--sm btn--ghost" popovertarget="md-stub-settlement">원장</button></div>'
            f'<table class="tbl md-kv"><tbody>{rows}</tbody></table>'
            '<p class="md-sub">6개월 — <i class="md-b-in md-key"></i>들어온 돈(충전) · <i class="md-b-out md-key"></i>나간 돈(지급·환불)</p>'
            f'<ul class="md-bars">{bars}</ul></section>')


def audit():
    trs = "".join(f'<tr><td class="cell-sub nowrap">{t}</td><td class="cell-strong">{w}</td><td><span class="badge badge--gray">{a}</span></td>'
                  f'<td class="cell-sub">{tg}</td><td>{esc(d)}</td></tr>' for t, w, a, tg, d in AUDIT)
    return ('<section class="card md-audit"><div class="card__head"><span class="card__title">최근 운영 활동</span>'
            '<button type="button" class="btn btn--sm btn--ghost" popovertarget="md-stub-audit-log">감사 로그 전체</button></div>'
            f'<table class="tbl"><thead><tr><th>일시</th><th>운영자</th><th>행위</th><th>대상</th><th>내용</th></tr></thead><tbody>{trs}</tbody></table></section>')


def ver(name):
    """[2026-11-13] CSS 주소에 내용 해시를 붙인다 — GitHub Pages 가 10분 캐시라 새 페이지 + 옛 CSS 가 섞여 보였음"""
    import hashlib
    return hashlib.md5((ROOT / "master" / "css" / name).read_bytes()).hexdigest()[:8]


def page():
    # [2026-11-13] 요청 "즉시 처리 알림은 기본이 우측 패널에서" — 오른쪽 패널 = 스크롤해도 붙어 있는 알림(대행사 대시보드의 오른쪽 패널과 같은 자리)
    body = (f'{head_line()}{sys_strip()}{board()}<div class="md-two">{platform()}{money()}</div>{audit()}{side_noti()}')
    overlays = "".join(drawer(q) + center(q) for q in QUEUES) + sys_drawer() + stubs()
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>대시보드 - 뷰마 MASTER (데모)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
<link rel="stylesheet" href="css/master.css?v={ver("master.css")}">
<link rel="stylesheet" href="css/md.css?v={ver("md.css")}">
</head>
<body data-page="dashboard">
<div class="dashboard md">
{sidebar()}
<main class="main-content">
{topbar()}
<div class="main-view">
<p class="md-demo">데모 — 뷰마 마스터 대시보드 기획안(2026-11-13) · 숫자는 모두 예시 · <a href="../dashboard.html">대행사 데모로</a></p>
{body}
</div>
</main>
</div>
{overlays}
</body>
</html>
'''


if __name__ == "__main__":
    OUT.write_text(page(), encoding="utf-8")
    print(f"written {OUT.relative_to(ROOT)} · 큐 {len(QUEUES)} (행동 {sum(q['kind'] == 'act' for q in QUEUES)})")
