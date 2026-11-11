# -*- coding: utf-8 -*-
"""
[2026-11-12 v0.9] 캠페인 등록 · 복제 화면 — 광고주 등록창(admin/inc/campaign/campaignCreate.inc.html)을 그대로
  · 마크업 · class · 단계 순서 · 칸 이름 · 안내 문구 · 선택지 = 광고주 등록창 그대로(값은 시안용 가짜)
  · 광고주 JS 가 바꾸던 상태(단계 이동 · 유형별 3단계 · 채널별 키워드 줄 · 펼치기/접기 · 지급/미지급 · 닫기 확인)
    = 숨은 라디오/체크박스 + :has() + popover → css/bridge/create.css
  · 대행사 추가분(업체 선택 · 복제 · 보는 사람 · 회차 · 충전 요청) = .add 점선 + ag- class → css/ag/create.css
  · 계산 · 복제 채우기 · 업체 검색 · 키워드 추가 · 지역 요약 = js/campaign_new.js (CSS 로 안 되는 것만)
  광고주 등록창은 캠페인 리스트 위에 뜨는 모달이다. [2026-11-12] 시안도 같게 — .modal-wrap.open 덮개 + 뒤에 캠페인 리스트(iframe).
"""
import json

import camp_data as D

P, G = D.P, D.G
esc = P.esc
ME = "psj"            # 시안의 '담당자로 보기' = 박서준(1팀)

# 광고주 선택지 — core/inc/taxonomyDefine.inc.php 기본값 · core/inc/define.inc.php
CATE = [(1, "맛집"), (2, "뷰티"), (3, "여행"), (12, "육아"), (4, "문화"), (5, "생활"), (6, "배달"), (7, "포장"),
        (8, "디지털"), (9, "반려동물"), (10, "식품"), (11, "기타")]
CHANNEL = [("BLOG", "블로그"), ("INSTARGRAM", "인스타"), ("YOUTUBE", "유튜브"), ("REELS", "릴스"), ("SHORTS", "쇼츠"),
           ("CLIP", "클립"), ("TIKTOK", "틱톡"), ("REVIEWS", "구매평")]
TYPES = [("1", "방문형"), ("2", "배송형"), ("3", "기자단"), ("999", "기타")]
TY_CODE = {"v": "1", "s": "2", "p": "3"}        # 대행사 시안 유형 → 광고주 유형 코드
CHARLEN = [800, 1000, 1200, 1500, 2000]
IMGCNT = list(range(1, 21))
VODCNT = [1, 2, 3]
GIFCNT = [1, 2, 3, 4, 5]

# 노출 지역 — 광고주 zoneList()/sigunguList() 는 DB 값. 시안은 시/도 17곳 + 업체 주소에 나오는 시군구 위주
ZONES = [
    (11, "서울", ["종로구", "중구", "용산구", "성동구", "광진구", "서대문구", "마포구", "양천구", "영등포구", "강남구", "송파구"]),
    (26, "부산", ["중구", "해운대구", "수영구", "부산진구"]), (27, "대구", ["중구", "수성구", "달서구"]),
    (28, "인천", ["중구", "연수구", "남동구"]), (29, "광주", ["동구", "서구", "북구"]), (30, "대전", ["중구", "서구", "유성구"]),
    (31, "울산", ["중구", "남구"]), (36, "세종", ["세종시"]),
    (41, "경기", ["수원시", "성남시", "고양시", "용인시", "평택시"]), (51, "강원", ["춘천시", "강릉시", "원주시"]),
    (43, "충북", ["청주시", "충주시", "제천시"]), (44, "충남", ["천안시", "아산시"]), (52, "전북", ["전주시", "군산시"]),
    (46, "전남", ["목포시", "여수시", "순천시"]), (47, "경북", ["포항시", "경주시"]), (48, "경남", ["창원시", "김해시"]),
    (50, "제주", ["제주시", "서귀포시"])]

# 광고주 기본 문구($conf*) — richTextArea() 를 지난 모양(<br> → 줄바꿈)
CONF_VISIT = ("★방문 2~3일전 반드시 예약 문의 후 방문 부탁 드립니다.\n예약 문의가 없을 시 체험이 불가능 할 수 있으니 유의 바랍니다.\n"
              "★예약 문의 시 꼭 '선정된 서비스명 (뷰마체험단) ㅇㅇㅇ'임을 밝혀주시길 바랍니다.\n★당일 체험 불가 / 예약 시 취소 될 수 있습니다.")
CONF_ABID = {
    "blog": "위의 키워드 중 제목, 본문, #태그에 아래와 같이 키워드를 기재해주세요.\n키워드가 지켜지지 않으면 수정요청이 있을 수 있어요.",
    "instar": "표시광고법에 따라 #협찬 해시태그를 맨앞에 표기해주세요.\n키워드가 지켜지지 않으면 수정요청이 있을 수 있어요.",
    "youtube": "표시광고법에 따라 영상 설명 맨 앞에 #협찬 을 표기해주세요.\n지정한 해시태그·검색 키워드를 제목과 설명에 포함해주세요.",
    "tiktok": "표시광고법에 따라 #협찬 해시태그를 맨앞에 표기해주세요.\n지정한 해시태그·검색 키워드를 본문에 포함해주세요.",
    "reviews": "구매평에 지정한 검색 키워드를 포함해주세요.\n대가를 받아 작성한 후기임을 함께 밝혀주세요."}
