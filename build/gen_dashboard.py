# -*- coding: utf-8 -*-
"""
[2026-11-09] 대행사 사이트 MVP — 대시보드 시안 생성기
  기획서 v0.3 6-3 (업체 × 이슈 격자 + 처리 패널) 을 정적 HTML 로 만든다.
  더미 데이터는 고정 시드로 만들어 매번 같은 화면이 나온다.
  실행: python -I build/gen_dashboard.py  →  mvp/dashboard.html
"""
import html
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # -I 로 돌려도 같은 폴더 모듈을 찾게
import alerts  # noqa: E402  [2026-11-10] 수시 알림 (v0.4)

VERSION = "v0.9"   # 시안 버전 — mvp/CHANGELOG.md · git 태그와 맞춘다

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard.html"
TODAY_LABEL = "11월 9일 (월)"
rnd = random.Random(1109)

# ── 이슈 8종 (기획서 8-1) ─────────────────────────────
ISSUES = [
    ("apply",  "신청<br>확인"),
    ("select", "선정<br>임박"),
    ("prep",   "준비<br><small>발송·자료</small>"),
    ("review", "검수"),
    ("nudge",  "리뷰<br>독촉"),
    ("pay",    "지급"),
    ("point",  "포인트<br>부족"),
    ("owner",  "미담당"),
    ("late",   "마감<br>지남"),
]
ISSUE_NAME = {"apply": "신청 확인", "select": "선정 임박", "prep": "체험 준비", "review": "검수", "nudge": "리뷰 독촉",
              "pay": "지급", "point": "포인트 부족", "owner": "미담당 업체", "late": "마감 지남"}

# ── 직원·팀 (팀 2개 + 팀 없는 담당자 1) ───────────────
TEAMS = [
    ("A", "1팀", [("kje", "김지은", True), ("psj", "박서준", False), ("lhn", "이하늘", False)]),
    ("B", "2팀", [("cmh", "최민호", True), ("jyn", "정유나", False)]),
    (None, "팀 없음", [("hdy", "한도윤", False)]),
]
STAFF = [(sid, name, lead, tname) for _, tname, members in TEAMS for sid, name, lead in members]

BIZ_NAMES = [
    "연남 헤어살롱", "망원 파스타바", "성수 브런치랩", "합정 네일스튜디오", "을지로 노포갈비",
    "판교 필라테스", "서촌 한옥카페", "강남 피부과의원", "홍대 타코하우스", "잠실 키즈풀",
    "광교 치과의원", "송리단길 베이커리", "부산 해운대횟집", "제주 감귤농원", "대구 막창골목",
    "수원 왕갈비", "일산 애견미용", "분당 수학학원", "익선동 와인바", "용산 라멘집",
    "건대 마라탕", "목동 영어학원", "청담 속눈썹샵", "신촌 보드게임카페", "여의도 샐러드",
    "인천 차이나타운", "전주 한정식", "강릉 커피공장", "춘천 닭갈비", "평택 정육식당",
]
# [2026-11-09] 캠페인 유형·채널 — 뷰마 taxonomy 그대로(type 1 방문형 · 2 배송형 · 3 기자단, 채널 8종)
CAMP_META = {
    "11월 방문 체험단": ("v", "블로그"), "신메뉴 리뷰": ("v", "인스타"), "겨울 시즌 체험": ("v", "블로그"),
    "인스타 릴스 체험": ("v", "릴스"), "블로그 기자단": ("p", "블로그"), "보도자료 기자단": ("p", "블로그"),
    "신제품 배송 체험": ("s", "블로그"), "홈케어 키트 배송": ("s", "인스타"), "구매평 체험": ("s", "구매평"),
    "유튜브 쇼츠 체험": ("v", "쇼츠"),
}
CAMPAIGNS = list(CAMP_META)
TYPE_NAME = {"v": "방문형", "s": "배송형", "p": "기자단"}


def ctype(camp):
    return CAMP_META[camp][0]


def ccode(camp):
    """캠페인 번호(전역 고유) — 칸의 건 목록(data-camps)과 패널 건(li data-camp)을 잇는다"""
    return CAMPAIGNS.index(camp)


# 캠페인 상태 = 그 캠페인에 걸린 이슈로 추정 (기획서 4장, 체험 단계는 유형별 이름)
STATE_ORDER = [("apply", "모집 중"), ("select", "선정 중"), ("prep", None), ("review", "리뷰 중"),
               ("nudge", "리뷰 중"), ("pay", "정산 중"), ("late", "기한 지남")]
PREP_STATE = {"v": "체험 중", "s": "배송·체험 중", "p": "원고 작성 중"}


def camp_state(b, camp):
    for key, label in STATE_ORDER:
        it = b["issues"].get(key)
        if it and any(c == camp for c, _d in it["items"]):
            return label or PREP_STATE[ctype(camp)]
    return "진행 중"


CUR = {"bid": "", "key": ""}   # 패널을 만드는 동안 지금 업체·이슈 (캠페인 영역 id 용)
REVIEWERS = ["맛집탐방러", "하늘빛일상", "도토리기록", "서울먹방일기", "주말산책", "봄날의리뷰",
             "카페투어링", "육아맘일기", "뷰티로그", "운동하는곰", "여행가방", "소소한하루"]
CHANNELS = [("블로그", "방문자"), ("인스타", "팔로워"), ("유튜브", "구독자"), ("클립", "팔로워")]

esc = html.escape


def due_label(d):
    """[2026-11-09] 기한(오늘 기준 일수) → 칩 글자"""
    if d < 0:
        return f"{-d}일 지남"
    if d == 0:
        return "오늘"
    return f"D-{d}"


def due_class(d):
    if d <= 0:
        return "is-hot"     # 기한 지남·오늘 = 빨강
    if d <= 3:
        return "is-soon"    # 3일 내 = 주황
    return "is-later"       # 그 외 = 회색


MULTI = ("apply", "review", "nudge", "pay")       # 건이 여러 캠페인에 걸칠 수 있는 이슈
DUE_RANGE = {"apply": (0, 6), "review": (-1, 4), "nudge": (-1, 2), "pay": (1, 8)}


def issue_from(items):
    """[2026-11-09] items = [(캠페인, 기한일수), ...] 한 건씩. 칸 기한 = 가장 급한 건"""
    items = sorted(items, key=lambda x: x[1])
    return {"n": len(items), "due": items[0][1], "camp": items[0][0], "items": items}


def make_issue(key, camps):
    if key in MULTI:
        cnt = rnd.randint(1, 5)
        k = min(cnt, len(camps), rnd.choice([1, 2, 2, 3]))   # 캠페인 1~3개에 나눠 걸림
        lo, hi = DUE_RANGE[key]
        dues = rnd.sample(range(lo, hi + 1), k)
        split = [1] * k
        for _ in range(cnt - k):
            split[rnd.randrange(k)] += 1
        return issue_from([(camps[j], dues[j]) for j in range(k) for _ in range(split[j])])
    due = {"select": rnd.randint(0, 1), "point": 0, "late": -rnd.randint(1, 3)}[key]
    return issue_from([(rnd.choice(camps), due)])


def due_mix(items):
    """기한별 건수 — "오늘 1건 · D-2 1건 · D-5 1건" """
    seen = {}
    for _c, d in items:
        seen[d] = seen.get(d, 0) + 1
    return " · ".join(f"{due_label(d)} {n}건" for d, n in sorted(seen.items()))


