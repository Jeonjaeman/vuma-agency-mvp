# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 캠페인 운영 — 광고주 화면 그대로 옮긴 4 화면 (조사/광고주_운영화면_스펙_20261110.md 6·7·8·9장)
  photos.html        리뷰 사진 관리[photoManage]   (메뉴 키 photo)
  search_report.html 검색결과 리포트[searchReport] (메뉴 키 srch)
  video.html         영상 제작 요청[videoRequest]  (메뉴 키 video)
  messages.html      쪽지                            (메뉴 키 chat)
  대행사 차이 = 모든 업체를 한 화면에(줄마다 data-biz → js/scope.js 가 한 업체 범위면 숨김),
  업체·담당자 칸(.col-biz) · 업체 select · 보고서 싣기 · 통포인트 차감 · 쪽지 배정 — 모두 .add / add_tag 로 표시.
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
MAX_BYTES = 300_000
PHOTO_CAP = 12                       # 사진보기 창에 그리는 칸 수(시안 — 실제는 전부)
VIDEO_PRICE = 5000
TONG_POINT = 1_284_500               # 통포인트 잔액(시안 값)
# 캠페인 채널 → 사진 거르기 채널(구매평은 "전체"에서만 보임)
CH_KEY = {"블로그": "blog", "쇼츠": "yt", "인스타": "ig", "릴스": "ig"}
CH_LABEL = {"blog": "블로그", "yt": "유튜브", "ig": "인스타", "etc": "구매평"}
NO_REASON = ["동의 범위 밖(블로그 게시만)", "리뷰어 얼굴 포함", "광고 사용 미동의", "화질 낮음"]


# ── 공통 ──────────────────────────────────────────────
def region(b):
    """[지역] = 업체 이름 첫 단어 (연남 헤어살롱 → 연남)"""
    return b["name"].split()[0]


def title_of(c):
    return f'[{esc(region(c["b"]))}] {esc(c["name"])}'


def biz_line(b):
    """카드용 업체·담당자 줄(한 업체 범위면 .col-biz 가 숨김)"""
    return f'<p class="col-biz">{K.biz_cell(b)} · {K.owner_of(b)}{K.add_tag()}</p>'


def biz_td(b):
    return f'{K.biz_cell(b)}<br><small>{K.owner_of(b)}</small>'


BIZ_HEAD = ("업체·담당자" + K.add_tag(), "col-biz")


def biz_select():
    return f'<span class="add">{K.select("업체", ["업체 전체"] + [b["name"] for b in P.BIZS])}</span>'


def camp_link(c):
    return f'campaigns.html#c-{c["id"]}'


def ok_reviews(c):
    return [r for r in c["revs"] if r["st"] == "ok"]


def write(fname, title, key, body):
    html = P.page(title, key, f'<section class="ops">{body}</section>', None,
                  K.CSS + '<link rel="stylesheet" href="css/media.css">', "ops.js")
    size = len(html.encode("utf-8"))
    if size > MAX_BYTES:
        raise SystemExit(f"{fname} 가 {size:,}B — {MAX_BYTES:,}B 넘음")
    (K.ROOT / fname).write_text(html, encoding="utf-8")
    print(f"written {fname} ({size:,} B)")


# ── 1. 리뷰 사진 관리 ─────────────────────────────────
def photo_set(c):
    """사진 N장 · 사용 가능 여부 — 캠페인마다 고정 난수"""
    r = random.Random(f"photo-{c['id']}")
    n = sum(r.randint(3, 8) for _ in ok_reviews(c))
    hue = r.randint(0, 359)
    items = []
    for i in range(n):
        ok = r.random() < .7 and i not in (2, 7)      # 창 첫 화면에 "사용 불가" 예시가 꼭 보이게
        items.append({"h": (hue + i * 23) % 360, "ok": ok, "nick": r.choice(ok_reviews(c))["nick"],
                      "why": "" if ok else r.choice(NO_REASON)})
    return items