CONF_MISSION1 = ("● 예시) 메뉴와 오션뷰가 함께 보이도록 사진 촬영해주세요.\n"
                 "● 예시) 신선한 재료 사용, 데이트하기 좋은 분위기, 교통이 편리한 점을 본문에 함께 소개해주세요.")
CONF_MISSION2 = "● 본문 글자 수 1,300자 이상, 사진+동영상 10장 이상 첨부해 주세요.\n● 위치 정보(지도 첨부), 운영 시간을 반드시 함께 작성해 주세요."

# 신규 등록 기본 일정(광고주: 오늘 2026-11-11 기준 +1 · +7 · +8 · +9 · +16, 결과발표 = 방문형 리뷰마감 다음 날)
DATES = {"recruitSTDate": "2026-11-12", "recruitEDDate": "2026-11-18", "announceDate": "2026-11-19",
         "deliveryDate": "2026-11-19", "campaignSTDate": "2026-11-20", "campaignEDDate": "2026-11-27", "resultDate": "2026-12-05"}


def tag(kind, name, value, text, checked=False, check_cls="cc-tag-check", attr=""):
    """광고주 .cc-tag-label (라디오/체크박스 태그 모양)"""
    on = " checked" if checked else ""
    return (f'<label class="cc-tag-label"><input type="{kind}" name="{name}" value="{value}"{on}{attr}>'
            f'<span class="{check_cls}"></span><span class="cc-tag-text">{text}</span></label>')


def date_box(name, ph):
    return (f'<div class="date-input-box"><input type="text" class="cc-input" placeholder="{ph}" name="{name}" id="{name}" '
            f'value="{DATES[name]}"><span class="material-symbols-outlined date-icon">calendar_today</span></div>')


def fold_btn(btn_id, box_id, label="펼쳐서 작성"):
    """광고주 '펼쳐서 작성 / 접기' 버튼(campaign.js *DetailToggle) → 숨은 체크박스 + label. 글자 두 벌을 CSS 가 바꿔 보여 준다"""
    return (f'<input type="checkbox" id="{box_id}" hidden>'
            f'<label class="cc-btn-sub" id="{btn_id}" for="{box_id}"><span>{label}</span><span>접기</span></label>')


# ════════════════════════ 대행사 추가분 ════════════════════════
def biz_cards():
    out = []
    for b in P.BIZS:
        x = P.extra(b)
        own = b["owner"]
        mine = " ag-own" if own and own[0] == ME else ""
        who = (f'<span class="ag-who"><i>{own[1][0]}</i>{own[1]}</span>' if own else '<span class="ag-who ag-who--none">미담당</span>')
        out.append(f'<label class="ag-bpick{mine}" data-q="{esc(b["name"])} {x["ind"]} {x["reg"]}">'
                   f'<input type="radio" name="agBiz" value="{b["id"]}" data-owner="{own[1] if own else ""}" '
                   f'data-team="{own[3] if own else ""}" data-reg="{x["reg"]}" data-tel="{x["tel"]}" data-name="{esc(b["name"])}">'
                   f'<b class="ag-bpick__name">{esc(b["name"])}</b><span class="ag-bpick__meta">{x["ind"]} · {x["reg"]}</span>'
                   f'<span class="ag-bpick__foot">{who}<small>진행 {len(b["camps"])}</small></span></label>')
    return "".join(out)


def copy_opts():
    groups = {}
    for c in D.CAMPS:
        if c["group"] != "draft":
            groups.setdefault(c["b"]["name"], []).append(c)
    return "".join(f'<optgroup label="{esc(n)}">' + "".join(
        f'<option value="{c["id"]}">{esc(c["name"])} · {c["round"]}회차 ({c["state"]})</option>' for c in cs) + '</optgroup>'
        for n, cs in groups.items())


def ag_bizpick():
    """1단계 맨 앞 — 어느 업체 캠페인인지(담당자 자동) + 복제. 광고주 등록창에는 없는 칸"""
    return f'''<div class="add ag-bizpick" role="group" aria-labelledby="agBizpickT">
							<p class="ag-bizpick__head" id="agBizpickT"><b>업체 선택</b><span>담당자는 업체 담당자로 자동으로 정해집니다 · 대행사 추가</span></p>
							<div class="ag-copy">
								<label class="ag-copy__label" for="agCopy"><b>복제해서 만들기</b> 지난 캠페인 조건을 그대로 가져옵니다</label>
								<select class="ag-copy__sel" id="agCopy"><option value="">새로 만들기 (복제 안 함)</option>{copy_opts()}</select>
								<p class="ag-copy__msg" id="agCopyMsg" role="status" hidden></p>
							</div>
							<label class="ag-bizsearch"><span class="ag-sr">업체 검색</span><input type="search" id="agBizSearch" placeholder="업체명·업종·지역"></label>
							<p class="ag-staffnote">담당자로 보는 중 — <b>내 업체만</b> 고를 수 있습니다(팀장 = 팀 업체, 관리자 = 전체).</p>
							<div class="ag-bpicks">{biz_cards()}</div>
							<p class="ag-pick-sum" id="agPickSum" role="status">업체를 고르세요</p>
						</div>'''