def make_biz():
    """업체 30곳 + 이슈 무작위 배치 (이슈 없는 업체도 섞음)"""
    owners = [s for s in STAFF]
    rows = []
    for i, name in enumerate(BIZ_NAMES):
        owner = None if i in (7, 22) else owners[i % len(owners)]
        camps = rnd.sample(CAMPAIGNS, rnd.randint(2, 3))
        issues = {}
        if i % 4 != 3:  # 4곳 중 1곳은 이슈 없음
            for key in ["apply", "select", "review", "nudge", "pay", "point", "late"]:
                p = {"apply": .45, "select": .18, "review": .4, "nudge": .22, "pay": .3, "point": .06, "late": .1}[key]
                if rnd.random() < p:
                    issues[key] = make_issue(key, camps)
            prep_camps = [c for c in camps if ctype(c) in ("s", "p")]
            if prep_camps and rnd.random() < .55:
                items = []
                for c in prep_camps[:2]:
                    d = rnd.randint(0, 3) if ctype(c) == "s" else rnd.randint(-1, 2)
                    items += [(c, d)] * rnd.randint(1, 4)
                issues["prep"] = issue_from(items)
        if owner is None:
            issues["owner"] = issue_from([(camps[0], 0)])
        rows.append({"id": f"b{i}", "name": name, "owner": owner, "camps": camps, "issues": issues})
    # [2026-11-10 v0.8] 셸(업체 범위 목록 · 메뉴 숫자)도 같은 업체 데이터를 쓴다
    SCOPE_BIZ[:] = rows
    COUNTS.update({k: sum(b["issues"][k]["n"] for b in rows if k in b["issues"]) for k in ("review", "pay")})
    return rows


def biz_due(b):
    return min((v["due"] for v in b["issues"].values()), default=None)


def group_of(d):
    if d is None:
        return "none"
    if d < 0:
        return "late"
    if d == 0:
        return "today"
    if d <= 3:
        return "soon"
    return "later"


GROUPS = [("late", "기한 지남"), ("today", "오늘"), ("soon", "3일 내"), ("later", "그 외")]


# ── 격자 행 ─────────────────────────────────────────
def cell_html(b, key):
    it = b["issues"].get(key)
    if not it:
        return '<td class="c"><span class="dot" aria-label="없음">·</span></td>'
    cid = f'{b["id"]}-{key}'
    own = f' data-owner="{b["owner"][0]}"' if b["owner"] else ""
    dues = [d for _c, d in it["items"]]
    mix = due_mix(it["items"])
    # [2026-11-09] 기한이 섞인 칸만 아래 막대(빨강·주황·회색 비율). 색만으로 뜻을 전하지 않게 title·aria 에 글자로도
    bar = mixbar_html(dues) if len(set(dues)) > 1 else ""
    return (f'<td class="c"><button type="button" class="cell {due_class(it["due"])}" data-cell="{cid}"{own} '
            f'data-n="{it["n"]}" data-dues="{",".join(map(str, dues))}" data-types="{",".join(ctype(c) for c, _d in it["items"])}" data-camps="{",".join(str(ccode(c)) for c, _d in it["items"])}" title="{mix}" '
            f'aria-label="{esc(b["name"])} {ISSUE_NAME[key]} {it["n"]}건 · {mix}">'
            f'<b>{it["n"]}</b><small>{due_label(it["due"])}</small>{bar}</button></td>')


def mixbar_html(dues):
    segs = [(c, sum(1 for d in dues if due_class(d) == c)) for c in ("is-hot", "is-soon", "is-later")]
    return '<i class="mixbar" aria-hidden="true">' + "".join(
        f'<span class="{c}" style="flex:{n}"></span>' for c, n in segs if n) + "</i>"


def has_classes(keys):
    return " ".join(f"has-{k}" for k in keys)


def camp_rows(b):
    """[2026-11-09] 업체 행 아래 캠페인 줄 — 기본 접힘, 업체 이름 옆 [캠페인 N ▸] 체크박스로 펼침(CSS)
      칸 = 그 캠페인 건만. 숫자는 JS 가 업체 칸의 건 목록에서 다시 센다(처리·유형 칩 반영)"""
    rows = []
    for c in b["camps"]:
        ty, ch = CAMP_META[c]
        code = ccode(c)
        cells, keys, dues = [], [], []
        for k, _lab in ISSUES:
            it = b["issues"].get(k)
            mine = [d for x, d in it["items"] if x == c] if it else []
            if not mine:
                cells.append('<td class="c"><span class="dot" aria-hidden="true">·</span></td>')
                continue
            keys.append(k)
            dues += mine
            m = min(mine)
            cells.append(f'<td class="c"><button type="button" class="cell ccell {due_class(m)}" data-of="{b["id"]}-{k}" '
                         f'data-camp="{code}" aria-label="{esc(c)} {ISSUE_NAME[k]} {len(mine)}건">'
                         f'<b>{len(mine)}</b><small>{due_label(m)}</small></button></td>')
        nxt = f' · 다음 기한 {due_label(min(dues))}' if dues else ""
        rows.append(f'<tr class="camp {has_classes(keys)}" data-of-biz="{b["id"]}">'
                    f'<th scope="row" class="bizname cname"><span class="cn-l1"><span class="ty ty-{ty}">{TYPE_NAME[ty]}</span>'
                    f'<span class="chn">{ch}</span><b>{esc(c)}</b></span>'
                    f'<span class="cn-l2">{camp_state(b, c)}{nxt}</span></th>'
                    f'<td class="tot">{len(dues) or ""}</td>{"".join(cells)}</tr>')
    return "".join(rows)


def biz_row(b, show_owner=True):
    """[2026-11-09] data-g = 업체의 기한 묶음 → CSS 가 이름 칸 왼쪽 색 선으로 표시(어느 묶음 행인지 스크롤 중에도 보이게)"""
    owner = b["owner"]
    who = (f'<span class="who"><i>{esc(owner[1][0])}</i>{esc(owner[1])}</span>' if owner
           else '<span class="who none">미담당</span>')
    total = sum(v["n"] for v in b["issues"].values())
    cells = "".join(cell_html(b, k) for k, _ in ISSUES)
    gk = group_of(biz_due(b))
    staff_cls = "" if show_owner else " in-staff"
    cfold = (f'<label class="cfold"><input type="checkbox" class="camp-cb" aria-label="{esc(b["name"])} 캠페인 펼치기">'
             f'캠페인 {len(b["camps"])}</label>')
    return (f'<tr class="biz{staff_cls} {has_classes(b["issues"].keys())}" data-g="{gk}">'
            f'<th scope="row" class="bizname"><button type="button" class="bizlink" data-biz="{b["id"]}">{esc(b["name"])}</button>'
            f'<button type="button" class="adot" data-abiz="{b["id"]}" hidden><i aria-hidden="true"></i><em></em></button>'
            f'{who if show_owner else ""}'
            f'{cfold if show_owner else ""}</th>'
            f'<td class="tot">{total or ""}</td>{cells}</tr>'
            + (camp_rows(b) if show_owner else ""))


GROUP_DESC = {"late": "기한이 지난 이슈가 있는 업체", "today": "오늘까지 처리할 이슈가 있는 업체",
              "soon": "3일 안에 기한이 오는 업체", "later": "4일 이후 기한"}
GROUP_ICO = {"late": "!", "today": "●", "soon": "◔", "later": "○"}


def group_head(label, bizs, cls="grp", g=""):
    keys = {k for b in bizs for k in b["issues"]}
    dg = f' data-g="{g}"' if g else ""
    return (f'<tr class="{cls} {has_classes(keys)}"{dg}><th scope="rowgroup" colspan="{len(ISSUES) + 2}">'
            f'<span class="g-in"><span class="g-ico" aria-hidden="true">{GROUP_ICO.get(g, "")}</span>'
            f'<b>{label}</b><em class="g-n js-gcount">{len(bizs)}곳</em>'
            f'<span class="g-desc">{GROUP_DESC.get(g, "")}</span></span></th></tr>')


