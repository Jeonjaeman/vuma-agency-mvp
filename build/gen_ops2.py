# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 운영 — 광고주 화면 그대로 옮긴 4 화면 (조사/광고주_운영화면_스펙_20261110.md 6·7·8·9장)
[2026-11-11 v0.9] 본문 마크업을 광고주 원본 그대로로 다시 씀 — 같은 요소·클래스·순서·문구 (css/adv/* 가 그대로 입혀지게)
  photos.html        리뷰 사진 관리  ← U:\\admin\\inc\\photo.inc.html + photoView.inc.html + script/index.js renderPhotoGrid()
  search_report.html 검색결과 리포트 ← U:\\admin\\inc\\searchReport.inc.html + core/inc/searchRankTerms.inc.html
                                      + script/index.js openReportModal()
  video.html         영상 제작 요청  ← U:\\admin\\inc\\videoRequest.inc.html + script/videoRequest.js open()
  messages.html      쪽지            ← U:\\admin\\inc\\message\\receivedMessages · sentMessages · sendBox.inc.html
                                      (광고주는 4 화면, 여기선 한 파일 + 라디오 탭 — 탭 줄 .msg-box-tabs 는 그대로)
  광고주가 JS 로 여닫는 창(.modal-wrap · .modal-overlay)은 popover 로 연다(css/v9-media.css).
  대행사 차이 = 모든 업체를 한 화면에(카드·줄마다 data-biz → js/scope.js 가 한 업체 범위면 숨김),
  업체·담당자 줄(.col-biz) · 보고서 링크에 싣기 · 포인트 차감 · 쪽지의 업체·캠페인 표시 — 모두 .add / add_tag 로 표시.
  실행: python -I build/gen_ops2.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402

P, G = D.P, D.G
esc = K.esc
MAX_BYTES = 400_000
PHOTO_CAP = 12                       # 사진보기 창에 그리는 칸 수(시안 — 실제는 전부)
VIDEO_PRICE = 5000                   # videoRequest::priceTable — 세 종류 같은 단가(시안)
TONG_POINT = 1_284_500               # 포인트 잔액(시안 값)
# 캠페인 채널 → 광고주 사진 거르기 값(photo.inc.html ?ch= : blog / youtube / insta)
CH_KEY = {"블로그": "blog", "쇼츠": "youtube", "인스타": "insta", "릴스": "insta"}
NO_REASON = ["동의 범위 밖(블로그 게시만)", "리뷰어 얼굴 포함", "광고 사용 미동의", "화질 낮음"]
SU_SCOPE = ["자사몰 · SNS 광고 · 1년", "자사몰 · 6개월", "SNS 광고 · 2년"]
CSS = K.CSS + '<link rel="stylesheet" href="css/v9-media.css">'


# ── 공통 ──────────────────────────────────────────────
def msi(name, style=""):
    """Material Symbols 아이콘(광고주와 같은 글꼴)"""
    st = f' style="{style}"' if style else ""
    return f'<span class="material-symbols-outlined"{st}>{name}</span>'


def region(b):
    """[지역] = 업체 이름 첫 단어 (연남 헤어살롱 → 연남) — 광고주 zoneAreaName() 자리"""
    return b["name"].split()[0]


def code(c):
    return 10200 + D.CAMPS.index(c)        # 캠페인 코드 — gen_campaigns.code() 와 같은 값


def ymd(off, short=False):
    d = P.d_of(off)
    return f'{d.year % 100:02d}.{d.month:02d}.{d.day:02d}' if short else f'{d.year}.{d.month:02d}.{d.day:02d}'


def biz_text(b):
    return f'{K.biz_cell(b)} · {K.owner_of(b)}{K.add_tag()}'


def camp_link(c):
    return f'campaigns.html#c-{c["id"]}'


def ok_reviews(c):
    return [r for r in c["revs"] if r["st"] == "ok"]


def hide_btn(pid, cls, inner, label="닫기", style=""):
    """광고주 onclick="close…()" 자리 — popover 닫기 버튼"""
    st = f' style="{style}"' if style else ""
    return (f'<button type="button" class="{cls}"{st} popovertarget="{pid}" popovertargetaction="hide" aria-label="{label}">'
            f'{inner}</button>')


def modal_wrap(pid, cls, content_attr, header, body, footer):
    """광고주 .modal-wrap 창 — 바깥에 popover, .modal-dim 은 닫기 버튼으로"""
    return (f'<div id="{pid}" class="modal-wrap {cls}" popover>'
            + hide_btn(pid, "modal-dim", "")
            + f'<div class="modal-content"{content_attr}><div class="modal-header">{header}</div>'
            f'<div class="modal-body">{body}</div><div class="modal-footer"{footer[0]}>{footer[1]}</div></div></div>')


def write(fname, title, key, body):
    html = P.page(title, key, body, None, CSS, "ops.js")
    size = len(html.encode("utf-8"))
    if size > MAX_BYTES:
        raise SystemExit(f"{fname} 가 {size:,}B — {MAX_BYTES:,}B 넘음")
    (K.ROOT / fname).write_text(html, encoding="utf-8")
    print(f"written {fname} ({size:,} B)")


# ── 1. 리뷰 사진 관리 (photo.inc.html · photoView.inc.html) ──
def photo_set(c):
    """사진 N장 · 2차 활용 여부 · 사용 가능 여부 — 캠페인마다 고정 난수"""
    r = random.Random(f"photo-{c['id']}")
    n = sum(r.randint(3, 8) for _ in ok_reviews(c))
    hue = r.randint(0, 359)
    su_on = r.random() < .65
    items = []
    for i in range(n):
        ok = r.random() < .7 and i not in (2, 7)      # 창 첫 화면에 "사용 불가" 예시가 꼭 보이게
        items.append({"h": (hue + i * 23) % 360, "ok": ok, "why": "" if ok else r.choice(NO_REASON)})
    return items, su_on, (r.choice(SU_SCOPE) if su_on else "")


def photo_card(c, items, su_on, scope):
    pid = f"ph-{c['id']}"
    cnt = len(items)
    more = cnt - 4 if cnt > 4 else 0
    cells = ""
    for i in range(4):
        inner = ""
        if i < cnt:          # 사진 칸 — 외부 그림 대신 색 블록(.v9-ph)이 <img> 자리
            inner = f'<i class="v9-ph" style="--h:{items[i]["h"]}"></i>'
            if i == 3 and more > 0:
                inner += f'<div class="photo-more-overlay">+{more}</div>'
        cells += f'<div class="photo-cell">{inner}</div>'
    if su_on:
        su_cnt = sum(1 for p in items if p["ok"])
        su = (f'<div style="margin-bottom:12px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;">'
              f'<span class="photo-su-badge {"photo-su-badge--ok" if su_cnt else "photo-su-badge--no"}">광고 사용 가능 {su_cnt}장</span>'
              f'<span style="font-size:11px;color:#0e0e0e;">{scope}</span></div>')
    else:
        su = '<div style="margin-bottom:12px;"></div>'
    return (f'<div class="cmp-card cmp-photo-card" data-biz="{c["bid"]}" data-ch="{CH_KEY.get(c["ch"], "etc")}">'
            f'<div class="card-thumb"><div class="photo-grid-4">{cells}</div></div>'
            f'<div class="card-content"><div class="card-desc" style="margin-bottom:2px;">[{esc(region(c["b"]))}]</div>'
            f'<div class="card-title" style="margin-bottom:8px;">{esc(c["name"])} <span class="cell-sub" style="font-weight:400;">· 사진 {cnt}장</span></div>'
            f'{su}<div class="card-desc col-biz add v9-biz">{biz_text(c["b"])}</div></div>'
            f'<div class="card-actions"><a class="card-btn" href="{camp_link(c)}">{msi("article")} 캠페인보기</a>'
            f'<button type="button" class="card-btn" popovertarget="{pid}">{msi("photo_library")} 사진보기</button></div></div>')


def photo_cell(p, su_on, src_label):
    """script/index.js renderPhotoGrid() 가 만드는 칸 그대로"""
    tag = ""
    if su_on and p["ok"]:
        tag = '<span class="photo-su-tag photo-su-tag--ok">광고 사용 가능</span>'
    elif su_on:
        tag = f'<span class="photo-su-tag photo-su-tag--no" title="{p["why"]}">사용 불가</span>'
    if su_on and not p["ok"]:
        ov = f'<div class="photo-su-why">광고 사용 불가 — {p["why"]}</div>'
    else:
        dl = su_on and p["ok"]
        ov = (f'<a href="#" class="btn-photo-action">{msi("download" if dl else "zoom_in")} {"내려받기" if dl else "원본보기"}</a>'
              + ('<div class="photo-su-until">사용 기한 2027.11.10</div>' if dl else ""))
    ov += f'<a href="#" class="btn-photo-action">{msi("open_in_new")} {src_label}</a>'
    return (f'<div class="photo-modal-cell"><i class="v9-ph" style="--h:{p["h"]}"></i>{tag}'
            f'<div class="photo-hover-overlay">{ov}</div></div>')


SU_BAR = ('<div class="v9-subar" style="background:#f1f6ff;border:1px solid #d6e4ff;border-radius:8px;padding:11px 14px;margin:0 0 14px;">'
          '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
          '<span class="photo-su-badge photo-su-badge--ok">광고 사용 가능</span>'
          '<span style="font-size:12px;color:#1a3c7a;">리뷰어가 동의한 범위 — <b>{scope}</b></span>'
          '<label style="margin-left:auto;display:flex;align-items:center;gap:6px;font-size:12px;color:#1a3c7a;cursor:pointer;">'
          '<input type="checkbox" class="v9-suonly"> 사용 가능한 사진만 보기</label></div>'
          '<p style="margin:8px 0 0;font-size:11px;color:#5a6b8c;line-height:1.6;">'
          '· 위 범위와 기간 안에서만 사용할 수 있습니다. 재판매·제3자 제공·수정 후 별도 저작물 제작은 포함되지 않습니다.<br>'
          '· 리뷰어의 이름·아이디를 광고에 노출하려면 따로 동의를 받아야 합니다.<br>'
          '· <b>사용 불가</b> 로 표시된 사진은 내려받을 수 없습니다. 칸에 표시된 사유를 확인해 주세요.</p>'
          '<p style="margin:8px 0 0;padding:9px 12px;background:#fff6f6;border:1px solid #f3c7c7;border-radius:8px;font-size:11px;color:#c53030;line-height:1.7;">'
          '· <b>\'광고 사용 가능\' 은 리뷰어 본인의 진술에 따른 표시</b>입니다 — 뷰마이 사진 원본을 검증하지는 않습니다.<br>'
          '· 리뷰어가 권리 없는 사진을 올렸다면 <b>그 사진으로 얻는 권리도 없습니다.</b> '
          '모르고 사용했더라도 <b>게시 중단 요구·손해배상 책임이 광고주에게 미칠 수 있습니다.</b><br>'
          '· <b>광고에 쓰기 전에 직접 확인해 주세요</b> — 사람 얼굴, 다른 브랜드 로고·상품, 타인의 작품이 담긴 사진은 한 번 더 보셔야 합니다.</p></div>')


def photo_modal(c, items, su_on, scope):
    """photoView.inc.html — 광고주는 창 하나를 AJAX 로 채움, 여기선 캠페인마다 창 하나"""
    pid = f"ph-{c['id']}"
    src = {"youtube": "유튜브 보기", "insta": "인스타 보기"}.get(CH_KEY.get(c["ch"], ""), "블로그 원문 보기")
    cells = "".join(photo_cell(p, su_on, src) for p in items[:PHOTO_CAP])
    rest = len(items) - PHOTO_CAP
    header = (f'<h3 class="modal-title">등록된 리뷰 사진 리스트 <span class="cell-sub" style="font-weight:400;">({len(items)}장)</span></h3>'
              '<div style="display:flex;align-items:center;gap:8px;">'
              '<button type="button" class="btn btn--sm btn--outline js-flash" data-msg="시안: 리뷰 사진을 다시 가져왔습니다">'
              f'{msi("refresh", "font-size:16px;vertical-align:-3px;")} 다시 가져오기</button>'
              + hide_btn(pid, "btn-close", msi("close")) + '</div>')
    body = ((SU_BAR.format(scope=scope) if su_on else "")
            + f'<p class="add v9-pm-camp">[{esc(region(c["b"]))}] {esc(c["name"])} · {biz_text(c["b"])}</p>'
            + f'<div class="photo-modal-grid">{cells}</div>'
            + (f'<p class="v9-more">시안: 나머지 {rest}장은 생략했습니다.</p>' if rest > 0 else ""))
    return (f'<div id="{pid}" class="modal-wrap photo-modal" popover>' + hide_btn(pid, "modal-dim", "")
            + f'<div class="modal-content photo-modal-content"><div class="modal-header">{header}</div>'
            f'<div class="modal-body">{body}</div>'
            f'<div class="modal-footer">{hide_btn(pid, "btn btn-outline", "닫기")}</div></div></div>')


def build_photos():
    camps = [c for c in D.CAMPS if ok_reviews(c)]
    cards, pops = [], []
    for c in camps:
        items, su_on, scope = photo_set(c)
        cards.append(photo_card(c, items, su_on, scope))
        pops.append(photo_modal(c, items, su_on, scope))
    # 채널 거르기: 광고주는 <a href="?ch=…"> 새로 불러오기 → 여기선 라디오 + :has() (css/v9-media.css)
    radios = "".join(f'<input type="radio" name="rpch" id="rpch-{k}" class="v9-r"{" checked" if k == "all" else ""}>'
                     for k in ("all", "blog", "youtube", "insta"))
    btns = "".join(f'<label for="rpch-{k}" class="btn btn--sm btn--outline">{lab}</label>'
                   for k, lab in (("all", "전체"), ("blog", "블로그"), ("youtube", "유튜브"), ("insta", "인스타")))
    body = ('<div class="cmp-layout">' + K.camp_tabs("photo")
            + '<div class="cmp-page-card v9-photo">' + radios
            + '<div class="cmp-page-header cc-mb-16"><h2 class="cmp-page-title">리뷰 사진 리스트</h2></div>'
            + '<div class="cmp-filters-wrap cc-bb cc-mb-24" style="padding-bottom:14px;">'
            + f'<div style="display:flex;gap:8px;">{btns}</div></div>'
            + f'<div class="cmp-grid-view">{"".join(cards)}</div></div></div>' + "".join(pops))
    write("photos.html", "리뷰 사진 관리", "photo", body)


# ── 2. 검색결과 리포트 (searchReport.inc.html) ─────────
SR_TERMS = ('<div style="margin:16px 0 0;padding:12px 14px;background:#f7f8fb;border-radius:8px;font-size:13px;line-height:1.8;color:#555;">'
            '· <strong>최고 순위</strong> : 그날 캠페인 키워드로 네이버 블로그 검색을 했을 때, '
            '내 승인 리뷰 중 가장 위에 있던 자리입니다. 숫자가 작을수록 좋습니다.<br>'
            '· <strong>노출/대조</strong> : <em>대조</em>는 그날 확인한 승인 리뷰 수, '
            '<em>노출</em>은 그중 검색 결과에서 찾은 수입니다. 예) <b>3/5</b> — 리뷰 5개 중 3개가 걸렸습니다.<br>'
            '· <strong>검색결과</strong> : 그날 <b>검색 첫 페이지에서 확인한 블로그 글 수</b>입니다'
            '(보통 30개 안팎). 그 키워드의 전체 글 개수가 아닙니다.<br>'
            '<span style="display:block;margin-top:8px;padding-top:8px;border-top:1px solid #e5e7eb;">'
            '※ <b>\'미노출\'은 글이 사라졌다는 뜻이 아닙니다.</b> 순위는 <b>검색 첫 페이지까지만</b> 확인합니다. '
            '그 뒤에 있으면 미노출로 기록됩니다.<br>'
            '※ 네이버 검색 화면이 바뀌거나 조회가 막히면 그날 수치가 비거나 낮게 잡힐 수 있습니다. '
            '하루치보다 <b>며칠간의 흐름</b>으로 보시는 편이 정확합니다.</span></div>')


def rank_history(r):
    """수집 7회(최근 → 과거) — (수집일 오프셋, 최고 순위 or 0, 노출, 대조, 검색결과)"""
    out = []
    for k in range(7):
        rk = r.choice([0, r.randint(1, 30), r.randint(1, 12), r.randint(1, 5)])
        tot = r.randint(3, 10)
        out.append((-k - 1, rk, r.randint(1, tot) if rk else 0, tot, r.randint(26, 31)))
    return out


def srch_card(c):
    r = random.Random(f"srch-{c['id']}")
    kw = c["b"]["name"]
    hist = rank_history(r)
    off, best, found, checked, _res = hist[0]
    pid = f"sr-{c['id']}"
    tag = ('<span class="tag-sns bg-green">검색노출</span>' if best
           else '<span class="tag-sns" style="background:#e5e7eb;color:#6b7280;">미노출</span>')
    rep = (f'<label class="add v9-inrep"><input type="checkbox"{" checked" if r.random() < .4 else ""}>'
           f' 보고서 링크에 싣기{K.add_tag()}</label>')
    card = (f'<div class="cmp-card cmp-list-card" data-biz="{c["bid"]}"><div class="card-content">'
            f'<div class="card-tags">{tag}<span class="tag-code tag-code-report">검색순위 {f"{best}위" if best else "미노출"}</span></div>'
            f'<div class="card-title">[{esc(region(c["b"]))}] {esc(c["name"])}</div>'
            f'<div class="card-desc">키워드 \'{esc(kw)}\' · 리뷰 {found}/{checked} 노출 · 갱신 {ymd(off)}</div>'
            f'<div class="card-desc col-biz add v9-biz">{biz_text(c["b"])}</div>'
            f'<div class="card-stats" style="margin-top:auto;"><span>신청 <strong>{c["applied"]}</strong> / 모집 {c["n"]}</span>{rep}</div></div>'
            f'<div class="card-actions"><a class="card-btn" href="{camp_link(c)}">{msi("article")} 캠페인보기</a>'
            f'<button type="button" class="card-btn" popovertarget="{pid}">{msi("receipt_long")} 검색 리포트</button></div></div>')
    # openReportModal() 이 그리는 줄: td padding 8px 10px, 순위 칸은 굵게 · 보라/회색
    td = 'style="padding:8px 10px;"'
    trs = "".join(f'<tr><td {td}>{ymd(o)}</td>'
                  f'<td style="padding:8px 10px;font-weight:700;color:{"#7346f3" if x else "#8e8e93"};">{f"{x}위" if x else "미노출"}</td>'
                  f'<td {td}>{s} / {t}</td><td {td}>{n}건</td></tr>' for o, x, s, t, n in hist)
    th = 'style="padding:8px 10px;"'
    table = ('<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead>'
             '<tr style="text-align:left;color:#0e0e0e;border-bottom:1px solid #ececf0;">'
             f'<th {th}>수집일</th><th {th}>최고 순위</th><th {th}>노출/대조</th><th {th}>검색결과</th></tr></thead>'
             f'<tbody>{trs}</tbody></table>')
    header = (f'<h3 class="modal-title">검색순위 리포트 <span class="cell-sub" style="font-weight:400;font-size:13px;">키워드: {esc(kw)}</span></h3>'
              + hide_btn(pid, "btn-close", msi("close")))
    body = f'<p class="add v9-pm-camp">[{esc(region(c["b"]))}] {esc(c["name"])} · {biz_text(c["b"])}</p>' + table + SR_TERMS
    pp = modal_wrap(pid, "report-modal", ' style="width:560px;max-width:calc(100vw - 32px);"', header, body,
                    ("", hide_btn(pid, "btn btn-primary", "확인", "확인")))
    return card, pp


def build_search():
    camps = [c for c in D.CAMPS if c["ch"] == "블로그" and ok_reviews(c)]
    cards, pops = [], []
    for c in camps:
        card, pp = srch_card(c)
        cards.append(card)
        pops.append(pp)
    note = ('<p class="add v9-note">체크한 캠페인의 검색순위는 <a href="reports.html">보고서 링크</a>에도 실려 '
            f'업체 고객이 함께 봅니다{K.add_tag()}</p>')
    body = ('<div class="cmp-layout">' + K.camp_tabs("srch")
            + '<div class="cmp-page-card"><div class="cmp-page-header" style="margin-bottom:16px;">'
            + '<h2 class="cmp-page-title">검색결과 리포트</h2></div>' + note
            + f'<div class="cmp-list-view">{"".join(cards)}</div>' + SR_TERMS + '</div></div>' + "".join(pops))
    write("search_report.html", "검색결과 리포트", "srch", body)


# ── 3. 영상 제작 요청 (videoRequest.inc.html · videoRequest.js) ──
# videoRequest::$TYPE / $STATE (core/lib/classes/videoRequest.class.php)
VTYPE = [("clip", "클립"), ("reels", "릴스"), ("shorts", "쇼츠")]
VSTATE = {0: ("접수", "wait"), 1: ("제작중", "wait"), 2: ("제공완료", "done"), 3: ("게시완료", "done"), 9: ("취소", "reject")}
REFUND = ["환불 완료", "환불 승인 대기중"]
REJECT = "원본 영상 화질이 낮아 제작할 수 없습니다."


def camp_cell(c):
    return (f'<td><a class="ri-camp__name" href="{camp_link(c)}">{esc(c["name"])}</a>'
            f'<span class="ri-camp__code">{code(c)}</span></td>')


def biz_td(c):
    return f'<td class="col-biz add">{K.biz_cell(c["b"])}<br><span class="ri-muted">{K.owner_of(c["b"])}</span></td>'


def vr_modal(i, c, rv, left):
    """videoRequest.js open() 이 채우는 #vrModal — 줄마다 창 하나(제목·닉네임·남은 종류가 줄마다 다름)"""
    pid = f"vr-{i}"
    types = "".join(f'<label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px;">'
                    f'<input type="radio" name="vrType-{i}" value="{k}"{" checked" if j == 0 else ""}>'
                    f'<span>{lab} · {VIDEO_PRICE:,}P</span></label>' for j, (k, lab) in enumerate(left))
    header = f'<h3 class="modal-title">영상 제작 요청 — {esc(c["name"])}</h3>' + hide_btn(pid, "btn-close", msi("close"))
    body = (f'<p class="ri-modal-head"><strong>{esc(rv["nick"])}</strong> 님의 리뷰</p>'
            '<label class="ri-reason-label">영상 종류</label>'
            f'<div class="vr-type-box" style="display:flex;flex-direction:column;gap:8px;margin-bottom:14px;">{types}</div>'
            f'<label class="ri-reason-label" for="vrRequest-{i}">요청사항 <span class="ri-muted" style="font-weight:400;">(선택)</span></label>'
            f'<textarea id="vrRequest-{i}" class="ri-reason-input" placeholder="강조하고 싶은 장면, 자막 문구, 분위기 등을 적어주시면 제작에 반영합니다."></textarea>'
            f'<label class="ri-reason-label" style="margin-top:14px;" for="vrRefFile-{i}">참고자료 첨부 <span class="ri-muted" style="font-weight:400;">(선택)</span></label>'
            f'<input type="file" id="vrRefFile-{i}" class="vr-file" accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.m4v,.webm,.pdf,.zip,.ppt,.pptx,.doc,.docx,.hwp,.hwpx">'
            '<p class="ri-muted" style="font-size:12px;line-height:1.6;margin:6px 0 0;">'
            '로고 · 참고 영상 · 브랜드 가이드처럼 제작에 도움이 될 파일을 올려주세요.<br>'
            '이미지 · 영상 · pdf · zip · 기획안(ppt/doc/hwp) · 최대 50MB</p>'
            f'<p class="ri-modal-notice">※ <b>{VIDEO_PRICE:,}P</b> 가 바로 차감됩니다. 영상을 받기 전에는 언제든 취소하고 전액 돌려받을 수 있습니다.<br>'
            f'현재 보유 포인트 <b>{TONG_POINT:,}P</b></p>'
            f'<p class="add v9-note">포인트에서 차감 · {esc(c["b"]["name"])} 사용내역에 표시{K.add_tag()}</p>')
    foot = (hide_btn(pid, "btn", "닫기", style="border:1px solid #d1d1d6;background:#fff;")
            + '<button type="button" class="btn btn-primary js-flash" data-msg="시안: 영상 제작을 요청했습니다">요청하기</button>')
    return modal_wrap(pid, "", "", header, body, (' style="display:flex;gap:8px;justify-content:flex-end;"', foot))


def build_video():
    r = random.Random("video")
    revs = [(c, rv) for c in D.CAMPS for rv in ok_reviews(c) if c["ch"] != "구매평"]
    pick = r.sample(revs, min(18, len(revs)))
    rows, pops = [], []
    for i, (c, rv) in enumerate(pick):
        left = VTYPE if i % 4 else VTYPE[1:]          # 이미 요청한 종류는 빠짐(넷 중 하나는 클립을 이미 요청)
        rows.append(f'<tr data-biz="{c["bid"]}">{biz_td(c)}{camp_cell(c)}<td>{esc(rv["nick"])}</td>'
                    f'<td class="ri-muted">{esc(rv["ch"])}</td><td class="ri-muted">{ymd(-rv["ago"], True)}</td>'
                    '<td class="ri-col-center"><a href="#" class="ri-link">열기</a></td>'
                    f'<td class="ri-col-center"><button type="button" class="btn btn-primary" style="padding:6px 14px;font-size:13px;" '
                    f'popovertarget="vr-{i}">영상 요청</button></td></tr>')
        pops.append(vr_modal(i, c, rv, left))

    states = [0, 1, 1, 2, 3, 3, 9, 9, 0, 2]
    hist = []
    for i, st in enumerate(states):
        c, _rv = r.choice(revs)
        lab, cls = VSTATE[st]
        sub = ""
        if st == 9:
            if i % 2:
                sub += f'<div class="ri-reject-reason">사유 : {REJECT}</div>'
            sub += f'<div class="ri-muted" style="font-size:12px;margin-top:3px;">{REFUND[i % 2]}</div>'
        dash = '<span class="ri-muted">-</span>'
        video = ('<a href="#" class="ri-link">내려받기</a><div class="ri-muted" style="font-size:12px;">'
                 f'{r.randint(18, 64)}.{r.randint(0, 9)}MB</div>') if st in (2, 3) else dash
        sns = '<a href="#" class="ri-link">보기</a>' if st == 3 else dash
        cancel = ('<button type="button" class="btn js-flash" style="padding:6px 12px;font-size:13px;border:1px solid #d1d1d6;background:#fff;" '
                  f'data-msg="시안: 요청을 취소했습니다 — {VIDEO_PRICE:,}P 환불은 정산 담당자 승인 후 처리됩니다">취소</button>'
                  if st in (0, 1) else dash)
        hist.append(f'<tr data-biz="{c["bid"]}">{biz_td(c)}{camp_cell(c)}<td>{VTYPE[i % 3][1]}</td>'
                    f'<td class="ri-muted">{VIDEO_PRICE:,}P</td>'
                    f'<td class="ri-col-center"><span class="ri-badge ri-badge--{cls}">{lab}</span>{sub}</td>'
                    f'<td class="ri-muted">{ymd(-i * 2 - 1, True)}</td><td class="ri-col-center">{video}</td>'
                    f'<td class="ri-col-center">{sns}</td><td class="ri-col-center">{cancel}</td></tr>')
    biz_th = f'<th class="col-biz add">업체·담당자{K.add_tag()}</th>'
    can = ('<div class="ri-table-wrap" style="margin-bottom:28px;"><table class="ri-table"><thead><tr>' + biz_th
           + '<th>캠페인</th><th>리뷰어</th><th>채널</th><th>승인일</th><th class="ri-col-center">리뷰</th>'
           '<th class="ri-col-center">영상 요청</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>')
    mine = ('<div class="ri-table-wrap"><table class="ri-table"><thead><tr>' + biz_th
            + '<th>캠페인</th><th>종류</th><th>금액</th><th class="ri-col-center">상태</th><th>요청일</th>'
            '<th class="ri-col-center">영상</th><th class="ri-col-center">게시</th><th class="ri-col-center">취소</th>'
            '</tr></thead><tbody>' + "".join(hist) + '</tbody></table></div>')
    price = ('<div class="ri-filter" style="flex-wrap:wrap;gap:14px;">'
             + "".join(f'<span class="ri-filter__hint" style="font-size:14px;"><b>{lab}</b> {VIDEO_PRICE:,}P</span>' for _k, lab in VTYPE)
             + f'<span class="ri-filter__hint" style="margin-left:auto;">보유 포인트 <b>{TONG_POINT:,}P</b></span></div>'
             '<p class="ri-modal-notice" style="margin:0 0 14px;">'
             '※ 요청하시면 포인트가 <b>바로 차감</b>됩니다. 운영자가 반려하거나 영상을 받기 전에 취소하시면 전액 환불됩니다.</p>'
             f'<p class="add v9-note">포인트에서 차감 · 업체별 사용내역에 표시{K.add_tag()}</p>')
    # 제목 "{회사}님의 영상 제작 요청" — 업체 범위를 고르면 js/scope.js 가 .js-scope-name 을 업체 이름으로 바꿈
    body = ('<div class="cmp-layout">' + K.camp_tabs("video")
            + '<div class="cmp-page-card"><div class="cmp-page-header">'
            + '<h2 class="cmp-page-title"><span class="js-scope-name">전체 업체</span>님의 영상 제작 요청</h2></div>'
            + price
            + '<h3 class="cmp-page-title" style="font-size:16px;margin:0 0 10px;">요청 가능한 리뷰</h3>' + can
            + '<h3 class="cmp-page-title" style="font-size:16px;margin:0 0 10px;">요청 내역</h3>' + mine
            + '</div></div>' + "".join(pops))
    write("video.html", "영상 제작 요청", "video", body)


# ── 4. 쪽지 (message/receivedMessages · sentMessages · sendBox.inc.html) ──
IN_MSG = [("방문 일정 변경 문의", "안녕하세요, 토요일 방문이 어려워서 일요일로 바꿔도 될까요?"),
          ("리뷰 수정했습니다", "말씀하신 대로 사진을 추가하고 키워드를 넣어 수정했습니다. 확인 부탁드려요."),
          ("배송 언제 오나요?", "선정 안내 받았는데 아직 제품이 안 왔습니다. 송장번호 알 수 있을까요?"),
          ("영수증 첨부합니다", "방문 영수증 사진 첨부합니다."),
          ("주차 가능한가요", "차로 방문하려는데 주차 공간이 있는지 궁금합니다."),
          ("포인트 지급 문의", "리뷰 승인 후 포인트가 아직 안 들어왔어요."),
          ("동반인 인원", "2인 제공이라고 되어 있는데 아이 1명 추가 가능할까요?")]
OUT_MSG = [("방문 전 예약 부탁드립니다", "방문 하루 전까지 매장으로 예약 전화 부탁드립니다."),
           ("리뷰 보완 요청", "대표 사진 1장과 지도 첨부를 추가해 주세요."),
           ("선정 안내", "체험단에 선정되셨습니다. 안내문을 꼭 확인해 주세요."),
           ("송장번호 안내", "오늘 발송했습니다. 송장번호 확인 부탁드립니다.")]
TABS = [("받은쪽지함", "rcv"), ("보낸쪽지함", "snt"), ("문자발송함", "sms"), ("메일발송함", "mail")]


def msg_pool(seed, n):
    """쪽지 n건 — 리뷰어가 있는 캠페인에서 업체·캠페인을 고른다"""
    r = random.Random(seed)
    camps = [c for c in D.CAMPS if c["rows"]]
    out = []
    for i in range(n):
        c = r.choice(camps)
        out.append({"c": c, "nick": r.choice(c["rows"])["nick"], "off": -(i // 3),
                    "hm": f"{r.randint(9, 21):02d}:{r.choice([0, 12, 25, 38, 47, 55]):02d}",
                    "file": r.random() < .25, "read": i >= 4 and r.random() < .8})
    return out


def msg_tag(c):
    """대행사 추가 — 이 쪽지가 어느 업체·캠페인 것이고 누구에게 배정됐는지"""
    return (f'<div class="msg-snippet add v9-tag">{esc(c["b"]["name"])} · {esc(c["name"])} · 배정: {K.owner_of(c["b"])}'
            f'{K.add_tag()}</div>')


def box_tabs(active, unread):
    """.msg-box-tabs — 광고주는 <a href="?pageName=…">, 여기선 같은 클래스의 <label for=라디오>"""
    out = ""
    for i, (lab, _k) in enumerate(TABS):
        cnt = f' <span class="msg-box-tab__count">{unread}</span>' if i == 0 and unread else ""
        out += f'<label for="mb-{i}" class="msg-box-tab{" msg-box-tab--active" if i == active else ""}">{lab}{cnt}</label>'
    return f'<div class="msg-box-tabs">{out}</div>'


def msg_search(kind):
    """form.msg-search — 광고주는 GET 검색, 여기선 검색 버튼이 안내만"""
    dates = ('<div class="msg-search__group msg-search__group--period"><span class="msg-search__label">기간</span>'
             '<input type="date" aria-label="시작일" class="rev-msg-input msg-search__date">'
             '<span class="msg-search__label msg-search__sep">~</span>'
             '<input type="date" aria-label="끝일" class="rev-msg-input msg-search__date"></div>')
    if kind == "rcv":
        q = ('<select class="rev-msg-input" aria-label="읽음"><option>읽음 전체</option><option>안 읽음</option><option>읽음</option></select>'
             '<input type="text" placeholder="보낸사람 이름" class="rev-msg-input msg-search__name">'
             '<input type="text" placeholder="보낸사람 아이디 (정확히)" class="rev-msg-input msg-search__sid">'
             '<input type="text" placeholder="제목·내용" class="rev-msg-input msg-search__q">')
    elif kind == "snt":
        q = ('<input type="text" placeholder="받는사람 이름" class="rev-msg-input msg-search__name">'
             '<input type="text" placeholder="받는사람 아이디 (정확히)" class="rev-msg-input msg-search__sid">'
             '<input type="text" placeholder="제목·내용" class="rev-msg-input msg-search__q">')
    else:
        mail = kind == "mail"
        q = ('<input type="text" placeholder="리뷰어명" class="rev-msg-input msg-search__name">'
             f'<input type="text" placeholder="{"제목·내용" if mail else "내용"}" class="rev-msg-input msg-search__sid">'
             '<input type="text" placeholder="아이디" class="rev-msg-input msg-search__name">'
             f'<input type="text" placeholder="{"이메일" if mail else "핸드폰"}" class="rev-msg-input msg-search__sid">')
    q = f'<div class="msg-search__group msg-search__group--query"><span class="msg-search__label">검색</span>{q}</div>'
    if kind in ("sms", "mail"):
        cost = ('' if kind == "mail" else
                '<span class="msg-search__label" style="margin-left:8px;">비용</span>'
                '<select class="rev-msg-input" aria-label="비용"><option>전체</option><option>내 부담 (3)</option><option>뷰마 부담 (2)</option></select>')
        q += ('<div class="msg-search__group msg-search__group--filter"><span class="msg-search__label">구분</span>'
              '<select class="rev-msg-input" aria-label="구분"><option>전체</option><option>내가 보낸 것</option><option>자동 발송</option></select>'
              f'{cost}</div>')
    act = ('<div class="msg-search__actions"><button type="button" class="msg-search__submit js-flash" data-msg="시안: 검색">검색</button>'
           '<a href="messages.html" class="msg-search__reset">초기화</a></div>')
    return f'<form class="msg-search" action="messages.html">{dates}{q}{act}</form>'


def pager(total):
    """core/inc/pagination.inc.php — 한 쪽이면 '총 n건' 만"""
    return f'<div class="cmp-pagination"><span class="cmp-pagination__info">총 {total}건</span></div>'


def clip(m):
    if not m["file"]:
        return ""
    return f'<span class="msg-clip" title="첨부파일 1개">{msi("attach_file")}1</span>'


def msg_item(m, i, t, s, sent, pre):
    """.msg-item 한 줄 — 광고주는 줄 클릭(JS)으로 상세 창, 여기선 제목 버튼이 줄 전체를 덮어 popover 를 엶"""
    pid = f"{pre}-{i}"
    c = m["c"]
    date = ymd(m["off"])
    rtime = f'{P.d_of(m["off"]).month:02d}.{P.d_of(m["off"]).day:02d} {m["hm"]}'
    if sent:
        state = (f'<span class="msg-read-state read">읽음 {rtime}</span>' if m["read"]
                 else '<span class="msg-read-state unread">안읽음</span>')
        state += f'<span class="msg-date-text">{date}</span>'
        if not m["read"]:
            state += '<button type="button" class="msg-recall-btn js-flash" data-msg="시안: 발송을 취소했습니다">발송취소</button>'
        unread = ""
    else:
        state = ((f'<span class="msg-read-state read">읽음 {rtime}</span>' if m["read"]
                  else '<span class="msg-read-state unread">안읽음</span>') + f'<span class="msg-date-text">{date}</span>')
        unread = "" if m["read"] else " unread"
    return (f'<div class="msg-item{unread}" data-biz="{c["bid"]}">'
            '<div class="msg-checkbox"><label class="custom-checkbox"><input type="checkbox" aria-label="고르기">'
            '<span class="checkmark"></span></label></div>'
            f'<div class="msg-sender"><div class="msg-avatar"></div><span class="sender-name">{esc(m["nick"])}</span></div>'
            f'<div class="msg-content-wrap"><div class="msg-title"><button type="button" class="v9-open" popovertarget="{pid}">'
            f'{esc(t)}</button>{clip(m)}</div><div class="msg-snippet">{esc(s)}</div>{msg_tag(c)}</div>'
            f'<div class="msg-date">{state}</div></div>')


def msg_modal(m, i, t, s, sent, pre):
    """tpl-message-detail / tpl-sent-detail — Modal.openTemplate() 이 .modal-overlay > .modal-box > .modal-box-inner 에 넣는 것"""
    pid = f"{pre}-{i}"
    c = m["c"]
    who = f'받는사람 : {esc(m["nick"])}' if sent else esc(m["nick"])
    readst = ""
    if sent:
        readst = (f'<span class="detail-msg-readstate msg-read-state {"read" if m["read"] else "unread"}">'
                  f'{"읽음" if m["read"] else "안읽음"}</span>')
    files = ""
    if m["file"]:
        files = (f'<div class="msg-detail-files detail-msg-files" style="margin-top:14px;">'
                 f'<a href="#">{msi("attach_file")} 영수증_{i + 1}.jpg (1.2MB)</a></div>')
    if sent:
        act = ('<button type="button" class="btn-p-save btn-recall-message js-flash" style="min-width:100px;" '
               'data-msg="시안: 발송을 취소했습니다">발송취소</button>') if not m["read"] else ""
        title = "보낸 쪽지"
    else:
        act = ('<button type="button" class="btn-p-save btn-reply-message js-flash" style="min-width:100px;" '
               'data-msg="시안: 답장 창(쪽지 보내기)">답장하기</button>')
        title = "쪽지 상세보기"
    wrap = (f'<div class="msg-detail-wrap"><div class="msg-detail-header"><h2 class="msg-detail-title">{title}</h2>'
            + hide_btn(pid, "btn-close", msi("close")) + '</div>'
            '<div class="msg-detail-body"><div class="msg-info-section"><div class="msg-sender-box">'
            '<div class="msg-avatar"></div><div style="display:flex; flex-direction:column;">'
            f'<span class="sender-name">{who}</span><span class="msg-date">{ymd(m["off"])}</span></div></div>{readst}</div>'
            f'<div class="msg-detail-content"><h3 class="msg-detail-subject">{esc(t)}</h3>'
            f'<div class="msg-detail-campaign" style="display:block;">연관 캠페인 : {esc(c["name"])}</div>'
            f'<p class="add v9-note">{esc(c["b"]["name"])} · 배정: {K.owner_of(c["b"])}{K.add_tag()}</p>'
            f'<div class="msg-detail-text">{esc(s)}</div>{files}</div></div>'
            f'<div class="msg-detail-footer">{hide_btn(pid, "p-btn-sub", "닫기", style="min-width:100px;")}{act}</div></div>')
    # 바깥 어두운 곳 누르면 닫힘(광고주 Modal.init 의 overlay click) = 뒤에 깐 닫기 버튼
    return (f'<div id="{pid}" class="modal-overlay" popover role="dialog" aria-modal="true">'
            + hide_btn(pid, "v9-ovl-dim", "") + f'<div class="modal-box"><div class="modal-box-inner">{wrap}</div></div></div>')


def note_pane(idx, kind, title_h, actions, msgs, texts, sent, unread):
    items, pops = [], []
    for i, m in enumerate(msgs):
        t, s = texts[i % len(texts)]
        items.append(msg_item(m, i, t, s, sent, kind))
        pops.append(msg_modal(m, i, t, s, sent, kind))
    del_btn = ('<div class="msg-footer-actions"><button type="button" class="p-btn-sub js-flash" '
               'style="width:auto; padding:0 16px; height:36px; font-size:13px;" data-msg="시안: 삭제했습니다">선택 삭제</button></div>')
    pane = (f'<div class="received-messages-container cmp-page-card v9-mp mp-{idx}">'
            f'<div class="cmp-page-header"><h2 class="cmp-page-title">{title_h}</h2>{actions}</div>'
            + box_tabs(idx, unread) + msg_search(kind)
            + f'<div class="msg-list-container">{"".join(items)}</div>' + del_btn + pager(len(msgs)) + '</div>')
    return pane, pops


SEND_TEXT = {"sms": [("[뷰마] 방문 예약 잊지 마세요", "방문 하루 전까지 매장으로 예약 전화 부탁드립니다."),
                     ("[뷰마] 리뷰 마감 D-2 안내", "리뷰 마감이 이틀 남았습니다. 기한 안에 등록해 주세요."),
                     ("[뷰마] 선정 축하드립니다", "체험단에 선정되셨습니다. 안내문을 꼭 확인해 주세요.")],
             "mail": [("체험단 선정 안내 메일", "선정을 축하드립니다. 방문 일정과 유의사항을 안내드립니다."),
                      ("리뷰 작성 가이드", "키워드·사진 수·지도 첨부 등 리뷰 작성 가이드를 보내드립니다."),
                      ("배송 출발 안내", "제품이 오늘 발송되었습니다. 송장번호를 확인해 주세요.")]}


def send_item(c, nick, i, kind, r):
    """sendBox.inc.html 한 줄 — 체크칸 없는 .msg-item(cursor:default)"""
    mail = kind == "mail"
    t, s = SEND_TEXT[kind][i % 3]
    auto = i % 3 == 2                                          # 자동 발송(규칙이 보낸 것) 예시
    who = ("자동 발송", "#7a5af8") if auto else ("직접 발송", "#3468c0")
    badges = f'<span style="font-size:11.5px;padding:2px 7px;border-radius:10px;background:#f2f2f7;color:{who[1]};">{who[0]}</span>'
    fail = (not mail) and i == 3
    if not mail:
        cost = ("뷰마 부담", "#1f8a5f") if auto else ("내 부담", "#c0392b")
        badges += f'<span style="font-size:11.5px;padding:2px 7px;border-radius:10px;background:#f2f2f7;color:{cost[1]};">{cost[0]}</span>'
    if not auto:
        badges += ('<button type="button" class="btn-rev-act js-flash" style="height:28px;padding:0 10px;font-size:12px;width:auto;border-radius:6px;" '
                   'data-msg="시안: 다시 보냈습니다">다시 보내기</button>')
    if not mail and not fail and not auto:
        badges += '<span style="font-size:12px;color:#8e8e93;">20P 차감</span>'
    if fail:
        badges += '<span style="font-size:12px;color:#c0392b;">수신거부</span>'
    files = ""
    if mail and i == 1:
        files = ('<div style="margin-top:6px;display:flex;flex-direction:column;gap:4px;">'
                 '<a href="#" style="display:inline-flex;align-items:center;gap:6px;color:#3468c0;text-decoration:none;font-size:12px;">'
                 f'{msi("attach_file", "font-size:15px;")} 리뷰가이드.pdf (840KB)</a></div>')
    if mail:
        st = ("읽음", "read") if i % 2 else ("확인 안 됨", "")
    else:
        st = ("발송실패", "unread") if fail else (("수신확인", "read") if i % 2 == 0 else ("발송", ""))
    return (f'<div class="msg-item" style="cursor:default;" data-biz="{c["bid"]}">'
            f'<div class="msg-sender" style="min-width:120px;"><span class="sender-name">{esc(nick)}</span></div>'
            f'<div class="msg-content-wrap"><div class="msg-title">{esc(t)}</div><div class="msg-snippet">{esc(s)}</div>{files}'
            f'<div style="margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">{badges}</div>{msg_tag(c)}</div>'
            f'<div class="msg-date"><span class="msg-read-state {st[1]}">{st[0]}</span>'
            f'<span class="msg-date-text">{ymd(-i)} {r.randint(9, 20):02d}:{r.choice([0, 10, 30, 45]):02d}</span></div></div>')


def send_pane(idx, kind, unread):
    r = random.Random(kind)
    camps = [c for c in D.CAMPS if c["rows"]]
    items = []
    for i in range(5):
        c = r.choice(camps)
        items.append(send_item(c, r.choice(c["rows"])["nick"], i, kind, r))
    mail = kind == "mail"
    help_p = ('<p style="margin:-6px 0 14px;font-size:12px;color:#8e8e93;line-height:1.7;">'
              '※ 직접 보내신 것과 <strong>내 캠페인에서 자동으로 나간 것</strong>을 함께 보여 드립니다. '
              + ('메일 발송은 <strong>무료</strong>입니다.' if mail else
                 '줄마다 <strong>구분</strong>과 <strong>비용 부담</strong>이 함께 적힙니다.')
              + '<br>※ 모든 항목은 <strong>일부만 입력해도</strong> 찾을 수 있습니다. '
              '핸드폰은 하이픈을 넣으셔도 되고, 뒷자리만 입력하셔도 됩니다.<br>'
              '※ 이력이 많을 때는 <strong>기간을 함께</strong> 지정하시면 훨씬 빠릅니다.</p>')
    if not mail:
        help_p += f'<p class="add v9-note">\'내 부담\' 문자값은 포인트에서 차감 · 업체별 사용내역에 표시{K.add_tag()}</p>'
    return (f'<div class="received-messages-container cmp-page-card v9-mp mp-{idx}">'
            f'<div class="cmp-page-header"><h2 class="cmp-page-title">{"메일 발송함" if mail else "문자 발송함"}</h2></div>'
            + box_tabs(idx, unread) + msg_search(kind) + help_p
            + f'<div class="msg-list-container">{"".join(items)}</div>' + pager(len(items)) + '</div>')


def build_messages():
    inbox = msg_pool("msg-in", 10)
    outbox = msg_pool("msg-out", 8)
    unread = sum(1 for m in inbox if not m["read"])
    rcv_title = f'받은 쪽지함 <span style="color:#dc2f02;font-size:15px;">({unread})</span>' if unread else "받은 쪽지함"
    rcv_act = ('<div class="cmp-header-actions"><button type="button" class="btn-notif-all-read js-flash" '
               'data-msg="시안: 모두 읽음으로 바꿨습니다">전체읽음 처리</button></div>')
    p0, pop0 = note_pane(0, "rcv", rcv_title, rcv_act, inbox, IN_MSG, False, unread)
    p1, pop1 = note_pane(1, "snt", "쪽지함", "", outbox, OUT_MSG, True, unread)
    p2 = send_pane(2, "sms", unread)
    p3 = send_pane(3, "mail", unread)
    # 탭 = 라디오 넷(css/v9-media.css 가 고른 쪽 카드만 보임) — 각 카드 안 탭 줄은 광고주처럼 자기 탭이 --active
    radios = "".join(f'<input type="radio" name="mb" id="mb-{i}" class="v9-r"{" checked" if i == 0 else ""}>' for i in range(4))
    note = ('<p class="add v9-note v9-msgnote">광고주 사이트에 채팅은 없습니다(10-28 제거) — 리뷰어와는 쪽지로. '
            f'받은 쪽지는 업체 담당자에게 배정됩니다{K.add_tag()}</p>')
    body = (f'<div class="cmp-layout v9-msg">{radios}{note}{p0}{p1}{p2}{p3}</div>' + "".join(pop0 + pop1))
    write("messages.html", "쪽지", "chat", body)


def build():
    build_photos()
    build_search()
    build_video()
    build_messages()


if __name__ == "__main__":
    build()
