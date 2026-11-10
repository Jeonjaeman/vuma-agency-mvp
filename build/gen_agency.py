# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.8] 대행사 층 — 팀·담당자 화면 (광고주 사이트에 없는 화면)
  탭: 직원 · 팀 · 역할과 권한(기획서 8-3). 직원 초대 · 역할 변경 · 중지·인수인계 = popover.
  숫자(담당 업체 · 진행 캠페인 · 이슈)는 대시보드와 같은 데이터.
  실행: python -I build/gen_agency.py  →  mvp/team.html
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camp_data as D  # noqa: E402
import ops_kit as K  # noqa: E402

P, G = D.P, D.G
esc = K.esc

ROLE = {"admin": ("관리자", "st-purple"), "lead": ("팀장", "st-blue"), "staff": ("담당자", "st-gray"), "view": ("조회", "st-gray")}


def staff_rows():
    """대표(관리자) + 팀 직원 6명 + 조회 전용 1명(회계)"""
    r = random.Random("team")
    out = [{"sid": "ceo", "name": "대표", "role": "admin", "team": "—", "mail": "ceo@anyline.kr", "last": "지금", "on": True}]
    for sid, name, lead, tname in G.STAFF:
        out.append({"sid": sid, "name": name, "role": "lead" if lead else "staff", "team": tname,
                    "mail": f"{sid}@anyline.kr", "last": r.choice(["지금", "10분 전", "1시간 전", "어제"]), "on": True})
    out.append({"sid": "acc", "name": "오세린", "role": "view", "team": "—", "mail": "acc@anyline.kr", "last": "3일 전", "on": True})
    out.append({"sid": "old", "name": "윤재희", "role": "staff", "team": "1팀", "mail": "old@anyline.kr", "last": "10/21", "on": False})
    return out


def load(sid):
    bz = [b for b in P.BIZS if b["owner"] and b["owner"][0] == sid]
    camps = [c for c in D.CAMPS if c["b"] in bz and c["group"] in D.ACTIVE]
    iss = sum(v["n"] for b in bz for v in b["issues"].values())
    hot = sum(1 for b in bz for v in b["issues"].values() if v["due"] <= 0)
    return bz, camps, iss, hot


def tab_staff(rows):
    heads = [("이름", ""), ("역할", ""), ("팀", ""), ("담당 업체", "num"), ("진행 캠페인", "num"), ("이슈", "num"),
             ("기한 지남·오늘", "num"), ("마지막 접속", ""), ("상태", ""), ("", "")]
    trs = []
    for s in rows:
        bz, camps, iss, hot = load(s["sid"])
        role, rc = ROLE[s["role"]]
        acts = (K.btn("업체 배정", pop="pop-assign") + K.btn("역할", pop="pop-role")
                + (K.btn("중지·인수인계", pop="pop-stop") if s["sid"] != "ceo" and s["on"] else ""))
        if not s["on"]:
            acts = K.btn("다시 사용", "시안: 다시 사용하게 했습니다")
        trs.append((f'class="{"" if s["on"] else "muted"}"', [
            f'<span class="who"><i>{s["name"][0]}</i>{s["name"]}</span><br><small>{s["mail"]}</small>',
            K.badge(rc, role), s["team"],
            f'<a href="biz.html">{len(bz)}</a>' if bz else "—", len(camps) or "—", iss or "—",
            f'<b class="bad">{hot}</b>' if hot else "—", s["last"],
            K.badge("st-green", "사용 중") if s["on"] else K.badge("st-gray", "중지"),
            f'<div class="acts">{acts}</div>']))
    un = [b for b in P.BIZS if not b["owner"]]
    note = (f'<p class="help">미담당 업체 {len(un)}곳({", ".join(esc(b["name"]) for b in un)}) — '
            f'<a href="dashboard.html">대시보드 미담당 칸</a>에서 바로 배정할 수 있습니다.</p>')
    return K.fbar(K.select("역할", ["역할 전체", "관리자", "팀장", "담당자", "조회"]), K.select("팀", ["팀 전체", "1팀", "2팀", "팀 없음"]),
                  K.search("이름·이메일"), count=f"직원 <b>{len(rows)}</b>명") + K.table(heads, trs) + note


def tab_teams(rows):
    cards = []
    for _x, tname, members in G.TEAMS:
        bz = [b for b in P.BIZS if b["owner"] and b["owner"][3] == tname]
        iss = sum(v["n"] for b in bz for v in b["issues"].values())
        lead = next((n for _s, n, ld in members if ld), "없음")
        mem = " ".join(f'<span class="chip">{n}</span>' for _s, n, _l in members)
        cards.append(f'<div class="card"><h3>{tname}</h3><p>팀장 <b>{lead}</b></p><p>{mem}</p>'
                     f'<p class="muted">업체 {len(bz)}곳 · 이슈 {iss}건</p>'
                     f'<p style="margin-top:10px"><a class="btn sm" href="dashboard.html">대시보드에서 이 팀 보기</a> '
                     f'{K.btn("팀 이름·팀원", pop="pop-team")}</p></div>')
    cards.append(f'<div class="card"><h3>+ 새 팀</h3><p class="muted">팀장 1명 + 팀원. 팀장은 자기 팀 업체를 모두 볼 수 있습니다.</p>'
                 f'<p style="margin-top:10px">{K.btn("팀 만들기", pop="pop-team", cls="btn sm primary")}</p></div>')
    return f'<div class="cards">{"".join(cards)}</div>'