def sum_cells(bizs, attr=None):
    out = []
    for k, _ in ISSUES:
        n = sum(b["issues"][k]["n"] for b in bizs if k in b["issues"])
        data = f' data-sum="{attr}-{k}"' if attr else ""
        out.append(f'<td class="c"><span class="sum{" zero" if not n else ""}"{data}>{n or "·"}</span></td>')
    return "".join(out)


def tbody_by_biz(bizs):
    """[업체별] 보기 — 급한 순 묶음, 이슈 없음은 접힘"""
    parts = ['<tbody class="tb-biz">']
    sorted_b = sorted(bizs, key=lambda b: (biz_due(b) if biz_due(b) is not None else 99, -len(b["issues"])))
    for gkey, glabel in GROUPS:
        gb = [b for b in sorted_b if group_of(biz_due(b)) == gkey]
        parts.append(group_head(glabel, gb, f"grp grp-{gkey}", gkey))
        parts += [biz_row(b) for b in gb]
    parts.append("</tbody>")
    none = [b for b in bizs if not b["issues"]]
    # [2026-11-09] 이슈 없는 업체는 기본 접힘 — 펼침은 JS 없이 체크박스 + CSS
    parts.append('<tbody class="tb-biz tb-none">'
                 f'<tr class="grp grp-none"><th colspan="{len(ISSUES) + 2}">'
                 f'<label class="fold"><input type="checkbox" class="fold-cb">이슈 없음 <em class="js-gcount">{len(none)}곳</em>'
                 '<span class="fold-ico" aria-hidden="true"></span></label></th></tr>')
    parts += [biz_row(b).replace('class="biz ', 'class="biz quiet ') for b in none]
    parts.append("</tbody>")
    return "".join(parts)


def tbody_by_staff(bizs):
    """[담당자별] 보기 — 미담당 → 팀 → 담당자 → 업체"""
    parts = ['<tbody class="tb-staff">']
    un = [b for b in bizs if b["owner"] is None]
    if un:
        parts.append(f'<tr class="team team-none-owner has-owner"><th scope="rowgroup" colspan="{len(ISSUES) + 2}">'
                     f'<span class="g-in"><span class="g-ico" aria-hidden="true">!</span><b>미담당 업체</b>'
                     f'<em class="g-n">{len(un)}곳</em><span class="g-desc">담당자를 정해 주세요</span></span></th></tr>')
        parts += [biz_row(b, False) for b in un]
    for _, tname, members in TEAMS:
        team_b = [b for b in bizs if b["owner"] and b["owner"][3] == tname]
        lead_name = next((n for _s, n, ld in members if ld), None)
        t_issue = sum(v["n"] for b in team_b for v in b["issues"].values())
        t_late = sum(1 for b in team_b if b["issues"] and biz_due(b) < 0)
        meta = (f'팀장 {lead_name} · ' if lead_name else "") + f'담당자 {len(members)}명 · 업체 {len(team_b)}곳 · 이슈 {t_issue}건'
        tcls = "team" if lead_name else "team team-solo"
        parts.append(f'<tr class="{tcls} {has_classes({k for b in team_b for k in b["issues"]})}">'
                     f'<th scope="rowgroup" colspan="{len(ISSUES) + 2}"><span class="g-in"><b>{tname}</b>'
                     f'<span class="g-desc">{meta}</span>'
                     f'{f"<em class=g-late>기한 지남 {t_late}곳</em>" if t_late else ""}</span></th></tr>')
        for sid, sname, lead in members:
            mine = [b for b in team_b if b["owner"][0] == sid]
            mine.sort(key=lambda b: biz_due(b) if biz_due(b) is not None else 99)
            issues_n = sum(v["n"] for b in mine for v in b["issues"].values())
            late_n = sum(1 for b in mine if b["issues"] and biz_due(b) < 0)
            badge = '<span class="lead">팀장</span>' if lead else ""
            parts.append(f'<tr class="staff {has_classes({k for b in mine for k in b["issues"]})}">'
                         f'<th scope="row"><span class="who"><i>{sname[0]}</i>{sname}</span>{badge}'
                         f'<em>업체 {len(mine)}곳{f" · <span class=late-t>기한 지남 {late_n}</span>" if late_n else ""}</em></th>'
                         f'<td class="tot"><span class="sum" data-sum="s-{sid}-total">{issues_n}</span></td>{sum_cells(mine, "s-" + sid)}</tr>')
            parts += [biz_row(b, False) for b in mine if b["issues"]]
    parts.append("</tbody>")
    return "".join(parts)


# ── 처리 패널 (칸마다 하나씩 미리 만들어 두고 JS 로 보이기만) ──────────




def point_rows():
    return ('<dl class="kv"><dt>추가 예치 필요</dt><dd>165,000P</dd><dt>사용 가능 잔액</dt><dd class="bad">84,500P</dd></dl>'
            '<p class="ctx">초과모집 3명 요청 · 잔액이 부족해 대기 중입니다.</p>'
            '<div class="acts wide"><a class="ag-btn primary" href="point.html">충전하기 (포인트) →</a>'
            '<button type="button" class="ag-btn" disabled title="잔액이 부족합니다">예치하고 진행</button></div>')


def owner_rows():
    opts = "".join(f'<option>{s[1]} ({s[3]})</option>' for s in STAFF)
    return ('<p class="ctx">담당자가 없어 이 업체의 이슈 알림이 관리자에게만 갑니다.</p>'
            f'<div class="assign"><select class="input" aria-label="담당자 선택"><option>담당자 선택</option>{opts}</select>'
            '<button type="button" class="ag-btn primary" data-done="배정됨" data-whole>배정</button></div>'
            '<button type="button" class="ag-btn link" data-done="내가 맡음" data-whole>내가 맡기</button>')


def late_rows(it, b=None):
    return (f'<p class="ctx">모집 마감이 {-it["due"]}일 지났는데 선정 단계로 넘어가지 않았습니다.</p>'
            '<div class="acts wide"><button type="button" class="ag-btn primary" data-done="선정 단계로 넘김" data-whole>이대로 진행</button>'
            f'<a class="ag-btn" href="{detail_href(b, "late", it) if b else "#"}">기간 연장 (상세 관리) →</a></div>')


def by_campaign(items):
    """[(캠페인, 기한)] → [(캠페인, 기한, 건수)] 급한 순"""
    out = {}
    for c, d in items:
        out[(c, d)] = out.get((c, d), 0) + 1
    return sorted(((c, d, n) for (c, d), n in out.items()), key=lambda x: x[1])


def cgroup(camp, due, n, unit, inner):
    """[2026-11-09] 캠페인 영역 카드 — 사용자: "캠페인별 리뷰어가 이 캠페인에 해당한다고 영역을 명확히"
      카드 테두리 + 유형 색 왼쪽 띠 + 고정 머리(스크롤해도 어느 캠페인인지 보임) + 안쪽은 그 캠페인 리뷰어만"""
    ty, ch = CAMP_META[camp]
    b = CUR.get("biz")
    state = camp_state(b, camp) if b else ""
    gid = f'cg-{CUR["bid"]}-{CUR["key"]}-{ccode(camp)}'
    return (f'<section class="cgroup cg-{ty}" id="{gid}" data-type="{ty}" data-camp="{ccode(camp)}" aria-label="{esc(camp)} 캠페인">'
            f'<header class="cgroup-h"><div class="cg-l1"><span class="ty ty-{ty}">{TYPE_NAME[ty]}</span>'
            f'<span class="chn">{ch}</span><b class="cg-name">{esc(camp)}</b></div>'
            f'<div class="cg-l2"><span class="cg-state">{state}</span>'
            f'<span class="due {due_class(due)}">{due_label(due)}</span><em>{unit} {n}</em></div></header>'
            f'<div class="cgroup-b">{inner}</div></section>')