def photo_card(c, items):
    pid = f"ph-{c['id']}"
    use = sum(1 for p in items if p["ok"])
    ch = CH_KEY.get(c["ch"], "etc")
    cells = "".join(f'<i class="ph" style="--h:{p["h"]}"></i>' for p in items[:3])
    more = len(items) - 3
    cells += (f'<i class="ph more" style="--h:{items[3]["h"]}">+{more}</i>' if more > 0 else "")
    return (f'<article class="card pcard" data-biz="{c["bid"]}" data-ch="{ch}">'
            f'<div class="ph4" aria-hidden="true">{cells}</div>'
            f'<h3>{title_of(c)}</h3>{biz_line(c["b"])}'
            f'<p class="meta"><span class="chip">{esc(c["ch"])}</span><span>사진 {len(items)}장</span>'
            f'{K.badge("st-green", f"광고 사용 가능 {use}장")}</p>'
            f'<p class="bt"><a class="btn sm" href="{camp_link(c)}">캠페인보기</a>'
            f'{K.btn("사진보기", pop=pid)}</p></article>'), photo_pop(pid, c, items, use)


def photo_pop(pid, c, items, use):
    pct = round(use * 100 / len(items))
    tiles = "".join(
        f'<figure class="tile{"" if p["ok"] else " no"}"><i class="ph" style="--h:{p["h"]}"></i>'
        f'{K.badge("st-green", "사용 가능") if p["ok"] else K.badge("st-gray", "사용 불가")}'
        f'<figcaption>{esc(p["nick"])}{"" if p["ok"] else "<br>" + p["why"]}</figcaption></figure>'
        for p in items[:PHOTO_CAP])
    rest = len(items) - PHOTO_CAP
    body = (f'<p class="muted" style="margin:0">{title_of(c)}</p>'
            f'<p style="margin:0">{K.btn("다시 가져오기", "시안: 리뷰 사진을 다시 가져왔습니다")}</p>'
            f'<div class="usebar">광고 사용 가능<span class="bar"><i style="width:{pct}%"></i></span>'
            f'<b>{use}/{len(items)}장</b></div>'
            '<p class="help" style="margin:0">리뷰어가 동의한 범위 안에서만 광고에 쓸 수 있습니다.</p>'
            '<label class="chk"><input type="checkbox" class="only-ok"> 사용 가능한 사진만 보기</label>'
            f'<div class="tiles">{tiles}</div>'
            + (f'<p class="help">시안: 나머지 {rest}장은 생략했습니다.</p>' if rest > 0 else ""))
    return (f'<div id="{pid}" class="pop wide" popover><header><h2>등록된 리뷰 사진 리스트 ({len(items)})</h2>'
            f'<button type="button" class="btn sm" popovertarget="{pid}" popovertargetaction="hide">닫기</button></header>'
            f'<div class="pop-b">{body}</div></div>')


def build_photos():
    camps = [c for c in D.CAMPS if ok_reviews(c)]
    cards, pops = [], []
    for c in camps:
        card, pp = photo_card(c, photo_set(c))
        cards.append(card)
        pops.append(pp)
    chf = "".join(f'<label><input type="radio" name="chf" id="chf-{k}"{" checked" if k == "all" else ""}> {lab}</label>'
                  for k, lab in (("all", "전체"), ("blog", "블로그"), ("yt", "유튜브"), ("ig", "인스타")))
    body = (K.head("리뷰 사진 리스트", "승인된 리뷰의 사진 — 광고 사용 가능 여부는 리뷰어 동의 범위를 따릅니다")
            + K.camp_tabs("photo")
            + f'<div class="phs"><div class="fbar"><div class="chf" role="radiogroup" aria-label="채널">{chf}</div>'
            + biz_select() + f'<span class="sp"></span><span class="cnt">캠페인 <b>{len(cards)}</b>개</span></div>'
            + f'<div class="cards">{"".join(cards)}</div></div>' + "".join(pops))
    write("photos.html", "리뷰 사진 관리", "photo", body)


