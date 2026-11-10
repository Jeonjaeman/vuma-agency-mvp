# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.6] 캠페인 등록 · 복제 화면 (기획서 v0.6 6-5)
  1단계 = 업체 고르기(담당자는 업체 담당자로 자동) → 2~5단계 = 기존 광고주 사이트 등록 단계 그대로
    (admin/inc/campaign/campaignCreate.inc.html: 캠페인 설정 · 기본정보 · 유형별 안내(방문/배송/기자단) · 홍보내용)
  단계 이동 · 유형별 칸 바꾸기 · 보는 사람(관리자/담당자) 바꾸기 = 라디오 + CSS.
  비용 미리보기 계산 · 업체 검색 · 복제 채우기만 js/campaign_new.js.
"""
import json

import camp_data as D

P, G = D.P, D.G
esc = P.esc
ME = "psj"            # 시안의 '담당자로 보기' = 박서준(1팀)
STEPS = [(1, "업체 선택"), (2, "캠페인 설정"), (3, "기본정보"), (4, "유형별 안내"), (5, "홍보내용 · 확인")]
CATS = ["맛집", "카페", "뷰티", "헬스·운동", "교육", "생활", "반려동물", "여행·숙박", "식품", "기타"]
CHANNELS = ["블로그", "인스타", "유튜브", "릴스", "쇼츠", "클립", "틱톡", "구매평"]


def biz_cards():
    out = []
    for b in P.BIZS:
        x = P.extra(b)
        own = b["owner"]
        mine = " own" if own and own[0] == ME else ""
        who = (f'<span class="who"><i>{own[1][0]}</i>{own[1]}</span>' if own else '<span class="who none">미담당</span>')
        out.append(f'<label class="bpick{mine}" data-name="{esc(b["name"])} {x["ind"]} {x["reg"]}">'
                   f'<input type="radio" name="biz" value="{b["id"]}" data-owner="{own[1] if own else ""}" '
                   f'data-team="{own[3] if own else ""}" data-reg="{x["reg"]}" data-name="{esc(b["name"])}">'
                   f'<b>{esc(b["name"])}</b><span class="muted">{x["ind"]} · {x["reg"]}</span>'
                   f'<span class="bp-l3">{who}<small>진행 {len(b["camps"])}</small></span></label>')
    return "".join(out)


def step1():
    return f'''<div class="nstep ns-1">
		<h2 class="ns-t">1. 업체 선택 <small>담당자는 업체 담당자로 자동으로 정해집니다</small></h2>
		<div class="copybox">
			<p class="cb-t"><b>복제해서 만들기</b> <span class="muted">지난 캠페인 조건을 그대로 가져옵니다</span></p>
			<select class="input js-copy" aria-label="복제할 캠페인"><option value="">새로 만들기 (복제 안 함)</option>{copy_opts()}</select>
			<p class="cb-msg js-copy-msg" role="status" hidden></p>
		</div>
		<label class="search b-search"><span class="sr">업체 검색</span><input type="search" class="js-nsearch" placeholder="업체명·업종·지역"></label>
		<p class="staff-note">담당자로 보는 중 — <b>내 업체만</b> 고를 수 있습니다(팀장 = 팀 업체, 관리자 = 전체).</p>
		<div class="bpicks">{biz_cards()}</div>
		<p class="pick-sum js-pick-sum" role="status">업체를 고르세요</p>
	</div>'''


def copy_opts():
    groups = {}
    for c in D.CAMPS:
        if c["group"] != "draft":
            groups.setdefault(c["b"]["name"], []).append(c)
    return "".join(f'<optgroup label="{esc(n)}">' + "".join(
        f'<option value="{c["id"]}">{esc(c["name"])} · {c["round"]}회차 ({c["state"]})</option>' for c in cs) + '</optgroup>'
        for n, cs in groups.items())


def row(th, td, cls=""):
    return f'<tr{f" class={cls}" if cls else ""}><th>{th}</th><td>{td}</td></tr>'


def step2():
    types = "".join(f'<label class="tagr"><input type="radio" name="ctype" value="{t}" class="ty-{t}r"{" checked" if t == "v" else ""}>'
                    f'<span class="ty ty-{t}">{n}</span></label>' for t, n in G.TYPE_NAME.items())
    chans = "".join(f'<label class="tagr"><input type="radio" name="chan" value="{c}"{" checked" if c == "블로그" else ""}><span>{c}</span></label>'
                    for c in CHANNELS)
    cats = "".join(f"<option>{c}</option>" for c in CATS)
    rows = (row("캠페인명", '<input class="input wide js-cname" placeholder="예: 11월 방문 체험단"> <span class="js-round rnd">1회차</span>')
            + row("카테고리", f'<select class="input">{cats}</select>')
            + row("채널", f'<div class="tagrs">{chans}</div>')
            + row("유형", f'<div class="tagrs">{types}</div><p class="muted small">유형에 따라 4단계 안내 칸과 일정 이름이 바뀝니다</p>')
            + row("노출 지역", '<span class="js-reg muted">업체를 고르면 업체 주소로 자동</span>', "t-v-only")
            + row("모집 일정", '<input type="date" class="input" value="2026-11-11"> ~ <input type="date" class="input" value="2026-11-18">')
            + row("발표일", '<input type="date" class="input" value="2026-11-20"> <span class="muted small">선정 마감</span>')
            + row('<span class="lab-v">체험 일정</span><span class="lab-s">배송 시작일</span><span class="lab-p">원고 시작일</span>',
                  '<input type="date" class="input" value="2026-11-22">')
            + row("리뷰 마감", '<input type="date" class="input" value="2026-12-02">')
            + row("모집인원", '<input type="number" class="input num js-n" min="1" value="5"> 명 <span class="muted small">무료 등급 최대 30명</span>')
            + row("포인트 지급", '1인당 <input type="number" class="input num js-reward" min="0" step="1000" value="10000"> P'))
    return f'<div class="nstep ns-2"><h2 class="ns-t">2. 캠페인 설정</h2><p class="need-biz">먼저 1단계에서 업체를 고르세요.</p><table class="ftable">{rows}</table></div>'


def step3():
    rows = (row("대표이미지", '<input type="file" class="input" accept="image/*"> <span class="muted small">목록에 보이는 사진 1장</span>')
            + row("상세이미지", '<input type="file" class="input" accept="image/*" multiple> <span class="muted small">최대 10장</span>')
            + row("리뷰어 제공", '<textarea class="input" rows="3" placeholder="예: 2인 코스 식사권(6만 원 상당)"></textarea>'))
    return f'<div class="nstep ns-3"><h2 class="ns-t">3. 기본정보</h2><table class="ftable">{rows}</table></div>'


def step4():
    v = (row("플레이스 링크", '<input class="input wide" placeholder="https://map.naver.com/...">')
         + row("담당자 연락처", '<input class="input js-tel" placeholder="업체 정보에서 자동"> <span class="muted small">대행사 내부 정보 — 선정자에게만</span>')
         + row("주소", '<input class="input wide js-addr" placeholder="업체 주소로 자동">')
         + row("방문 및 예약안내", '<textarea class="input" rows="3" placeholder="예약 방법 · 방문 가능 시간 · 주차"></textarea>'))
    s = (row("제품 링크", '<input class="input wide" placeholder="https://smartstore...">')
         + row("배송방식", '<div class="tagrs"><label class="tagr"><input type="radio" name="ship" checked><span>택배</span></label>'
               '<label class="tagr"><input type="radio" name="ship"><span>직접 전달</span></label></div>'
               '<p class="muted small">선정자 배송정보는 선정자에게만, 신청 후 3개월까지(기존 규칙) · 발송 완료·운송장 기록은 대시보드 "체험 준비"</p>'))
    p = (row("링크", '<input class="input wide" placeholder="기사에 넣을 링크">')
         + row("전달 자료", '<input type="file" class="input" multiple> <span class="muted small">보도자료 · 이미지 · 가이드라인 — 선정자가 받아 갔는지 대시보드에서 봄</span>'))
    return (f'<div class="nstep ns-4"><h2 class="ns-t">4. <span class="lab-v">방문 및 예약안내</span><span class="lab-s">배송안내</span>'
            f'<span class="lab-p">기자단안내</span></h2>'
            f'<table class="ftable for-v">{v}</table><table class="ftable for-s">{s}</table><table class="ftable for-p">{p}</table></div>')


def step5():
    rows = (row("가이드라인/요청사항", '<textarea class="input" rows="4" placeholder="필수 키워드 · 사진 장수 · 글자 수 · 광고 표시"></textarea>')
            + row("추가 안내사항", '<textarea class="input" rows="2"></textarea>')
            + row("패널티 안내", '<p class="muted small">기한 내 미등록 · 무단 취소/노쇼 · 가이드 미준수는 기존 뷰마 패널티 정책을 따릅니다(신청 화면에 자동 표시).</p>'))
    return f'''<div class="nstep ns-5"><h2 class="ns-t">5. 홍보내용 · 확인</h2><table class="ftable">{rows}</table>
		<section class="cost" aria-labelledby="cost-t">
			<h3 id="cost-t" class="sec-t">비용 미리보기</h3>
			<dl class="rc-cost js-cost">
				<dt>리뷰어 지급 <small class="js-c-f"></small></dt><dd class="js-c-pay"></dd>
				<dt>플랫폼 수수료 <small>{int(D.FEE * 100)}%</small></dt><dd class="js-c-fee"></dd>
				<dt class="tot">예치 예정액</dt><dd class="tot js-c-total"></dd>
				<dt>사용 가능 잔액</dt><dd>{D.BALANCE:,}P</dd>
				<dt>등록 후 잔액</dt><dd class="js-c-after"></dd></dl>
			<p class="short js-short" hidden>잔액이 <b class="js-c-gap"></b> 모자랍니다 — 충전하거나 작성 중으로 저장해 두세요. 충전 후 [예치하고 진행] 한 번이면 시작됩니다.</p>
			<div class="acts wide">
				<button type="button" class="btn js-save">작성 중으로 저장</button>
				<button type="button" class="btn as-admin js-charge">충전하기</button>
				<button type="button" class="btn as-staff js-req">관리자에게 충전 요청</button>
				<button type="button" class="btn primary js-submit">등록하고 예치</button>
			</div>
		</section></div>'''


def summary():
    return f'''<div class="nsum">
	<h2 class="sec-t">요약</h2>
	<dl class="kv2">
		<dt>업체</dt><dd class="js-s-biz muted">—</dd>
		<dt>담당자</dt><dd class="js-s-own muted">업체를 고르면 자동</dd>
		<dt>캠페인</dt><dd class="js-s-name muted">—</dd>
		<dt>유형</dt><dd class="js-s-type">방문형 · 블로그</dd>
		<dt>인원 · 지급</dt><dd class="js-s-n">5명 × 10,000P</dd>
		<dt>예치 예정</dt><dd class="js-s-total">—</dd>
		<dt>잔액</dt><dd>{D.BALANCE:,}P</dd></dl>
	<p class="note">관리자·팀장·담당자 권한(8-3): 담당자는 내 업체만, 충전은 관리자에게 요청합니다.</p>
	<p class="muted small">시안: 저장되지 않습니다. 맨 위 [보는 사람]으로 관리자·담당자 화면을 바꿔 볼 수 있어요.</p>
</div>'''


def copy_data():
    """복제용 — 캠페인 id → 조건(JS 가 칸을 채움)"""
    return {c["id"]: {"biz": c["bid"], "name": c["name"], "ty": c["ty"], "ch": c["ch"], "n": c["n"],
                      "reward": c["reward"], "round": c["round"], "bname": c["b"]["name"]} for c in D.CAMPS}


def page():
    sr = "".join(f'<input type="radio" name="step" id="step-{i}" class="vr"{" checked" if i == 1 else ""}>' for i, _l in STEPS)
    ind = "".join(f'<label for="step-{i}" class="si si-{i}"><b>{i}</b><span>{lab}</span></label>' for i, lab in STEPS)
    nav = "".join(
        f'<div class="snav sn-{i}">'
        + (f'<label for="step-{i - 1}" class="btn">‹ 이전</label>' if i > 1 else '<a class="btn ghost" href="campaigns.html">취소</a>')
        + (f'<label for="step-{i + 1}" class="btn primary">다음 ›</label>' if i < len(STEPS) else "") + '</div>'
        for i, _l in STEPS)
    data = json.dumps({"bal": D.BALANCE, "fee": D.FEE, "camps": copy_data()}, ensure_ascii=False)
    body = f'''<section class="board cnew" aria-labelledby="t-new">
	<input type="radio" name="role" id="role-admin" class="vr" checked><input type="radio" name="role" id="role-staff" class="vr">
	{sr}
	<div class="board-h"><div><h1 id="t-new">캠페인 등록</h1>
		<p class="sub">1단계 업체 선택 → 이후는 광고주 사이트 등록 단계 그대로 · 담당자는 업체를 따름</p></div>
		<div class="seg sm role-seg" role="group" aria-label="보는 사람(시안)"><label for="role-admin">대표(관리자)로 보기</label><label for="role-staff">박서준(담당자)으로 보기</label></div></div>
	<nav class="steps" aria-label="등록 단계">{ind}</nav>
	<form class="nform" onsubmit="return false">
		{step1()}{step2()}{step3()}{step4()}{step5()}
		{nav}
	</form>
	<script type="application/json" id="new-data">{data}</script>
</section>'''
    return P.page("캠페인 등록", "camp", body, summary(), '<link rel="stylesheet" href="css/campaigns.css">', "campaign_new.js")