def make_evidence():
    """[2026-11-09] 신청자 선정 근거 더미
      - 블로그지수: 기존 뷰마 blogIndex(0~10, 7↑ 최적화 · 5↑ 준최적화 · 그 외 일반). 수집 전이면 None
      - 뷰마 이력: 참여 횟수(기존 getParticipationCount) · 기한 내 등록률 · 검수 승인률 · 패널티(기존)
      - 평점: ★ 뷰마에 아직 없는 데이터(신규 — 개발 메모). 이력 없으면 None"""
    bi = None
    if rnd.random() < 0.75:
        score = round(rnd.uniform(2.0, 9.6), 1)
        grade = "최적화" if score >= 7 else "준최적화" if score >= 5 else "일반"
        bi = {"score": score, "grade": grade, "visit": rnd.choice([40, 120, 380, 860, 1500, 3200]),
              "post30": rnd.randint(0, 28), "neighbor": rnd.choice([120, 480, 1300, 2600, 5400])}
    part = rnd.choice([0, 0, 1, 3, 6, 12, 24])
    hist = None
    if part:
        hist = {"part": part, "ontime": rnd.choice([100, 96, 90, 83, 70]), "pass": rnd.choice([100, 95, 88, 75]),
                "rating": round(rnd.uniform(3.4, 5.0), 1), "ours": rnd.choice([0, 0, 1, 2]),
                "penalty": rnd.random() < 0.12}
    return bi, hist


GRADE_CLS = {"최적화": "bi-opt", "준최적화": "bi-semi", "일반": "bi-normal"}


def evidence_html(bi, hist):
    """신청자 줄의 근거 두 줄: ① 블로그지수 ② 뷰마 이력·평점"""
    if bi:
        l1 = (f'<span class="bi {GRADE_CLS[bi["grade"]]}">{bi["grade"]}</span><b class="ag-bi-score">{bi["score"]}</b>'
              f'<span class="ev">일 방문 {bi["visit"]:,} · 최근 30일 {bi["post30"]}글 · 이웃 {bi["neighbor"]:,}</span>')
    else:
        l1 = '<span class="bi ag-bi-none">지수 수집 전</span>'
    if hist:
        warn = '<span class="pen">패널티 이력</span>' if hist["penalty"] else ""
        ours = f'<span class="ours">우리와 {hist["ours"]}회</span>' if hist["ours"] else ""
        l2 = (f'<span class="star" aria-label="평점 {hist["rating"]}점">★ {hist["rating"]}</span>'
              f'<span class="ev">뷰마 참여 {hist["part"]}회 · 기한 내 등록 {hist["ontime"]}% · 검수 승인 {hist["pass"]}%</span>{ours}{warn}')
    else:
        l2 = '<span class="ev new">뷰마 첫 참여 — 이력·평점 없음</span>'
    return f'<span class="evi">{l1}</span><span class="evi">{l2}</span>'


def applicant_li(due, mark=False):
    """신청자 한 줄 + 선정 근거. mark=True 면 표시만(선정 마감 — 이슈 처리는 [선정 완료] 한 번)
      [2026-11-09] 선정 전에 근거부터: 블로그지수나 뷰마 이력이 있으면 줄에 바로 보이므로 [선정] 가능.
        둘 다 없는 첫 참여 리뷰어는 [블로그 보기]로 직접 확인해야 [선정]이 켜진다(JS)."""
    bi, hist = make_evidence()
    need_check = not bi and not hist
    nick = rnd.choice(REVIEWERS)
    li_attr = "" if mark else f' data-due="{due}"'
    b_attr = " data-mark" if mark else ""
    sort = (f' data-bi="{bi["score"] if bi else 0}" data-rate="{hist["rating"] if hist else 0}"'
            f' data-ours="{hist["ours"] if hist else 0}"')
    lock = ' disabled title="블로그를 먼저 확인하세요"' if need_check else ""
    gate = ('<span class="gate">근거 없음 · 블로그를 열어 확인한 뒤 선정할 수 있어요</span>' if need_check else "")
    return (f'<li class="item ap{" need-check" if need_check else ""}"{li_attr}{sort}>'
            f'<div class="item-main"><b>{nick}</b>{evidence_html(bi, hist)}'
            f'<span class="memo">"{rnd.choice(["주말 방문 가능해요", "아이와 함께 방문 예정", "사진 위주로 작성합니다", "평일 저녁 방문"])}"</span>'
            f'<a href="#" class="blog-open js-blog">블로그 보기 ↗</a>{gate}</div>'
            f'<div class="acts"><button type="button" class="ag-btn sm primary js-pick"{b_attr}{lock} data-done="선정됨">선정</button>'
            f'<button type="button" class="ag-btn sm"{b_attr} data-done="보류">보류</button></div></li>')


SORT_CHIPS = ('<div class="sorts" role="group" aria-label="신청자 정렬">'
              '<button type="button" class="sort ag-on" data-sort="">신청순</button>'
              '<button type="button" class="sort" data-sort="bi">블로그지수순</button>'
              '<button type="button" class="sort" data-sort="rate">평점순</button>'
              '<button type="button" class="sort" data-sort="ours">우리와 해본 리뷰어</button></div>')


def review_li(due):
    ch, _u = rnd.choice(CHANNELS)
    return (f'<li class="item col" data-due="{due}"><div class="item-main"><b>{rnd.choice(REVIEWERS)}</b>'
            f'<span class="meta">{ch} · 등록 {rnd.randint(1, 3)}일 전 · <a href="#" class="ext">리뷰 보기 ↗</a></span></div>'
            '<div class="checks"><label><input type="checkbox" checked> 필수 키워드</label>'
            '<label><input type="checkbox" checked> 글자 수</label><label><input type="checkbox"> 사진 5장</label>'
            '<label><input type="checkbox" checked> 광고 표시</label></div>'
            '<div class="acts"><button type="button" class="ag-btn sm primary" data-done="승인">승인</button>'
            '<button type="button" class="ag-btn sm" data-done="수정 요청 보냄">수정 요청</button>'
            '<button type="button" class="ag-btn sm ghost-danger" data-done="반려">반려</button></div></li>')


# ── 추가모집 (= 기존 초과모집 + 재모집, 11-09 사용자 확정) ─────────────
#   열고 닫기는 <details> (JS 없음). 비용 미리보기 계산·시작 표시만 JS.
#   비용 = 추가 인원 × 리뷰어 지급(수수료 포함) + 등급 무료 한도를 넘는 인원 × 초과모집 단가
GRADE_FREE = 2          # 대행사 등급별 캠페인당 무료 추가 인원(예시 — 마스터 설정값)
OVER_UNIT = 10000       # 초과모집 단가(예시 — 회의: 일괄 1만 원 → 등급별 설정)
REWARD = 5500           # 리뷰어 지급 5,000P + 플랫폼 수수료 10%
BALANCE = 1284500       # 사이드바 사용 가능 잔액과 같은 값

RECRUIT_KIND = {
    "add":     ("추가 모집", "신청자가 모자라면 모집을 다시 열어 더 받습니다", 3, "+3", "선정 중 → 모집 중으로 돌아갑니다"),
    "more":    ("인원 늘리기", "좋은 신청자가 많으면 뽑을 인원을 늘립니다", 2, "0", "모집은 그대로, 선정 인원만 늘어납니다"),
    "replace": ("대체 리뷰어 모집", "포기·미등록 리뷰어 자리를 다시 모집합니다", 1, "+5", "빈자리만큼 모집을 다시 엽니다"),
}