# ── 2. 검색결과 리포트 ────────────────────────────────
def rank_history(r):
    """수집 7회(최근 → 과거) — (수집일 오프셋, 최고 순위 or None, 노출, 대조)"""
    out = []
    for k in range(7):
        rk = r.choice([None, r.randint(1, 30), r.randint(1, 12), r.randint(1, 5)])
        tot = r.randint(3, 10)
        out.append((-k * 2, rk, r.randint(1, tot) if rk else 0, tot))
    return out


def srch_card(c):
    r = random.Random(f"srch-{c['id']}")
    kw = c["b"]["name"]
    hist = rank_history(r)
    _off, rk, shown, tot = hist[0]
    pid = f"sr-{c['id']}"
    expo = K.badge("st-purple", "검색노출") if rk else K.badge("st-gray", "미노출")
    rank = f'<span class="rk">검색순위 {rk}위</span>' if rk else '<span class="rk none">검색순위 —</span>'
    rep = (f'<label class="chk add inrep"><input type="checkbox"{" checked" if r.random() < .4 else ""}>'
           f' 보고서 링크에 싣기{K.add_tag()}</label>')
    card = (f'<article class="card scard" data-biz="{c["bid"]}"><p class="meta">{expo}</p>{rank}'
            f'<h3>{title_of(c)}</h3>{biz_line(c["b"])}'
            f'<p class="kw">키워드 \'{esc(kw)}\' · 리뷰 {shown}/{tot} 노출 · 갱신 {P.md(hist[0][0])}</p>'
            f'<p class="muted">신청 {c["applied"]} / 모집 {c["n"]}</p>'
            f'<p class="bt"><a class="btn sm" href="{camp_link(c)}">캠페인보기</a>{K.btn("검색 리포트", pop=pid)}</p>{rep}</article>')
    trs = "".join(f'<tr><td>{P.md(off)}</td><td class="num">{f"{x}위" if x else "—"}</td>'
                  f'<td class="num">{s}/{t}</td><td><a href="#" class="btn link">검색결과</a></td></tr>'
                  for off, x, s, t in hist)
    pp = (f'<div id="{pid}" class="pop" popover><header><h2>검색순위 리포트 {esc(kw)}</h2>'
          f'<button type="button" class="btn sm" popovertarget="{pid}" popovertargetaction="hide">닫기</button></header>'
          f'<div class="pop-b"><p class="muted" style="margin:0">{title_of(c)}</p>'
          f'<div class="owrap"><table class="otable"><thead><tr><th>수집일</th><th class="num">최고 순위</th>'
          f'<th class="num">노출/대조</th><th>검색결과</th></tr></thead><tbody>{trs}</tbody></table></div></div></div>')
    return card, pp


def wait_card(c):
    """빈 상태 예시 — 리뷰가 아직 없어 첫 수집 전"""
    return (f'<article class="card scard wait" data-biz="{c["bid"]}"><p class="meta">{K.badge("st-gray", "미노출")}</p>'
            f'<span class="rk none">첫 수집을 기다리고 있습니다</span><h3>{title_of(c)}</h3>{biz_line(c["b"])}'
            f'<p class="kw">키워드 \'{esc(c["b"]["name"])}\' · 리뷰 0/0 노출</p>'
            f'<p class="muted">신청 {c["applied"]} / 모집 {c["n"]}</p>'
            f'<p class="bt"><a class="btn sm" href="{camp_link(c)}">캠페인보기</a></p></article>')


def build_search():
    camps = [c for c in D.CAMPS if c["ch"] == "블로그" and ok_reviews(c)]
    cards, pops = [], []
    for c in camps:
        card, pp = srch_card(c)
        cards.append(card)
        pops.append(pp)
    waits = [c for c in D.CAMPS if c["ch"] == "블로그" and c["group"] == "rec"][:1]
    cards += [wait_card(c) for c in waits]
    note = ('<p class="mnote add">체크한 캠페인의 검색순위는 <a href="reports.html">보고서 링크</a>에도 실려 '
            f'업체 고객이 함께 봅니다{K.add_tag()}</p>')
    body = (K.head("검색결과 리포트", "블로그 리뷰가 키워드 검색에 노출되는지 수집한 결과")
            + K.camp_tabs("srch") + note
            + K.fbar(biz_select(), count=f"캠페인 <b>{len(cards)}</b>개")
            + f'<div class="cards">{"".join(cards)}</div>' + "".join(pops))
    write("search_report.html", "검색결과 리포트", "srch", body)