def ag_bar():
    """창 위 — 보는 사람(시안) · 고른 업체/담당자 요약"""
    return '''<div class="add ag-cnew-bar">
		<div class="ag-roleseg" role="group" aria-label="보는 사람(시안)"><label for="agRoleAdmin">대표(관리자)로 보기</label><label for="agRoleStaff">박서준(담당자)으로 보기</label></div>
		<dl class="ag-sum"><dt>업체</dt><dd id="agSumBiz">—</dd><dt>담당자</dt><dd id="agSumOwn">업체를 고르면 자동</dd></dl>
		<p class="ag-cnew-note">아래 창 = 광고주 캠페인 등록 화면 그대로 · 점선 = 대행사 추가분 · 시안이라 저장되지 않습니다</p>
	</div>'''


# ════════════════════════ 1단계 캠페인 설정 ════════════════════════
def zone_rows():
    out = []
    for key, sido, gus in ZONES:
        items = "".join(f'<label class="p-tag-label"><input type="checkbox" name="area[]" parentArea="{key}" value="{key}{i:03d}" '
                        f'areaName="{gu}"><span>{gu}</span></label>' for i, gu in enumerate(gus, 1))
        out.append(f'''<div class="p-region-row">
														<button type="button" class="p-region-head" aria-expanded="false">
															<span class="p-region-head__name">{sido}</span>
															<span class="p-region-head__count" data-zone-count></span>
															<span class="p-region-head__arrow" aria-hidden="true">▾</span>
														</button>
														<div class="p-region-body" data-zone-items hidden>
															<label class="p-tag-label"><input type="checkbox" name="area[]" parentArea="" value="{key}" areaName="{sido}"><span>{sido}전체</span></label>{items}
														</div>
													</div>''')
    return "".join(out)


def zone_row():
    return f'''<tr id="zoneRow">
							<th>노출 지역</th>
							<td>
								<label class="cc-tag-label">
									<input type="checkbox" name="noRegion" id="noRegion" value="Y">
									<span class="cc-tag-check"></span>
									<span class="cc-tag-text">관심지역 설정하지 않음</span>
								</label>
								<p class="upload-help cc-ml-0" style="margin:6px 0 0;">
									※ 지역을 설정하면 <strong>그 지역을 관심지역으로 둔 리뷰어에게만</strong> 노출됩니다.
									(메인 '관심지역 캠페인' · 채널별 목록 · 캠페인 상세의 추천 모두)<br>
									※ 설정하지 않으면 지역과 상관없이 전체 리뷰어에게 노출됩니다. (전국 발송·온라인 캠페인은 설정하지 않는 편이 모집에 유리합니다)
								</p>
								<div id="zonePickWrap" style="margin-top:10px;">
									<div class="cc-flex-row cc-gap-15" style="align-items:center;flex-wrap:wrap;">
										<span class="cc-input" id="zonePicked" style="flex:1;min-width:0;background:#f7f7f7;">주소를 입력하면 지역이 선택됩니다.</span>
										{fold_btn("zoneToggle", "ccZoneOpen", "펼쳐서 수정")}
									</div>
									<div id="zoneArea" style="margin-top:10px;">
										<div class="p-region">
											<div class="p-region-table">{zone_rows()}</div>
										</div>
									</div>
								</div>
							</td>
						</tr>'''


def step1():
    cates = "".join(tag("radio", "category", k, v, k == 1) for k, v in CATE)
    chans = "".join(tag("checkbox", "channel[]", k, v, k == "BLOG") for k, v in CHANNEL)
    types = "".join(tag("radio", "campaignType", k, v, k == "1") for k, v in TYPES)
    period = ('<span data-ty-label="visit">체험 일정</span><span data-ty-label="delivery">리뷰등록기간</span>')
    return f'''<div class="step-content step1">
					<h4 class="step-title">1.캠페인 설정</h4>
					{ag_bizpick()}
					<table class="form-table">
						<tr><th>숨김</th><td><div class="input-with-btn"><input type="checkbox" name="campaignHidden" value="Y"> 캠페인 숨김</div></td></tr>
						<tr>
							<th>캠페인명</th>
							<td>
								<div class="input-with-btn">
									<input type="text" class="cc-input" placeholder="캠페인명을 입력해주세요. (32자 이내)" name="campaignName" id="campaignName" value="">
									<span class="add ag-round" id="agRound" title="대행사 추가 — 같은 업체로 복제하면 회차 +1">1회차</span>
									<button type="button" class="cc-btn-sub" id="ccLoadBtn">이전 캠페인 불러오기</button>
								</div>
							</td>
						</tr>
						<tr><th>카테고리</th><td><div class="cc-tag-group">{cates}</div></td></tr>
						<tr><th>채널</th><td><div class="cc-tag-group">{chans}</div></td></tr>
						<tr><th>유형</th><td><div class="cc-tag-group">{types}</div></td></tr>
						{zone_row()}
						<tr>
							<th>모집 일정</th>
							<td><div class="date-range-wrap">{date_box("recruitSTDate", "모집시작일")}<span>부터</span>{date_box("recruitEDDate", "모집마감일")}<span>까지</span></div></td>
						</tr>
						<tr><th>발표일</th><td><div class="date-range-wrap">{date_box("announceDate", "발표일")}</div></td></tr>
						<tr id="deliveryDateRow"><th>배송시작일</th><td><div class="date-range-wrap">{date_box("deliveryDate", "배송시작일")}</div></td></tr>
						<tr id="campaignPeriodRow">
							<th id="campaignPeriodLabel">{period}</th>
							<td><div class="date-range-wrap">{date_box("campaignSTDate", "체험시작일")}<span>부터</span>{date_box("campaignEDDate", "체험마감일")}<span>까지</span></div></td>
						</tr>
						<tr>
							<th>결과발표</th>
							<td>
								<div class="date-range-wrap">{date_box("resultDate", "결과발표일")}</div>
								<span class="cc-text-lightgray" style="display:block;margin-top:8px;">리뷰 등록이 끝난 뒤 캠페인 결과를 발표하는 날입니다. (비워두면 리뷰어 화면에 표시되지 않습니다.)</span>
							</td>
						</tr>
						{point_rows()}
					</table>
				</div>'''