def recruit_box(kind, camp):
    title, desc, n, ext, note = RECRUIT_KIND[kind]
    exts = "".join(f'<option value="{v}"{" selected" if v == ext else ""}>{lab}</option>'
                   for v, lab in (("0", "연장 없음"), ("+3", "+3일"), ("+5", "+5일"), ("+7", "+7일")))
    return (f'<details class="recruit" data-free="{GRADE_FREE}" data-unit="{OVER_UNIT}" data-reward="{REWARD}" data-bal="{BALANCE}">'
            f'<summary><span class="rc-t">{title}</span><span class="rc-d">{desc}</span></summary>'
            f'<div class="rc-b"><p class="rc-camp">{esc(camp)}</p>'
            '<div class="rc-f">'
            f'<label>추가 인원 <input type="number" class="input rc-n" min="1" max="20" value="{n}"> 명</label>'
            f'<label>모집 기간 <select class="input rc-ext">{exts}</select></label></div>'
            '<dl class="rc-cost">'
            '<dt>리뷰어 지급 예치</dt><dd class="js-c-reward"></dd>'
            f'<dt>등급 무료 한도 <small>(캠페인당 {GRADE_FREE}명)</small></dt><dd class="js-c-free"></dd>'
            '<dt>초과모집 비용</dt><dd class="js-c-over"></dd>'
            '<dt class="tot">추가 예치 합계</dt><dd class="tot js-c-total"></dd>'
            '<dt>사용 가능 잔액</dt><dd class="js-c-bal"></dd></dl>'
            f'<p class="rc-note">{note} · 이력에 남습니다</p>'
            '<div class="acts wide"><button type="button" class="ag-btn primary js-recruit" data-kind="' + kind + '">'
            f'{title} 시작</button></div></div></details>')


def typed(li, camp):
    """건(li)에 캠페인 유형을 붙인다 — 유형 칩으로 거를 때 JS 가 같이 뺀다"""
    return li.replace("<li ", f'<li data-type="{ctype(camp)}" data-camp="{ccode(camp)}" ', 1)


def grouped(it, unit, li_fn, recruit=None):
    return "".join(cgroup(c, d, n, unit, '<ul class="items">' + "".join(typed(li_fn(d), c) for _ in range(n)) + "</ul>"
                          + (recruit_box(recruit, c) if recruit else ""))
                   for c, d, n in by_campaign(it["items"]))


# ── 체험 준비 (유형별로 다른 일) ───────────────────────────
ADDRS = ["서울 마포구 월드컵로 ***", "경기 성남시 분당구 판교역로 ***", "부산 해운대구 우동 ***", "인천 연수구 송도동 ***"]


def ship_li(due):
    """배송형 — 선정자 배송정보(기존: 선정자에게만, 신청 후 3개월까지) + 발송 완료(★ 신규 기능)"""
    nick = rnd.choice(REVIEWERS)
    return (f'<li class="item col" data-due="{due}"><div class="item-main"><b>{nick}</b>'
            f'<span class="meta">📦 {rnd.choice(ADDRS)} · 010-****-{rnd.randint(1000, 9999)}</span></div>'
            '<div class="ship-f"><input class="input" placeholder="운송장 번호(선택)" aria-label="운송장 번호">'
            '<button type="button" class="ag-btn sm primary" data-done="발송 완료">발송 완료</button></div></li>')


def press_li(due):
    """기자단 — 자료를 받아 가지 않은 리뷰어(기존 campaignMaterialDown 기록)"""
    return (f'<li class="item" data-due="{due}"><div class="item-main"><b>{rnd.choice(REVIEWERS)}</b>'
            f'<span class="meta">선정 {rnd.randint(1, 4)}일 전 · 자료 아직 안 받아 감</span></div>'
            '<div class="acts"><button type="button" class="ag-btn sm" data-done="다시 알림 보냄">다시 알림</button></div></li>')


def prep_body(it):
    parts = []
    for c, d, n in by_campaign(it["items"]):
        if ctype(c) == "s":
            inner = (f'<p class="ctx">배송 시작일 {due_label(d)} · 아직 보내지 않은 <b>{n}명</b></p>'
                     '<ul class="items">' + "".join(typed(ship_li(d), c) for _ in range(n)) + "</ul>"
                     '<p class="note">주소는 선정자에게만, 신청 후 3개월까지 보입니다(기존 규칙). 발송 완료·운송장 기록은 새 기능입니다.</p>')
            parts.append(cgroup(c, d, n, "발송", inner))
        else:
            if rnd.random() < .45:
                # 자료가 아직 없음 — 올려야 리뷰어가 글을 쓸 수 있다. 올리면 묶음 전체가 처리됨
                inner = (f'<p class="ctx"><span class="warn-t">전달 자료가 없습니다</span> · 선정된 {n}명이 원고를 시작하지 못하고 있어요</p>'
                         '<div class="upload"><input type="file" class="input" aria-label="보도자료·이미지·가이드라인">'
                         '<button type="button" class="ag-btn primary" data-done="자료 올림 · 선정자에게 알림" data-gwhole>올리고 알림 보내기</button></div>'
                         '<ul class="items hidden-items">' + "".join(typed(press_li(d), c) for _ in range(n)) + "</ul>")
                parts.append(cgroup(c, d, n, "미전달", inner))
            else:
                got = rnd.randint(1, 4)
                inner = (f'<p class="ctx">전달 자료: <b>가이드라인.pdf · 보도자료.hwp</b> (11/7 올림) · 받아 감 {got}/{got + n}명</p>'
                         '<ul class="items">' + "".join(typed(press_li(d), c) for _ in range(n)) + "</ul>")
                parts.append(cgroup(c, d, n, "미수령", inner))
    return "".join(parts)


def nudge_body(it):
    groups = "".join(cgroup(c, d, n, "미등록", f'<p class="names">{", ".join(rnd.sample(REVIEWERS, n))}</p>'
                            + recruit_box("replace", c))
                     for c, d, n in by_campaign(it["items"]))
    return (groups + '<div class="acts wide"><button type="button" class="ag-btn primary" data-done="등록 요청 알림 보냄" data-whole>'
            f'미등록 {it["n"]}명에게 등록 요청 알림</button></div>')


def pay_body(it):
    total = 0
    parts = []
    for c, d, n in by_campaign(it["items"]):
        lis = []
        for _ in range(n):
            amt = rnd.choice([5000, 10000, 15000, 30000])
            total += amt
            lis.append(f'<li class="item"><div class="item-main"><b>{rnd.choice(REVIEWERS)}</b>'
                       f'<span class="meta">검수 승인 · 계좌 확인됨</span></div><span class="amt">{amt:,}P</span></li>')
        parts.append(cgroup(c, d, n, "지급", '<ul class="items">' + "".join(lis) + "</ul>"))
    return ("".join(parts) + f'<p class="ctx sum-line">합계 <b>{total:,}P</b> · 플랫폼 수수료 10% 포함 차감 {int(total * 1.1):,}P</p>'
            '<div class="acts wide"><button type="button" class="ag-btn primary" data-done="지급 확정됨" data-whole>지급 확정</button></div>')


def select_body(it):
    c, d = it["items"][0]
    lis = "".join(applicant_li(d, mark=True) for _ in range(4))
    return (SORT_CHIPS + cgroup(c, d, 1, "캠페인", '<p class="ctx"><span class="warn-t">3명 더 뽑아야 합니다</span> (선정 2/5명)</p>'
                   f'<ul class="items">{lis}</ul>')
            + '<div class="acts wide"><button type="button" class="ag-btn primary" data-done="선정 완료" data-whole>선정 완료</button></div>'
            + '<p class="or">신청자 중에 뽑을 사람이 모자라면</p>' + recruit_box("add", c))