# ── 3. 영상 제작 요청 ─────────────────────────────────
VSTATE = {"접수": "st-gray", "제작중": "st-orange", "제공완료": "st-blue", "게시완료": "st-green", "취소": "st-red"}
CANCEL_SUB = ["요청 취소 · 5,000P 돌려받음", "제작 불가(원본 화질) · 5,000P 돌려받음"]


def build_video():
    r = random.Random("video")
    revs = [(c, rv) for c in D.CAMPS for rv in ok_reviews(c) if c["ch"] != "구매평"]
    pick = r.sample(revs, min(18, len(revs)))
    heads = [BIZ_HEAD, ("캠페인", ""), ("리뷰어", ""), ("채널", ""), ("승인일", ""), ("리뷰", ""), ("", "")]
    rows = [(f'data-biz="{c["bid"]}"', [biz_td(c["b"]), f'<a href="{camp_link(c)}">{title_of(c)}</a>', esc(rv["nick"]),
                                         esc(rv["ch"]), P.md(-rv["ago"]), '<a href="#" class="btn link">열기</a>',
                                         K.btn("영상 요청", pop="pop-vreq", cls="btn sm primary")])
            for c, rv in pick]
    can = K.table(heads, rows)

    states = ["접수", "제작중", "제작중", "제공완료", "게시완료", "게시완료", "취소", "취소", "접수", "제공완료"]
    hist = []
    for i, st in enumerate(states):
        c, _rv = r.choice(revs)
        kind = r.choice(["클립", "릴스", "쇼츠"])
        stc = K.badge(VSTATE[st], st)
        if st == "취소":
            stc += f'<small class="sub">{CANCEL_SUB[i % 2]}</small>'
        hist.append((f'data-biz="{c["bid"]}"', [
            biz_td(c["b"]), f'<a href="{camp_link(c)}">{title_of(c)}</a>', kind, K.won(VIDEO_PRICE), stc, P.md(-i * 2 - 1),
            '<a href="#" class="btn link">내려받기</a>' if st in ("제공완료", "게시완료") else "—",
            '<a href="#" class="btn link">보기</a>' if st == "게시완료" else "—",
            K.btn("취소", "시안: 요청을 취소했습니다(포인트 돌려받음)", "btn sm ghost-danger") if st == "접수" else "—"]))
    hheads = [BIZ_HEAD, ("캠페인", ""), ("종류", ""), ("금액", "num"), ("상태", ""), ("요청일", ""), ("영상", ""),
              ("게시", ""), ("취소", "")]
    price = (f'<div class="price"><span>클립 <b>{K.won(VIDEO_PRICE)}</b></span><span>릴스 <b>{K.won(VIDEO_PRICE)}</b></span>'
             f'<span>쇼츠 <b>{K.won(VIDEO_PRICE)}</b></span><span class="sp"></span>'
             f'<span>보유 포인트 <b>통포인트 {K.won(TONG_POINT)}</b></span></div>'
             '<p class="notice">※ 요청하시면 포인트가 바로 차감됩니다.</p>'
             f'<p class="notice add">통포인트에서 차감 · 업체별 사용내역에 표시{K.add_tag()}</p>')
    kinds = "".join(f'<label><input type="radio" name="vk"{" checked" if i == 0 else ""}> {k}</label>'
                    for i, k in enumerate(["클립", "릴스", "쇼츠"]))
    pp = K.pop("pop-vreq", "영상 제작 요청",
               f'<div class="fl">영상 종류<div class="radios">{kinds}</div></div>'
               '<label class="fl">요청사항<textarea placeholder="강조할 장면, 길이, 자막 등"></textarea></label>'
               '<label class="fl">참고자료 첨부<input type="file"></label>'
               f'<p class="help">요청하면 {K.won(VIDEO_PRICE)}가 바로 차감됩니다.'
               f' <span class="add">통포인트에서 차감 · 이 업체 사용내역에 표시{K.add_tag()}</span></p>',
               "요청하기", "시안: 영상 제작을 요청했습니다")
    body = (K.head("영상 제작 요청", "승인된 리뷰로 짧은 영상을 만들어 드립니다")
            + K.camp_tabs("video") + price
            + '<h2 class="sec-h">요청 가능한 리뷰</h2>' + K.fbar(biz_select(), count=f"리뷰 <b>{len(rows)}</b>건") + can
            + '<h2 class="sec-h">요청 내역</h2>' + K.table(hheads, hist) + pp)
    write("video.html", "영상 제작 요청", "video", body)