def point_rows():
    fee_pct = f"{int(D.FEE * 100)}%"
    return f'''<tr>
							<th>모집인원</th>
							<td><div class="recruit-count-box"><input type="text" class="cc-input" name="cnt" id="cnt" data-format="number" inputmode="numeric" value="0"> 명
								* 0인 경우 무제한입니다.</div></td>
						</tr>
						<tr>
							<th>포인트 지급</th>
							<td>
								<div class="recruit-count-box">
									{tag("radio", "rewards", "Y", "지급")}{tag("radio", "rewards", "N", "미지급", True)}
									<span id="rewardPointWrap">
										1인당 <input type="text" class="cc-input" name="rewardPoint" id="rewardPoint" value="0" data-format="number" inputmode="numeric"> P
									</span>
								</div>
							</td>
						</tr>
						<tr id="usePointRow">
							<th>총사용 포인트</th>
							<td>
								<div class="input-with-btn">
									<input type="text" class="cc-input cc-input-sm" id="usePoint" value="0" readonly>
									<span class="cc-fs-13 cc-text-gray" id="usePointHint">P (모집인원 0 x 지급포인트 0 x 수수료 {fee_pct})</span>
								</div>
							</td>
						</tr>
						<tr id="myBalanceRow">
							<th>보유 포인트</th>
							<td>
								<div class="input-with-btn">
									<span class="cc-fs-13" id="myBalanceText"><b>{D.BALANCE:,}</b> P</span>
									<a class="cc-btn-sub badge-radius br-black" href="point.html">포인트 충전</a>
									<span class="add ag-chargereq"><button type="button" class="ag-btn-sub" id="agChargeReq">관리자에게 충전 요청</button></span>
									<span class="cc-fs-13 cc-text-gray" id="pointShortMsg" style="display:none;color:#e5484d;">잔액이 총사용포인트보다 부족합니다. 충전 후 등록해 주세요.</span>
								</div>
								<input type="hidden" id="myBalance" value="{D.BALANCE}">
								<input type="hidden" id="reservedHold" value="0">
								<input type="hidden" id="feeRate" value="{D.FEE}">
								<input type="hidden" id="feeText" value="{fee_pct}">
							</td>
						</tr>'''


# ════════════════════════ 2단계 기본정보 ════════════════════════
HELP = 'class="cc-help" style="margin:0 0 8px;font-size:13px;color:#0e0e0e;line-height:1.7;"'
STRONG = 'style="color:#0e0e0e;"'


def step2():
    return f'''<div class="step-content step2">
					<h4 class="step-title">2.기본정보</h4>
					<table class="form-table">
						<tr>
							<th>대표이미지</th>
							<td>
								<p {HELP}>
									권장 <strong {STRONG}>900 × 600px (가로:세로 3:2)</strong> · 최소 600 × 400px · JPG·PNG, 2MB 이하<br>
									목록에서는 <strong {STRONG}>3:2 로 잘려</strong> 보입니다. 글자가 들어간 이미지는 가장자리가 잘리지 않게 여백을 두세요.
								</p>
								<div class="cc-flex-row cc-gap-15">
									<label class="upload-box" id="mainImgBtnArea">
										<span class="material-symbols-outlined">image</span>
										<span class="cc-fw-500">이미지 첨부</span>
										<input type="file" accept="image/*" name="mainImg" id="mainImg" hidden>
									</label>
								</div>
							</td>
						</tr>
						<tr>
							<th>상세이미지</th>
							<td>
								<p {HELP}>
									권장 <strong {STRONG}>가로 1000px</strong> (최소 800px) · 세로는 제한 없음 · JPG·PNG, 장당 2MB 이하<br>
									상세 화면에서 <strong {STRONG}>본문 폭에 맞춰 늘어납니다.</strong> 가로가 작으면 흐리게 보입니다.
									여러 장은 올린 순서대로 이어서 나옵니다.
								</p>
								<div class="cc-flex-column">
									<label class="cc-form-group cc-gap-15">
										<span class="cc-btn-sub cc-btn-sub-sm">이미지 첨부</span>
										<input type="file" accept="image/*" name="detailImgFile" id="detailImgFile" hidden>
									</label>
									<div class="upload-grid" id="detailImgArea"></div>
								</div>
							</td>
						</tr>
						<tr>
							<th>리뷰어 제공</th>
							<td>
								<div class="cc-flex-column cc-gap-15">
									<div class="cc-form-group">
										<span class="cc-sub-title">제공내용</span>
										<input type="text" class="cc-input" name="reviewerOffer" id="reviewerOffer" placeholder="5만원 상당 자유 체험권" value="">
									</div>
									<div class="cc-form-group align-start">
										<span class="cc-sub-title">제공내용상세</span>
										<div style="flex:1;min-width:0;">
											{fold_btn("offerDetailToggle", "ccOfferOpen")}
											<div id="offerDetailArea" style="margin-top:10px;">
												<textarea name="reviewerAbidance" id="reviewerAbidance" class="cc-editor-area"></textarea>
											</div>
										</div>
									</div>
								</div>
							</td>
						</tr>
					</table>
				</div>'''