def panel_body(key, it):
    return {
        "apply": lambda: SORT_CHIPS + grouped(it, "신청", applicant_li, "more"),
        "select": lambda: select_body(it),
        "prep": lambda: prep_body(it),
        "review": lambda: grouped(it, "리뷰", review_li),
        "nudge": lambda: nudge_body(it),
        "pay": lambda: pay_body(it),
        "point": point_rows,
        "owner": owner_rows,
        "late": lambda: late_rows(it, CUR.get("biz")),
    }[key]()


def camp_index(b, key, it):
    camps = []
    for c, _d in it["items"]:
        if c not in camps:
            camps.append(c)
    if len(camps) < 2:
        return ""
    links = "".join(
        f'<a href="#cg-{b["id"]}-{key}-{ccode(c)}" class="cidx cg-{ctype(c)}"><span class="ty ty-{ctype(c)}">{TYPE_NAME[ctype(c)]}</span>'
        f'{esc(c)} <em>{sum(1 for x, _d in it["items"] if x == c)}</em></a>' for c in camps)
    return f'<nav class="cindex" aria-label="이 이슈가 걸린 캠페인"><span>캠페인 {len(camps)}개</span>{links}</nav>'


# [2026-11-10 v0.6] [상세 관리 →] = 캠페인 페이지의 그 이슈 탭(기획서 6-4 "검수 카드 → 리뷰 탭")
# [2026-11-10 v0.8] [상세 관리 →] = 운영 층 그 화면(검수 → 리뷰 검수, 지급 → 포인트 지급 확인, 포인트 → 포인트)
DETAIL_TAB = {"apply": "app", "select": "app", "prep": "rev", "review": "rev", "nudge": "rev", "pay": "rev",
              "point": "ov", "late": "app"}
DETAIL_PAGE = {"review": "inspect.html", "pay": "payout.html", "point": "point.html"}


def detail_href(b, key, it):
    if key == "owner":
        return f'biz.html#biz={b["id"]}'          # 담당자 없음 = 업체 화면에서 배정
    if key in DETAIL_PAGE:
        return f'{DETAIL_PAGE[key]}?biz={b["id"]}'   # 업체 범위를 그 업체로 걸고 연다
    return f'campaigns.html#c-{b["id"]}-{ccode(it["camp"])}-{DETAIL_TAB[key]}'


def panel(b, key):
    CUR.update({"bid": b["id"], "key": key, "biz": b})
    it = b["issues"][key]
    owner = b["owner"][1] if b["owner"] else "미담당"
    chips = "".join(
        f'<button type="button" class="pchip{" ag-on" if k == key else ""}" data-go="{b["id"]}-{k}">'
        f'{ISSUE_NAME[k]} {v["n"]}</button>' for k, v in sorted(b["issues"].items(), key=lambda kv: kv[1]["due"]))
    return (f'<section class="pane" data-panel="{b["id"]}-{key}" hidden>'
            f'<header class="pane-h"><p class="pane-biz">{esc(b["name"])} <span>담당 {owner}'
            f'{" · <a href=\'#\'>변경</a>" if b["owner"] else ""}</span></p>'
            f'<h2>{ISSUE_NAME[key]} <em>{it["n"]}건</em> <span class="due js-due {due_class(it["due"])}">{due_label(it["due"])}</span></h2>'
            f'<p class="pane-camp js-mix">{due_mix(it["items"])}</p>'
            f'<div class="pchips" aria-label="이 업체의 다른 이슈">{chips}</div></header>'
            f'<div class="pane-b">{camp_index(b, key, it)}{panel_body(key, it)}</div>'
            f'<footer class="pane-f"><a href="{detail_href(b, key, it)}" class="ag-btn ghost">상세 관리 →</a>'
            f'<button type="button" class="ag-btn primary js-next">다음 ▶</button></footer></section>')


# ── 셸 ────────────────────────────────────────────
ICON = {
    "dash": '<path d="M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z"/>',
    "cal": '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>',
    "biz": '<path d="M3 21V8l9-5 9 5v13M9 21v-6h6v6"/>',
    "camp": '<path d="M4 4h16v4H4zM4 12h16M4 16h10"/>',
    "rep": '<path d="M6 3h9l4 4v14H6zM9 13h6M9 17h6"/>',
    "pay": '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M2 10h20"/>',
    "team": '<circle cx="9" cy="8" r="3.5"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6M16 4.5a3.5 3.5 0 0 1 0 7M18 15c2.5.6 4 2.6 4 6"/>',
    "set": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    # [2026-11-10 v0.8] 운영·계정 메뉴
    "rvw": '<circle cx="10" cy="8" r="4"/><path d="M3 21c0-4 3-7 7-7M16 15l2 2 4-4"/>',
    "insp": '<path d="M9 11l2 2 4-4"/><rect x="4" y="3" width="16" height="18" rx="2"/>',
    "payc": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "photo": '<rect x="3" y="5" width="18" height="15" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M21 17l-5-5-8 8"/>',
    "srch": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5M8 11h6"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10l6-3v10l-6-3"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
    "plan": '<path d="M4 7h16v12H4zM8 7V5h8v2M4 12h16"/>',
    "sms": '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 18h4"/>',
    "pen": '<path d="M12 3l9 16H3zM12 10v4M12 17v.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6M12 17v.5"/>',
}


def ico(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICON[name]}</svg>'


# [2026-11-10 v0.8] 메뉴 = 세 묶음(기획 구조재설계_v0.8안 3장)
#   대행사 = 광고주 사이트에 없는 것 / 캠페인 운영 = 광고주 "캠페인 관리" 그대로 / 계정 = 광고주 계정 기능을 대행사 1개 단위로
#   (키, 이름, 주소, 화면이 있는가) — 아직 없는 화면은 흐리게 + "광고주 화면 그대로 예정"
NAV = [
    ("대행사", [("dash", "대시보드", "dashboard.html"), ("cal", "일정", "schedule.html"), ("biz", "업체", "biz.html"),
              ("team", "팀·담당자", "team.html"), ("rep", "보고서 링크", "reports.html")]),
    ("캠페인 운영", [("camp", "캠페인 리스트", "campaigns.html"), ("rvw", "리뷰어 관리", "reviewers.html"),
                ("insp", "리뷰 검수", "inspect.html"), ("payc", "포인트 지급 확인", "payout.html"),
                ("photo", "리뷰 사진 관리", "photos.html"), ("srch", "검색결과 리포트", "search_report.html"),
                ("video", "영상 제작 요청", "video.html"), ("chat", "쪽지", "messages.html")]),
    # ※ 광고주 사이트에 채팅은 없음(2026-10-28 제거) — 쪽지만
    ("계정", [("pay", "포인트", "point.html"), ("plan", "사용료", "plan.html"), ("sms", "문자설정", "sms.html"),
            ("pen", "패널티", "penalty.html"), ("info", "마이페이지", "info.html"), ("noti", "알림", "notifications.html"),
            ("notice", "공지사항", "notice.html"), ("qna", "1:1 문의", "inquiry.html"), ("faq", "자주묻는 질문", "faq.html"),
            ("smsbox", "문자·메일 발송내역", "sms_box.html"), ("home", "홈", "home.html"), ("agcy", "대행사 신청", "agency_apply.html")]),
]
NAV_HREF = {k: href for _g, items in NAV for k, _l, href in items}
OPS = {k for k, _l, _h in NAV[1][1]}          # 업체 범위가 걸리는 화면(운영 층)
# 만들어진 화면 — 화면을 새로 만들면 여기에 키를 더한다(생성 순서와 상관없이 모든 화면의 메뉴가 같게)
READY = {"dash", "cal", "biz", "rep", "camp", "team", "rvw", "insp", "payc", "photo", "srch", "video", "chat",
         "pay", "plan", "sms", "pen", "info", "noti", "notice", "qna", "faq", "smsbox"}


def _built():
    return READY