# ── 4. 쪽지 ───────────────────────────────────────────
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


def msg_pool(seed, n):
    """쪽지 n건 — 리뷰어가 있는 캠페인에서 업체·캠페인을 고른다"""
    r = random.Random(seed)
    camps = [c for c in D.CAMPS if c["rows"]]
    out = []
    for i in range(n):
        c = r.choice(camps)
        out.append({"c": c, "nick": r.choice(c["rows"])["nick"], "id": f"rv{r.randint(1000, 9999)}",
                    "off": -(i // 3), "hm": f"{r.randint(9, 21):02d}:{r.choice([0, 12, 25, 38, 47, 55]):02d}",
                    "file": r.random() < .25, "read": i >= 4 and r.random() < .8, "r": r})
    return out


def msg_tag(m):
    c = m["c"]
    return (f'<span class="tag add">{esc(c["b"]["name"])} · {esc(c["name"])} · 배정: {K.owner_of(c["b"])}'
            f'{K.add_tag()}</span>')


def stamp(off, hm, dot=True):
    d = P.d_of(off)
    return f'{d.month:02d}.{d.day:02d} {hm}' if dot else f'{d.year}.{d.month:02d}.{d.day:02d} {hm}'


def msg_rows(msgs, texts, sent, pre):
    rows, pops = [], []
    for i, m in enumerate(msgs):
        t, s = texts[i % len(texts)]
        clip = " 📎" if m["file"] else ""
        pid = f"{pre}-{i}" if i < 4 else ""
        ttl = (f'<button type="button" class="ttl" popovertarget="{pid}">{esc(t)}{clip}</button>' if pid
               else f'<span class="ttl">{esc(t)}{clip}</span>')
        rd = (K.badge("st-gray", "읽음") + f' <small>{stamp(m["off"], m["hm"])}</small>') if m["read"] else K.badge("st-red", "안읽음")
        rows.append((f'class="mrow{"" if m["read"] else " unread"}" data-biz="{m["c"]["bid"]}"', [
            f'{esc(m["nick"])}<br><small>{m["id"]}</small>', ttl + msg_tag(m), f'<span class="snip">{esc(s)}</span>',
            rd, stamp(m["off"], m["hm"], False)]))
        if pid:
            pops.append(msg_pop(pid, m, t, s, sent))
    return rows, pops


def msg_pop(pid, m, t, s, sent):
    who = "받는 사람" if sent else "보낸 사람"
    info = (f'<dl class="dl"><dt>{who}</dt><dd>{esc(m["nick"])} ({m["id"]})</dd><dt>제목</dt><dd>{esc(t)}</dd>'
            f'<dt>날짜</dt><dd>{stamp(m["off"], m["hm"], False)}</dd>'
            f'<dt>업체·캠페인 {K.add_tag()}</dt><dd class="add">{esc(m["c"]["b"]["name"])} · {esc(m["c"]["name"])}'
            f' · 배정: {K.owner_of(m["c"]["b"])}</dd></dl>'
            f'<div class="msg-b">{esc(s)}</div>' + ('<p class="help">📎 첨부파일 1개</p>' if m["file"] else ""))
    close = f'<button type="button" class="btn" popovertarget="{pid}" popovertargetaction="hide">닫기</button>'
    if sent:
        act = K.btn("발송취소", "시안: 발송을 취소했습니다", "btn ghost-danger") if not m["read"] else ""
        title = "보낸 쪽지"
    else:
        act = K.btn("답장하기", "시안: 답장 창(쪽지 보내기)", "btn primary")
        title = "쪽지 상세보기"
    return (f'<div id="{pid}" class="pop" popover><header><h2>{title}</h2>'
            f'<button type="button" class="btn sm" popovertarget="{pid}" popovertargetaction="hide">닫기</button></header>'
            f'<div class="pop-b">{info}</div><footer>{close}{act}</footer></div>')


def msg_search():
    return K.fbar(K.dates(), K.select("읽음", ["전체", "안읽음", "읽음"]),
                  '<input type="text" placeholder="이름" aria-label="이름">',
                  '<input type="text" placeholder="아이디" aria-label="아이디">', K.search("제목·내용"),
                  K.btn("검색", "시안: 검색", "btn sm primary"), K.btn("초기화", "시안: 초기화"), biz_select())


def send_cards(seed, kind, cost):
    r = random.Random(seed)
    camps = [c for c in D.CAMPS if c["rows"]]
    texts = (["[뷰마] 방문 예약 잊지 마세요", "[뷰마] 리뷰 마감 D-2 안내", "[뷰마] 선정 축하드립니다"] if kind == "sms" else
             ["체험단 선정 안내 메일", "리뷰 작성 가이드", "배송 출발 안내"])
    out = []
    for i in range(5):
        c = r.choice(camps)
        nicks = r.sample([x["nick"] for x in c["rows"]], min(len(c["rows"]), r.randint(1, 4)))
        out.append(f'<article class="card" data-biz="{c["bid"]}"><div class="body"><b>{texts[i % 3]}</b>'
                   f'<p class="muted">받는 리뷰어 {", ".join(esc(n) for n in nicks)} · {stamp(-i, "10:30", False)}</p>'
                   f'<p class="col-biz">{K.biz_cell(c["b"])} · {esc(c["name"])} · 배정: {K.owner_of(c["b"])}{K.add_tag()}</p></div>'
                   f'<span class="cost">{cost * len(nicks)}P 차감</span>'
                   f'{K.btn("다시 보내기", "시안: 다시 보냈습니다")}</article>')
    return f'<div class="sends">{"".join(out)}</div>'


def build_messages():
    heads = [("이름", ""), ("제목", ""), ("내용", ""), ("읽음", ""), ("날짜", "")]
    inbox = msg_pool("msg-in", 14)
    outbox = msg_pool("msg-out", 8)
    in_rows, in_pops = msg_rows(inbox, IN_MSG, False, "mi")
    out_rows, out_pops = msg_rows(outbox, OUT_MSG, True, "mo")
    unread = sum(1 for m in inbox if not m["read"])
    in_bulk = K.btn("선택 삭제", "시안: 삭제했습니다", "btn sm ghost-danger") + K.btn("전체읽음 처리", "시안: 모두 읽음으로 바꿨습니다")
    t_in = msg_search() + K.table(heads, in_rows, ck=True, bulk=in_bulk)
    t_out = msg_search() + K.table(heads, out_rows, ck=True, bulk=K.btn("선택 삭제", "시안: 삭제했습니다", "btn sm ghost-danger"))
    t_sms = msg_search() + send_cards("sms", "sms", 20)
    t_mail = msg_search() + send_cards("mail", "mail", 5)
    note = ('<p class="mnote add">광고주 사이트에 채팅은 없습니다(10-28 제거) — 리뷰어와는 쪽지로. '
            f'받은 쪽지는 업체 담당자에게 배정됩니다{K.add_tag()}</p>')
    body = (K.head("쪽지", "리뷰어와 주고받은 쪽지 · 보낸 문자·메일") + note
            + K.tabs("mb", [(f"받은쪽지함<em>{unread}</em>", t_in), ("보낸쪽지함", t_out),
                            ("문자발송함", t_sms), ("메일발송함", t_mail)])
            + "".join(in_pops + out_pops))
    write("messages.html", "쪽지", "chat", body)


def build():
    build_photos()
    build_search()
    build_video()
    build_messages()


if __name__ == "__main__":
    build()