# ════════════════════════ 3단계 유형별 안내 ════════════════════════
def addr_row():
    return '''<tr id="addrRow">
							<th>주소</th>
							<td>
								<div class="cc-flex-column cc-input-md">
									<div class="cc-form-group">
										<input type="text" class="cc-input cc-input-zip" name="zipCode" placeholder="12345" value="" readonly>
										<button type="button" class="cc-btn-sub" id="ccZipBtn">우편번호</button>
									</div>
									<input type="text" class="cc-input" placeholder="주소" name="addr1" id="addr1" value="" readonly>
									<input type="text" class="cc-input" placeholder="상세주소" name="addr2" value="">
								</div>
							</td>
						</tr>'''


def visit_row():
    return f'''<tr id="visitRow">
							<th>방문 및 예약안내</th>
							<td>
								<div class="cc-flex-column cc-gap-15">
									<input type="hidden" name="visitOpt" id="visitOpt" value="dicker">
									<input type="hidden" name="visitAbidanceType" id="visitAbidanceType" value="D">
									<div class="cc-flex-column visit-specific-detail">
										<div class="cc-form-group align-start">
											<span class="cc-sub-title cc-fw-700 cc-text-black">체험시간</span>
											<textarea class="cc-input cc-area-wide" name="campaignTime" id="campaignTime" placeholder="예) 주중 13:00 ~ 18:00"></textarea>
										</div>
										<div class="cc-form-group align-start">
											<span class="cc-sub-title cc-fw-700 cc-text-black">휴무일</span>
											<textarea class="cc-input cc-area-wide" name="closedDate" id="closedDate" placeholder="예) 주말 또는 연중무휴"></textarea>
										</div>
										<div class="cc-form-group align-start">
											<span class="cc-sub-title cc-fw-700 cc-text-black">준수사항</span>
											<div id="visitAbidanceArea">
												{fold_btn("visitDetailToggle", "ccVisitOpen")}
												<span class="cc-fs-14" style="margin-left:8px;color:#0e0e0e;">방문 시 지켜야 할 내용이 있을 때만 적으세요.</span>
												<div id="visitDetailArea" style="margin-top:10px;">
													<textarea name="visitAbidance" id="visitAbidance" class="cc-editor-area" def="{esc(CONF_VISIT)}"></textarea>
												</div>
											</div>
										</div>
									</div>
								</div>
							</td>
						</tr>'''


def link_input(name, ph, id_=None):
    return f'<input type="text" class="cc-input cc-input-md" name="{name}" id="{id_ or name}" placeholder="{ph}" value="">'


def step3():
    naver = "https://naver.me/abc1234"
    visit = (f'<tr><th>플레이스 링크</th><td>{link_input("shopLink", naver)}</td></tr>'
             f'<tr><th>담당자 연락처</th><td>{link_input("phone", "예) 010-0000-0000")}</td></tr>' + addr_row() + visit_row())
    ship = (f'<tr><th>제품 링크</th><td>{link_input("goodsLink", naver)}</td></tr>'
            f'<tr><th>배송방식</th><td>{link_input("deliveryMethod", "예)택배, 순차발송")}</td></tr>')
    press = f'<tr><th>링크</th><td>{link_input("referenceLink", naver)}</td></tr>'
    etc = f'<tr><th>제품 링크</th><td>{link_input("referenceLink", naver, "referenceLink999")}</td></tr>'
    panels = [("campaignType0", "3.방문 및 예약안내", visit), ("campaignType1", "3.배송안내", ship),
              ("campaignType2", "3.기자단안내", press), ("campaignType999", "3.기타안내", etc)]
    return "".join(f'<div class="step-content step3 {c}"><h4 class="step-title">{t}</h4><table class="form-table">{rows}</table></div>'
                   for c, t, rows in panels)


# ════════════════════════ 4단계 홍보내용 ════════════════════════
def tag_box(label, inp_id, ph, list_id, list_cls="cc-hashtag-list", extra_btn=""):
    sub = f'<span class="cc-sub-title">{label}</span>' if label else ""
    return (f'<div class="cc-form-group cc-input-md">{sub}<input type="text" class="cc-input" placeholder="{ph}" id="{inp_id}">'
            f'<button type="button" class="cc-btn-sub">추가</button>{extra_btn}</div><div class="{list_cls}" id="{list_id}"></div>')


def people(name, ph):
    return (f'<div class="cc-form-group cc-input-md"><span class="cc-sub-title">사람태그</span>'
            f'<input type="text" class="cc-input" name="{name}" id="{name}" placeholder="{ph}" value=""></div>')