COUNTS = {}        # 메뉴 숫자(검수·지급) — make_biz() 가 채운다


# [2026-11-11 v0.9] 셸 = 광고주 사이트 그대로(U:\admin\index.html · inc\sidebar.inc.html 마크업 · css\adv\main.css)
#   광고주 메뉴 자리: 홈 → 대시보드, 캠페인 관리(하위 5) · 마이페이지 → 대행사 정보 · 문자설정 · 문자·메일 발송내역 · 패널티 · 1:1 문의 · 자주묻는 질문 · 도움말
#   대행사 추가분(.add): 대시보드 숫자 · "대행사 관리" 묶음(일정 · 업체 · 팀·담당자 · 보고서 링크) · 업체 범위 칸
#   리뷰 검수 · 영상 제작 요청은 광고주처럼 캠페인 상단 탭에만, 포인트·사용료는 사용자 카드 [충전] · [플랜] 버튼으로
HEAD_ADV = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">'
            '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">'
            # 광고주 index.html 이 싣는 순서 그대로(loadCss 110~141행)
            + "".join(f'<link rel="stylesheet" href="css/adv/{n}.css">' for n in [
                "main", "campaignDetail", "blogIndex", "campaign-detail", "campaign-detail-panels-common", "campaign-applicants",
                "campaign-reviewers", "campaign-manage", "reviewer-manage", "campaign-create", "profile-edit", "received-messages",
                "inquiry", "faq", "postSearch", "review-inspect", "alertMessage"]))
ADV_ACTIVE = {"cal": "agc", "biz": "agc", "team": "agc", "rep": "agc",            # 하위 메뉴가 있는 묶음 → 묶음 키
              "camp": "cmp", "rvw": "cmp", "payc": "cmp", "photo": "cmp", "srch": "cmp", "insp": "cmp", "video": "cmp"}


def ms(name):
    return f'<span class="material-symbols-outlined" aria-hidden="true">{name}</span>'


def _nav(href, icon, label, on, cls="nav-item", extra=""):
    return f'<a href="{href}" class="{cls}{" active" if on else ""}"{" aria-current=page" if on else ""}>{ms(icon)}<span>{label}</span>{extra}</a>'


def sidebar(issue_total, active="dash"):
    """사이드바 — 광고주 sidebar.inc.html 마크업 그대로 + 대행사 추가분. active = 지금 화면 키"""
    grp = ADV_ACTIVE.get(active, active)
    sub = lambda k, href, icon, label: _nav(href, icon, label, active == k, "sub-nav-item")   # noqa: E731
    badge = f'<b class="nav-num add" title="대시보드 이슈 합계">{issue_total}</b>'
    # [2026-11-12] 순서 = 광고주 sidebar.inc.html 그대로(홈 · 캠페인 관리 · 마이페이지 · 대행사 신청 · 문자설정 · 문자·메일 발송내역 · 패널티 · 1:1 문의 · 자주묻는 질문 · 도움말)
    #   대행사 추가분(.add)은 맨 위 한 덩어리: 대시보드 + "대행사 관리" 묶음
    nav = (_nav("dashboard.html", "dashboard", "대시보드", active == "dash", cls="nav-item add", extra=badge)
           + '<div class="nav-item-wrap add">' + _nav("schedule.html", "apartment", "대행사 관리", grp == "agc")
           + '<div class="sub-nav">' + sub("cal", "schedule.html", "calendar_month", "일정") + sub("biz", "biz.html", "storefront", "업체")
           + sub("team", "team.html", "badge", "팀·담당자") + sub("rep", "reports.html", "description", "보고서 링크") + "</div></div>"
           + _nav("home.html", "home", "홈", active == "home")
           + '<div class="nav-item-wrap">' + _nav("campaigns.html", "campaign", "캠페인 관리", grp == "cmp")
           + '<div class="sub-nav">' + sub("camp", "campaigns.html", "list_alt", "캠페인 리스트") + sub("rvw", "reviewers.html", "group", "리뷰어 관리")
           + sub("payc", "payout.html", "paid", "포인트 지급 확인") + sub("photo", "photos.html", "insert_photo", "리뷰 사진 관리")
           + sub("srch", "search_report.html", "bar_chart", "검색결과 리포트") + "</div></div>"
           + _nav("info.html", "person", "마이페이지", active == "info") + _nav("agency_apply.html", "handshake", "대행사 신청", active == "agcy")
           + _nav("sms.html", "sms", "문자설정", active == "sms")
           + _nav("sms_box.html", "forward_to_inbox", "문자·메일 발송내역", active == "smsbox")
           + _nav("penalty.html", "gavel", "패널티", active == "pen") + _nav("inquiry.html", "support_agent", "1:1 문의", active == "qna")
           + _nav("faq.html", "quiz", "자주묻는 질문", active == "faq")
           + '<a href="help.html" class="nav-item" target="_blank" rel="noopener">' + ms("help") + '<span>도움말</span></a>')
    icons = ('<a class="icon-btn" href="#" title="검색">' + ms("search") + '</a>'
             '<a class="icon-btn" href="notifications.html" title="알림">' + ms("notifications") + '<span class="badge-dot"></span></a>'
             '<a class="icon-btn" href="notice.html" title="공지">' + ms("brand_awareness") + '</a>'
             '<a class="icon-btn" href="messages.html" title="쪽지">' + ms("mail") + '<span class="badge-dot"></span></a>')
    card = ('<div class="user-card"><div class="user-card-header"><div class="user-name-row"><span class="user-name">대표님</span>'
            '<span class="user-email">반갑습니다!</span><a href="#">로그아웃</a></div></div><div class="user-card-body">'
            '<div class="user-info-row"><span class="info-label">브론즈</span><div class="info-value-group"><span class="info-value">무료</span>'
            '<a class="btn-tag" href="plan.html">플랜</a></div></div>'
            f'<div class="user-info-row"><span class="info-label">포인트</span><div class="info-value-group"><span class="info-value">{BALANCE:,} P</span>'
            '<a class="btn-tag" href="point.html">충전</a></div></div></div></div>')
    scope = ('<div class="scope-box add ag"><p class="scope-l">업체 범위</p><button type="button" class="scope-biz" popovertarget="scope-pop">'
             f'{ms("storefront")}<b class="js-scope-name">전체 업체</b>{ms("expand_more")}</button>{scope_pop()}</div>')
    return (f'<aside class="sidebar"><div class="sidebar-inner">'
            f'<div class="sidebar-brand"><p class="brand-label">뷰마 대행사 <a class="ver add" href="versions/" title="이전 버전 보기">{VERSION} 시안</a></p>'
            f'<h1 class="brand-name">애니라인 마케팅</h1></div>'
            f'<div class="sidebar-icons">{icons}</div>'
            f'<div class="sidebar-section">{card}</div>'
            f'<div class="sidebar-section">{scope}</div>'
            f'<div class="sidebar-section"><a class="btn-new-campaign" href="campaign_new.html">{ms("add")}<span>새 캠페인 등록</span></a></div>'
            f'<nav class="sidebar-nav" aria-label="주 메뉴">{nav}</nav></div>'
            '<div class="sidebar-footer"><div class="sidebar-legal"><a href="#">이용약관</a><span class="sidebar-legal__sep"></span>'
            '<a href="#">개인정보처리방침</a></div>'
            # [2026-11-12] 광고주 sidebar.inc.html .sidebar-biz 그대로(값 = core define.inc.php BIZ_NUMBER · BIZ_CS_TEL — 회사 공개 정보)
            '<div class="sidebar-biz"><span>사업자등록번호 615-88-02870</span><span>고객센터 1833-3675</span></div>'
            '<p>ⓒ ANYRIZE All Rights Reserved.</p></div></aside>')


