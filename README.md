# 대행사 사이트 MVP (로컬 시안)

기준: `..\기획\대행사사이트_기획서_v0.9.md` (현재 시안 **v0.9**) · 구조 원칙: `..\기획\구조재설계_v0.8안.md` · 광고주 화면 원본 정리: `..\조사\광고주_운영화면_스펙_20261110.md` · `..\조사\광고주_계정화면_스펙_20261110.md` · 레퍼런스: `..\UI레퍼런스\선정레퍼런스\README.md`

**원칙(v0.8)**: 광고주 사이트의 모든 기능 = 그대로 + 대행사 전용 대시보드·정보관리. 화면의 점선(`.add`) = 광고주 화면에 없는 대행사 추가분.
**모양(v0.9)**: 광고주 기능 화면 = 광고주 화면 그대로(광고주 CSS · 마크업), 대행사 전용 화면만 대행사 CSS. 셸 = `gen_dashboard.HEAD_ADV` · `sidebar()` · `shell()`, 화면 틀 = `gen_pages.frame()`(광고주 기능 = `.adv-page`, 대행사 = `.work.ag`).
모든 `*.html` 은 생성 파일 — **직접 고치지 말고 `build/` 생성기를 고친다.**

| 메뉴 묶음 | 화면 | 생성기 · 스타일 · 동작 |
|---|---|---|
| 대행사 | `dashboard.html` 대시보드 | `gen_dashboard.py`(+ `alerts.py`) · `agency.css` · `dashboard.js` |
| | `schedule.html` 일정 · `biz.html` 업체 | `gen_pages.py` · `pages.css` · `pages.js` |
| | `team.html` 팀·담당자 | `gen_agency.py` |
| | `reports.html` 보고서 링크 · `report.html` 공개 보고서 | `gen_reports.py` · `settle.css` · `report.css` · `settle.js` |
| 캠페인 운영 | `campaigns.html` 캠페인 리스트·상세 · `campaign_new.html` 등록 | `gen_campaigns.py`(+ `camp_data.py` · `camp_new.py`) · `campaigns.css` · `campaigns.js` · `campaign_new.js` |
| | `reviewers.html` 리뷰어 관리 · `inspect.html` 리뷰 검수 · `payout.html` 포인트 지급 확인 | `gen_ops.py` |
| | `photos.html` · `search_report.html` · `video.html` · `messages.html` · `sms_box.html` | `gen_ops2.py` · `media.css` |
| 계정 | `point.html` 통포인트 · `plan.html` 사용료 · `sms.html` 문자설정 · `penalty.html` · `info.html` 마이페이지 · `notifications` · `notice` · `inquiry` · `faq.html` · `help.html`(따로 된 도움말) | `gen_account.py` · `account.css` |
| 공통 | 셸(메뉴 `NAV` · 업체 범위) | `gen_dashboard.py` `sidebar()`/`topbar()` · `gen_pages.page()` · `js/scope.js` |
| | 운영·계정 화면 조각(탭 · 표 · 창 · 캠페인 상단 탭) | `ops_kit.py` · `ops.css` · `ops.js` |

`gen_settle.py` 는 v0.7 정산 함수 모음(통포인트·지급 묶음이 가져다 씀) — `settle.html` 은 더 만들지 않음.
새 화면을 메뉴에 켜기: `gen_dashboard.py` 의 `READY` 에 키 추가.

다시 만들기(순서 상관없음):
`python -I build/gen_dashboard.py` · `gen_pages.py` · `gen_campaigns.py` · `gen_reports.py` · `gen_agency.py` · `gen_ops.py` · `gen_ops2.py` · `gen_account.py` · `gen_home.py`(홈 `home.html` — 메뉴에서 뺌 · 대행사 신청 `agency_apply.html`)

> 주의: PowerShell 5.1 의 `Get-Content`/`Set-Content` 로 생성기를 고치면 한글이 깨진다(BOM 없는 UTF-8). 편집기나 Python(`encoding="utf-8"`)으로만.