def abid_row(cls, key, row_id=""):
    rid = f' id="{row_id}"' if row_id else ""
    return f'''<tr{rid} class="{cls}"><td><div class="cc-flex-column cc-gap-15">
								<div class="cc-tag-group"><span class="cc-sub-title">준수사항</span>{tag("radio", key + "AbidanceType", "D", "기본내용")}{tag("radio", key + "AbidanceType", "N", "없음", True)}</div>
								<div class="guide-box" id="{key}AbidanceArea"><textarea name="{key}Abidance" id="{key}Abidance" class="cc-editor-area" def="{esc(CONF_ABID[key])}"></textarea></div>
							</div></td></tr>'''


def kw_group(cls, th, hint, body, key, ids=("", "")):
    rid = f' id="{ids[0]}"' if ids[0] else ""
    return (f'<tr{rid} class="{cls}"><th rowspan="2">{th}<span class="cc-th-hint">{hint}</span></th>'
            f'<td><div class="cc-flex-column cc-gap-12">{body}</div></td></tr>' + abid_row(cls, key, ids[1]))


def kw_rows():
    rel = '<button type="button" class="cc-btn-sub badge-radius br-black" id="ccKwSearch">연관키워드검색</button>'
    blog = tag_box("", "addkeyword", "키워드 입력", "keywordListArea", "cc-keyword-list", rel)
    insta = tag_box("해시태그", "addhashtag", "키워드 입력", "hashtagListArea") + people("instarPeopleTag", "예) @instagram_id")
    tube = (tag_box("해시태그", "add_youtubeHashtag", "해시태그 입력", "youtubeHashtagListArea")
            + tag_box("검색 키워드", "add_youtubeKeyword", "검색 키워드 입력", "youtubeKeywordListArea") + people("peopleTag", "예) @channelname"))
    tik = (tag_box("해시태그", "add_tiktokHashtag", "해시태그 입력", "tiktokHashtagListArea")
           + tag_box("검색 키워드", "add_tiktokKeyword", "검색 키워드 입력", "tiktokKeywordListArea"))
    rev = tag_box("검색 키워드", "add_reviewsKeyword", "검색 키워드 입력", "reviewsKeywordListArea")
    return (kw_group("js-kw-blog", "블로그키워드", "블로그·클립", blog, "blog")
            + kw_group("js-kw-insta", "인스타키워드", "인스타·릴스", insta, "instar")
            + kw_group("js-kw-youtube", "유튜브키워드", "유튜브·쇼츠", tube, "youtube", ("kwTubeRow1", "kwTubeRow2"))
            + kw_group("js-kw-tiktok", "틱톡키워드", "틱톡", tik, "tiktok", ("kwTikRow1", "kwTikRow2"))
            + kw_group("js-kw-reviews", "구매평키워드", "구매평", rev, "reviews", ("kwRevRow1", "kwRevRow2")))


def mission_grid():
    simple = [("keyword", "키워드 필수"), ("banner", "배너 필수"), ("link", "링크 필수"), ("map", "지도 필수")]
    sub = [("char", "글자 수", "charLen", CHARLEN, "자 이상"), ("img", "이미지", "imgCnt", IMGCNT, "개 이상"),
           ("vod", "영상", "vodCnt", VODCNT, "개 이상"), ("gif", "GIF", "gifCnt", GIFCNT, "개 이상")]
    chk = "cc-tag-check badge-radius"
    out = "".join(f'<div class="mission-item">{tag("checkbox", "mission[]", v, t, check_cls=chk)}</div>' for v, t in simple)
    for v, t, sel, opts, unit in sub:
        o = "".join(f'<option value="{x}">{x}</option>' for x in opts)
        out += (f'<div class="mission-item">{tag("checkbox", "mission[]", v, t, check_cls=chk)}'
                f'<div class="mission-sub"><select name="{sel}">{o}</select> {unit}</div></div>')
    return f'<div class="mission-grid">{out}</div>'


def step4():
    return f'''<div class="step-content step4">
					<h4 class="step-title">4.홍보내용</h4>
					<table class="form-table">
						{kw_rows()}
						<tr>
							<th>가이드라인/요청사항</th>
							<td>
								<div class="cc-flex-column cc-gap-15">
									{mission_grid()}
									<div class="guide-box white">
										<span class="upload-help cc-ml-0 cc-text-orange cc-mb-10 cc-db">리뷰어가 홍보해야 할 내용(촬영·본문 가이드)을 작성하세요.</span>
										<div class="cc-text-darkgray cc-fs-13"><textarea name="reviewMission1" id="reviewMission1" class="cc-editor-area">{esc(CONF_MISSION1)}</textarea></div>
									</div>
								</div>
							</td>
						</tr>
						<tr>
							<th>추가 안내사항</th>
							<td>
								<div>
									{fold_btn("extraDetailToggle", "ccExtraOpen")}
									<span class="cc-fs-14" style="margin-left:8px;color:#0e0e0e;">리뷰어 상세의 '추가안내사항' 으로 노출됩니다.</span>
								</div>
								<div class="guide-box white" id="extraDetailArea" style="margin-top:10px;">
									<span class="upload-help cc-ml-0 cc-text-orange cc-mb-10 cc-db">리뷰어에게 추가로 안내할 내용을 작성하세요.</span>
									<div class="cc-text-darkgray cc-fs-13"><textarea name="reviewMission2" id="reviewMission2" class="cc-editor-area">{esc(CONF_MISSION2)}</textarea></div>
								</div>
							</td>
						</tr>
					</table>
					{penalty_notice()}
				</div>'''