def scope_pop():
    """[2026-11-10 v0.8] 업체 범위 고르기 — 광고주는 계정 = 업체 하나라 없던 것.
       한 업체를 고르면 운영 화면은 광고주 사이트에서 그 업체로 본 것과 같아진다(업체·담당자 칸도 숨김 · Q18).
       고른 범위는 주소 ?biz= 로 화면을 넘어 이어진다(js/scope.js)."""
    rows = "".join(f'<li><a href="?biz={b["id"]}" data-scope="{b["id"]}" data-name="{esc(b["name"])}">{esc(b["name"])}'
                   f'<small>{b["owner"][1] if b["owner"] else "미담당"}</small></a></li>' for b in SCOPE_BIZ)
    return (f'<div id="scope-pop" class="scope-pop ag" popover><p class="sp-h">업체 범위 <small>캠페인 운영 화면에 걸립니다</small></p>'
            f'<a class="sp-all" href="?biz=" data-scope="">전체 업체 <small>{len(SCOPE_BIZ)}곳</small></a>'
            f'<label class="sp-q"><span class="sr">업체 찾기</span><input type="search" class="js-sp-q" placeholder="업체 이름"></label>'
            f'<ul>{rows}</ul></div>')


SCOPE_BIZ = []     # 업체 범위 목록 — make_biz() 결과


def topbar():
    """[2026-11-11 v0.9] 광고주 사이트에는 위 머리줄이 없다(검색·알림·쪽지는 사이드바 아이콘) — 빈 칸"""
    return ""




def shell(issue_total, active, body):
    """광고주 index.html 의 틀: .dashboard > aside.sidebar + main.main-content > .main-view"""
    return (f'<div class="dashboard">{sidebar(issue_total, active)}'
            f'<main class="main-content"><div class="main-view">{body}</div></main></div>')


def type_chips(bizs):
    """[2026-11-09] 캠페인 유형으로 거르기 — 숫자는 그 유형 캠페인의 이슈 건수"""
    cnt = {k: 0 for k in TYPE_NAME}
    for b in bizs:
        for key, it in b["issues"].items():
            if key in ("owner",):
                continue
            for c, _d in it["items"]:
                cnt[ctype(c)] += 1
    btns = "".join(f'<button type="button" class="tchip" data-type="{k}"><span class="ty ty-{k}">{v}</span><em>{cnt[k]}</em></button>'
                   for k, v in TYPE_NAME.items())
    return f'<div class="tchips" role="group" aria-label="캠페인 유형"><button type="button" class="tchip ag-on" data-type="">전체 유형</button>{btns}</div>'


def build():
    bizs = make_biz()
    total_issue = sum(v["n"] for b in bizs for v in b["issues"].values())
    with_issue = sum(1 for b in bizs if b["issues"])
    hot = sum(1 for b in bizs if b["issues"] and biz_due(b) <= 0)

    heads = "".join(f'<th scope="col" class="c"><button type="button" class="colh" data-col="{k}">{lab}</button></th>'
                    for k, lab in ISSUES)
    panels = "".join(panel(b, k) for b in bizs for k in b["issues"])
    lead_of = {tname: next((n for _s, n, ld in members if ld), "관리자") for _x, tname, members in TEAMS}
    al_shown, al_later, al_demo = alerts.make(bizs, CAMP_META, TYPE_NAME, lead_of)
    panels += alerts.pane(al_shown, al_later, al_demo)

    page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>대시보드 · 뷰마 대행사 ({VERSION} 시안)</title>
{HEAD_ADV}
<link rel="stylesheet" href="css/ag/agency.css">
<link rel="stylesheet" href="css/bridge/shell.css">
</head>
<body>
<!-- [2026-11-10] 대행사 대시보드 시안 {VERSION} — 기획서 v0.5 6-3 · 6-11. gen_dashboard.py 로 생성(직접 수정 금지)
     [2026-11-11 v0.9] 틀 = 광고주 index.html(.dashboard > .sidebar + .main-content > .main-view) -->
<div class="dashboard">
{sidebar(total_issue)}
<main class="main-content"><div class="main-view">
<div class="work ag">
<section class="board" aria-labelledby="board-title">
	<div class="board-h">
		<div>
			<h1 id="board-title">대시보드</h1>
			<p class="sub">{TODAY_LABEL} · 업체 {len(bizs)}곳 중 <b>{with_issue}곳</b>에 이슈 <b>{total_issue}건</b> · 기한 지남·오늘 <b class="hot-t">{hot}곳</b></p>
		</div>
		<div class="seg" role="group" aria-label="보기 범위">
			<button type="button">내 업체</button><button type="button">우리 팀</button><button type="button" class="ag-on">전체</button>
		</div>
	</div>

	<!-- [2026-11-10] 받은 알림 띠 — 순차 흐름(격자)과 따로, 수시 알림을 항상 같은 자리에 -->
	{alerts.bar()}

	<!-- [2026-11-09] 업체별/담당자별 전환은 라디오 + CSS (JS 없음) -->
	<input type="radio" name="view" id="v-biz" class="vr" checked>
	<input type="radio" name="view" id="v-staff" class="vr">
	<div class="toolbar">
		<div class="seg sm"><label for="v-biz">업체별</label><label for="v-staff">담당자별</label></div>
		{type_chips(bizs)}
		<button type="button" class="tchip js-afilter"><i class="adot-i" aria-hidden="true"></i>알림 있는 업체만</button>
		<p class="filter-note" hidden><span class="js-filter-name"></span> 이슈가 있는 업체만 보는 중 <button type="button" class="ag-btn link js-clear">전체 보기</button></p>
		<ul class="legend" aria-label="칸 색 뜻">
			<li><i class="is-hot"></i>기한 지남·오늘</li><li><i class="is-soon"></i>3일 내</li><li><i class="is-later"></i>그 외</li><li><i class="mix"></i>기한 섞임(칸 = 가장 급한 기한)</li>
		</ul>
	</div>

	<div class="grid-wrap">
	<table class="grid" id="grid">
		<caption class="sr">업체 × 이슈 격자. 칸을 누르면 오른쪽에서 처리합니다.</caption>
		<thead>
			<tr><th scope="col" class="bizname">업체 · 담당자</th><th scope="col" class="tot">합계</th>{heads}</tr>
			<tr class="sumrow"><th scope="row" class="bizname">전체 합계</th><td class="tot"><span class="sum" data-sum="all-total">{total_issue}</span></td>{sum_cells(bizs, "all")}</tr>
		</thead>
		{tbody_by_biz(bizs)}
		{tbody_by_staff(bizs)}
	</table>
	</div>
</section>

<aside class="panel" aria-label="이슈 처리" aria-live="polite">
	<div class="pane-empty">
		<p class="empty-ico" aria-hidden="true">☰</p>
		<p><b>격자에서 칸을 고르세요</b></p>
		<p class="muted">칸 하나 = 한 업체의 한 가지 이슈입니다.<br>여기서 바로 확인하고 처리합니다.</p>
		<button type="button" class="ag-btn primary js-next">가장 급한 이슈부터 ▶</button>
	</div>
	<div class="pane-done" hidden>
		<p class="empty-ico" aria-hidden="true">✓</p>
		<p><b>보이는 이슈를 모두 처리했습니다</b></p>
	</div>
	{panels}
</aside>
</div>
</div></main>
</div>
<div class="toasts" aria-live="assertive"></div>
<script src="js/scope.js"></script>
<script src="js/dashboard.js"></script>
</body>
</html>
'''
    OUT.write_text(page, encoding="utf-8")
    print(f"written {OUT} · 업체 {len(bizs)} · 이슈 {total_issue} · 패널 {panels.count('data-panel=')}")


if __name__ == "__main__":
    build()