## CSS 나눔 (광고주 ↔ 대행사 — 서로 안 겹치게)
| 폴더 | 내용 | 규칙 |
|---|---|---|
| `css/adv/` | 광고주 원본 17개(U:\admin\css · U:\core\css 를 읽기만 해서 복사) | **고치지 않는다** |
| `css/bridge/` | 광고주 화면을 시안에서 돌리는 이음(광고주 JS 대신 라디오·`:has()`·popover) · 광고주 셸에 대행사 것 붙이기(`shell.css`) | 광고주 모양 값을 덮지 않음 · 태그 전체 규칙 금지 |
| `css/ag/` | 대행사 전용(대시보드 · 일정 · 업체 · 팀 · 보고서 · 대행사 추가분 `.add`) | class 이름이 광고주에 없을 것(겹치던 것은 `ag-` — `ag-btn` · `ag-on` …) · 광고주 class 선택 금지 · 태그 규칙은 `:where(.ag)` 안에서만 · 변수는 `--ag-` |

- 검사: `python -I build/check_css.py` — 하나라도 겹치면 이유를 찍고 실패. 광고주 CSS 를 새로 복사했을 때도 돌린다
- 대행사 추가분 표시 = `.add`(보라 점선) · 대행사 영역 = `.ag`(대행사 화면 틀 · 사이드바 업체 범위)

## 버전 관리
- 버전 하나 = git 태그(`v0.9`) = 지난 버전 보관 폴더(`versions/v0.6/` …) = 기획서 파일(`..\기획\대행사사이트_기획서_v0.9.md`)
- 새 버전을 시작할 때: ①지금 배포본에 태그가 있는지 확인 ②`git archive <이전태그> *.html css js | tar -x -C versions/<이전태그>` 로 보관 ③`build/gen_dashboard.py` 의 `VERSION` 올림 ④`CHANGELOG.md`·`versions/index.html` 에 한 칸 추가 ⑤커밋 후 새 태그
- v0.7 은 태그 없이 v0.8 에 합쳐짐(보관 폴더 없음 · `시안_v0.7_*.png` 만)
- 보관 폴더는 고치지 않는다(그때 모습 그대로 비교용)

## 시안에서 해 볼 수 있는 것
- **업체 범위**: 맨 위 "전체 업체 ▾" → 한 업체 → 운영 화면이 그 업체 것만, 업체·담당자 칸 숨김, 다른 화면으로 가도 유지(주소 `?biz=b3`)
- 대시보드: 칸 클릭 → 처리 패널 / [상세 관리 →] → 운영 층 그 화면(신청 → 캠페인 신청자, 검수 → 리뷰 검수, 지급 → 포인트 지급 확인)
- 캠페인 리스트: 상태 탭 12개 · 채널/유형 · 정렬 · 썸네일형/목록형(모두 CSS) · 카드 → 상세(주소 `#c-...`), 신청자 [선정] → 선정대기 수
- 리뷰어 관리 5탭 · 리뷰 검수 상태/캠페인 select 거르기(CSS) · 포인트 지급 확인 [지급대기만 보기] · 지급 묶음 [묶음 확정]
- 계정 화면 탭 전부 · 충전 금액 버튼 · 증빙 신청 칸 바뀜 · 창(popover)들
- 팀·담당자: 탭 3개 · 직원 초대/역할/업체 배정/중지·인수인계 창

## 아직 안 된 것(시안 한계)
- 저장 없음(버튼은 안내 한 줄), 새로고침하면 처음 상태
- 담당자로 로그인했을 때 업체 범위를 "내 업체"로 묶는 것은 표시만(권한 표 · 8-3)
- 대시보드 이슈 수와 운영 화면 줄 수가 일부 다름(더미 데이터 모델 차이 — CHANGELOG v0.8)
- 모바일(≤900) 카드형 셸은 아직 없음