# 역할 × 할 수 있는 일(기획서 8-3) — y 가능 · n 불가 · 글자 = 범위 제한
PERM = [
    ("대시보드 · 일정 보기", "전체", "우리 팀", "내 업체", "전체"),
    ("업체 등록 · 보관", "y", "y", "n", "n"),
    ("업체 담당자 배정 · 변경", "y", "우리 팀", "n", "n"),
    ("캠페인 등록 · 복제", "y", "y", "내 업체", "n"),
    ("신청자 선정 · 리뷰 검수", "y", "y", "내 업체", "n"),
    ("포인트 지급 확인 · 묶음 확정", "y", "y", "확인만", "n"),
    ("통포인트 충전 · 환불", "y", "요청만", "요청만", "n"),
    ("사용내역 · 결제·거래내역 보기", "y", "y", "n", "y"),
    ("보고서 링크 만들기 · 끄기", "y", "y", "내 업체", "n"),
    ("문자설정 · 패널티 · 대행사 정보", "y", "보기", "n", "보기"),
    ("팀·직원 관리", "y", "n", "n", "n"),
]


def tab_perm():
    def cell(v):
        if v == "y":
            return '<td class="y">●</td>'
        if v == "n":
            return '<td class="n">—</td>'
        return f'<td class="p">{v}</td>'
    trs = "".join(f'<tr><th scope="row">{name}</th>{"".join(cell(v) for v in vals)}</tr>' for name, *vals in PERM)
    return (f'<div class="owrap"><table class="otable perm"><thead><tr><th>할 수 있는 일</th><th>관리자</th><th>팀장</th>'
            f'<th>담당자</th><th>조회</th></tr></thead><tbody>{trs}</tbody></table></div>'
            '<p class="help">업체 범위(맨 위 "전체 업체 ▾")도 역할을 따릅니다 — 담당자는 내 업체까지만 고를 수 있습니다.</p>')


def pops(rows):
    staff_opts = "".join(f"<option>{s['name']}</option>" for s in rows if s["on"] and s["sid"] != "ceo")
    biz_ck = "".join(f'<label><input type="checkbox"{" checked" if i < 3 else ""}> {esc(b["name"])}</label>'
                     for i, b in enumerate(P.BIZS[:10]))
    roles = "".join(f'<label><input type="radio" name="rl"{" checked" if k == "staff" else ""}> {v[0]}</label>' for k, v in ROLE.items())
    return (K.pop("pop-invite", "직원 초대",
                  '<label class="fl">이름<input type="text" placeholder="예: 김하린"></label>'
                  '<label class="fl">이메일 <small>초대 메일로 가입 링크를 보냅니다(비밀번호는 본인이 정함)</small><input type="email" placeholder="name@회사.kr"></label>'
                  f'<div class="fl">역할<div class="radios">{roles}</div></div>'
                  '<label class="fl">팀<select><option>1팀</option><option>2팀</option><option>팀 없음</option></select></label>',
                  "초대 보내기", "시안: 초대 메일을 보냈습니다")
            + K.pop("pop-role", "역할 바꾸기", f'<div class="fl">역할<div class="radios">{roles}</div></div>'
                    '<p class="help">팀장 → 담당자로 바꾸면 팀 전체 보기가 사라집니다.</p>', "바꾸기")
            + K.pop("pop-assign", "담당 업체 배정", f'<div class="fl">업체(일부)<div class="radios">{biz_ck}</div></div>'
                    '<p class="help">업체마다 담당자는 1명. 이미 다른 사람 업체를 고르면 담당이 넘어갑니다.</p>', "배정")
            + K.pop("pop-stop", "중지 · 인수인계",
                    '<p>중지하면 로그인할 수 없고, 담당 업체·진행 캠페인·처리 중 이슈를 다른 사람에게 넘깁니다.</p>'
                    f'<label class="fl">넘겨받을 사람<select>{staff_opts}</select></label>'
                    '<div class="fl">넘길 것<div class="radios"><label><input type="checkbox" checked> 담당 업체</label>'
                    '<label><input type="checkbox" checked> 진행 캠페인 담당</label><label><input type="checkbox" checked> 채팅·쪽지 배정</label></div></div>',
                    "중지하고 넘기기", "시안: 중지하고 인수인계했습니다")
            + K.pop("pop-team", "팀", '<label class="fl">팀 이름<input type="text" value="1팀"></label>'
                    f'<label class="fl">팀장<select>{staff_opts}</select></label>'))


def build():
    rows = staff_rows()
    on = [s for s in rows if s["on"]]
    kpis = (f'<div class="kpis"><div class="kpi"><p>직원</p><b>{len(on)}명</b><small>중지 {len(rows) - len(on)}명</small></div>'
            f'<div class="kpi"><p>팀</p><b>{len(G.TEAMS) - 1}개</b><small>팀 없는 담당자 1명</small></div>'
            f'<div class="kpi"><p>미담당 업체</p><b class="bad">{sum(1 for b in P.BIZS if not b["owner"])}곳</b><small>담당자 배정 필요</small></div>'
            f'<div class="kpi main"><p>로그인 계정</p><b>직원마다 1개</b><small>정보·지갑·패널티는 대행사 하나</small></div></div>')
    body = (K.head("팀·담당자", "직원 · 팀 · 역할 — 업체마다 담당자 1명, 담당자 = 알림 받는 사람(8-5)",
                   K.btn("+ 직원 초대", pop="pop-invite", cls="btn primary"), legend=False)
            + kpis + K.tabs("tm", [("직원", tab_staff(rows)), ("팀", tab_teams(rows)), ("역할과 권한", tab_perm())]) + pops(rows))
    K.write("team.html", "팀·담당자", "team", body)


if __name__ == "__main__":
    build()