# 광고주 패널티 규칙 — 마스터(정책 → 패널티 규칙) 값. 시안 숫자
PN_ROWS = [("모집 완료 후 캠페인 숨김·취소", "모집을 마친 뒤 숨기거나 취소하면 자동으로 부여됩니다", 3),
           ("제공내역 다름", "", 2), ("방문 거부/무시", "", 3), ("과도한 추가요구", "", 2), ("포인트 미지급", "", 3),
           ("허위 캠페인", "", 5), ("부적절한 언행", "", 2)]
PN_THR = [(5, "7일 이용 제한"), (10, "30일 이용 제한"), (15, "영구 이용 제한")]
PN_STYLE = """<style>
	/* 패널티 규정 안내 — core/inc/penaltyNotice.inc.php 짝 (세 사이트 공용이라 값으로 적는다) */
	.pn-notice{ margin:20px 0 0; border:1px solid #ececf2; border-radius:8px; background:#fafafc; text-align:left; }
	.pn-notice__head{ display:flex; flex-direction:column; gap:4px; padding:14px 16px; cursor:pointer; list-style:none; }
	.pn-notice__head::-webkit-details-marker{ display:none; }
	.pn-notice__title{ font-size:14px; font-weight:700; color:#1a1a1a; }
	.pn-notice__title::after{ content:"펼치기"; margin-left:8px; font-size:12px; font-weight:500; color:#7346f3; }
	.pn-notice[open] .pn-notice__title::after{ content:"접기"; }
	.pn-notice__lead{ font-size:13px; color:#1b1b1b; line-height:1.6; }
	.pn-notice__body{ padding:0 16px 14px; }
	.pn-notice__table{ width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }
	.pn-notice__cap{ text-align:left; padding:0 0 6px; font-size:12px; font-weight:700; color:#1b1b1b; }
	.pn-notice__table th,
	.pn-notice__table td{ padding:8px 0; border-top:1px solid #ececf2; vertical-align:top; line-height:1.5; }
	.pn-notice__table th{ font-weight:600; color:#333; }
	.pn-notice__table td{ width:30%; text-align:right; color:#c0392b; font-weight:600; white-space:nowrap; }
	.pn-notice__detail{ display:block; margin-top:2px; font-size:12px; font-weight:400; color:#1b1b1b; }
	.pn-notice__foot{ margin:10px 0 0; font-size:12px; color:#1b1b1b; line-height:1.7; }
	.pn-notice__more{ margin-left:6px; color:#7346f3; font-weight:600; text-decoration:underline; }
</style>"""


def penalty_notice():
    """core/inc/penaltyNotice.inc.php ($pnTarget = advertiser) 그대로 — <details> 라 JS 없음. 모양도 조각 안 <style> 그대로"""
    rows = "".join(f'<tr><th scope="row">{r}' + (f'<span class="pn-notice__detail">{d}</span>' if d else "")
                   + f'</th><td>{p}점</td></tr>' for r, d, p in PN_ROWS)
    thr = "".join(f'<tr><th scope="row">누적 {p}점 이상</th><td>{t}</td></tr>' for p, t in PN_THR)
    return f'''<details class="pn-notice">
	<summary class="pn-notice__head">
		<span class="pn-notice__title">광고주 패널티 규정</span>
		<span class="pn-notice__lead">약속을 지키지 않으면 패널티가 쌓이고, 일정 점수를 넘으면 서비스 이용이 제한됩니다.</span>
	</summary>
	<div class="pn-notice__body">
		<table class="pn-notice__table"><caption class="pn-notice__cap">이럴 때 패널티가 부여됩니다</caption>{rows}</table>
		<table class="pn-notice__table"><caption class="pn-notice__cap">누적 점수에 따른 제한</caption>{thr}</table>
		<p class="pn-notice__foot">
			부득이하게 일정을 지킬 수 없다면 미리 고객센터(1:1 문의)로 알려 주세요.
			<a href="penalty.html" class="pn-notice__more" target="_blank" rel="noopener">내 패널티 보기</a>
		</p>
	</div>
</details>
{PN_STYLE}'''


# ════════════════════════ 틀 · 단계 · 버튼 ════════════════════════
STEPS = [(1, "캠페인 설정"), (2, "기본정보"), (3, None), (4, "홍보내용")]
STEP3_LABEL = "".join(f'<span data-ty-label="{k}">{v}</span>' for k, v in
                      [("1", "방문 및 예약안내"), ("2", "배송안내"), ("3", "기자단안내"), ("999", "기타안내")])


def indicator():
    """광고주 .step-indicator — div onclick(moveCreateStep) → label for=단계 라디오"""
    items = []
    for i, lab in STEPS:
        text = f'<div class="step-label" id="step3Label">{STEP3_LABEL}</div>' if i == 3 else f'<div class="step-label">{lab}</div>'
        items.append(f'<label class="step-item" for="ccStep{i}"><div class="step-num">{i}</div>{text}</label>')
    return '<div class="step-indicator">' + '<div class="step-line"></div>'.join(items) + '</div>'


def footer():
    """광고주 이전/다음 버튼은 하나씩이고 JS 가 단계마다 바꾼다 → 단계별 label 을 두고 지금 단계 것만 보인다(data-on)"""
    prev = "".join(f'<label class="btn-cc btn-cc-black btn-prev-step" for="ccStep{i - 1}" data-on="{i}">이전</label>' for i in (2, 3, 4))
    nxt = "".join(f'<label class="btn-cc btn-cc-primary btn-next-step" for="ccStep{i + 1}" data-on="{i}">다음</label>' for i in (1, 2, 3))
    return f'''<div class="create-modal-footer">
				<div class="btn-cc-wrap">
					<button type="button" class="btn-cc btn-cc-white" id="ccTempSave">임시저장</button>
					<div class="cc-flex-end">
						{prev}{nxt}
						<button type="button" class="btn-cc btn-cc-primary btn-next-step" data-on="4" id="ccSubmit">캠페인 등록</button>
					</div>
				</div>
			</div>'''


def hidden_inputs():
    names = ["detailImg", "detailDel", "mainDel"]
    ids = ["keyword", "hashtag", "youtubeHashtag", "youtubeKeyword", "tiktokHashtag", "tiktokKeyword", "reviewsKeyword", "geocodeX", "geocodeY"]
    return ('<input type="hidden" name="tempCode" value="temp_20261111"><input type="hidden" name="mstrCode" value="0">'
            '<input type="hidden" name="loadMstrCode" value="0"><input type="hidden" name="processType" id="processType" value="write">'
            '<input type="hidden" name="step" id="step" value="1">'
            + "".join(f'<input type="hidden" name="{n}" value="">' for n in names)
            + "".join(f'<input type="hidden" name="{n}" id="{n}" value="">' for n in ids)
            + '<input type="hidden" name="addrUpdate" id="addrUpdate" value="N">')


def close_confirm():
    """광고주 닫기 확인(#ccCloseConfirm.open, campaign.js requestCloseCampaignCreate) → popover"""
    return '''<div class="cc-close-confirm" id="ccCloseConfirm" popover>
		<div class="cc-close-confirm__box">
			<p class="cc-close-confirm__title">작성 중인 내용이 있습니다</p>
			<p class="cc-close-confirm__desc">저장하지 않고 닫으면 작성한 내용이 사라집니다.<br />어떻게 할까요?</p>
			<div class="cc-close-confirm__btns">
				<a class="btn-cc btn-cc-primary" href="campaigns.html">저장 후 닫기</a>
				<a class="btn-cc btn-cc-white" href="campaigns.html">저장 안 함</a>
				<button type="button" class="btn-cc btn-cc-black" popovertarget="ccCloseConfirm" popovertargetaction="hide">계속 작성</button>
			</div>
		</div>
	</div>'''


def copy_data():
    """복제용 — 캠페인 id → 조건(JS 가 칸을 채움)"""
    return {c["id"]: {"biz": c["bid"], "name": c["name"], "ty": TY_CODE[c["ty"]], "ch": c["ch"], "n": c["n"],
                      "reward": c["reward"], "round": c["round"], "bname": c["b"]["name"]} for c in D.CAMPS}


def page():
    radios = "".join(f'<input type="radio" name="ccStep" id="ccStep{i}" hidden{" checked" if i == 1 else ""}>' for i, _l in STEPS)
    chan = {v: k for k, v in CHANNEL}
    data = json.dumps({"bal": D.BALANCE, "fee": D.FEE, "chan": chan, "camps": copy_data()}, ensure_ascii=False)
    body = f'''<section class="ag-cnew" aria-label="캠페인 등록">
	<input type="radio" name="agRole" id="agRoleAdmin" hidden checked><input type="radio" name="agRole" id="agRoleStaff" hidden>
	<!-- [2026-11-12] 광고주처럼 캠페인 리스트 위에 뜨는 창 — 뒤 화면 = 실제 campaigns.html(누르지 못함), 덮개 = 광고주 .modal-wrap.open + .modal-dim -->
	<iframe class="ag-cnew-bg" src="campaigns.html" title="뒤 화면: 캠페인 리스트" tabindex="-1" aria-hidden="true" inert></iframe>
	{ag_bar()}
	<div class="modal-wrap campaign-create-modal open" id="campaignCreate">
	<form name="campaignForm" data-use-editor="N">
		{radios}
		<div class="modal-dim"></div>
		<div class="modal-content create-modal-content">
			{hidden_inputs()}
			<div class="create-modal-header">
				<h3 class="modal-title">캠페인 등록</h3>
				<button type="button" class="btn-close" popovertarget="ccCloseConfirm" aria-label="닫기">
					<span class="material-symbols-outlined">close</span>
				</button>
				{indicator()}
			</div>
			<div class="create-modal-body">
				{step1()}{step2()}{step3()}{step4()}
			</div>
			{footer()}
		</div>
	</form>
	{close_confirm()}
	</div>
	<script type="application/json" id="new-data">{data}</script>
</section>'''
    css = '<link rel="stylesheet" href="css/bridge/create.css"><link rel="stylesheet" href="css/ag/create.css">'
    return P.page("캠페인 등록", "camp", body, None, css, "campaign_new.js")
