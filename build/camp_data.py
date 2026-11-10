# -*- coding: utf-8 -*-
"""
[2026-11-10 v0.6] 캠페인 화면 공통 더미 데이터 (기획서 v0.6 4장 · 6-4 · 6-5)
  진행 캠페인 = 대시보드와 같은 업체·캠페인(gen_pages.BIZS) — 상태·일정·이슈 숫자가 대시보드·일정 화면과 맞는다.
  여기에 업체마다 지난 캠페인(완료·중단)과 작성 중 캠페인을 덧붙인다(대시보드에는 안 나오는 상태).
  캠페인 하나 = dict. 난수는 캠페인마다 따로(Random(시드)) — 다른 화면 더미가 바뀌지 않게.
"""
import random

import gen_pages as P

G = P.G

# 상태 9종(기획서 4장) → 배지 색(디자인 기준안 8-4 6종)
STATE_CLS = {"작성 중": "st-gray", "승인 대기": "st-gray", "모집 중": "st-purple", "선정 중": "st-blue",
             "체험 중": "st-orange", "배송·체험 중": "st-orange", "원고 작성 중": "st-orange", "리뷰 중": "st-orange",
             "정산 중": "st-green", "완료": "st-green", "중단": "st-red"}
# 목록 거르기 묶음(체험 단계는 유형마다 이름이 달라 하나로 묶는다)
STATE_GROUP = {"모집 중": "rec", "선정 중": "sel", "체험 중": "exp", "배송·체험 중": "exp", "원고 작성 중": "exp",
               "리뷰 중": "rev", "정산 중": "pay", "작성 중": "draft", "승인 대기": "draft", "완료": "end", "중단": "end"}
ACTIVE = ("rec", "sel", "exp", "rev", "pay")
FEE = 0.10                    # 플랫폼 수수료(예시 — 대행사 등급·개별 요율)
BALANCE = G.BALANCE           # 사용 가능 잔액(사이드바와 같은 값)
REWARDS = [5000, 10000, 15000, 30000]
MEMOS = ["주말 방문 가능해요", "아이와 함께 방문 예정", "사진 위주로 작성합니다", "평일 저녁 방문", "영상도 같이 올릴게요",
         "단골 손님이에요", "근처 직장인입니다", "꼼꼼하게 쓰겠습니다"]
SHOW_APPS = 6                 # 신청자 탭에 미리 그려 두는 줄 수(시안 — 실제는 페이지 넘김)
STAFF_NAMES = {sid: name for sid, name, _l, _t in G.STAFF}


def _date_state(dts):
    """이슈가 안 걸린 진행 캠페인 — 일정으로 지금 단계를 정한다"""
    if dts["rec"] >= 0:
        return "모집 중"
    if dts["sel"] >= 0:
        return "선정 중"
    if dts["exp"] >= -3:
        return None            # 체험 단계(유형별 이름)
    return "리뷰 중"


def state_of(b, camp, dts):
    st = G.camp_state(b, camp)
    # 마감 지남 = 상태가 아니라 이슈(8-1) — 모집 마감이 지났는데 선정으로 안 넘어간 캠페인만.
    #   다른 단계 이슈가 먼저 잡힌 캠페인은 이미 다음 단계라 배지를 붙이지 않는다(상태와 어긋나 보임)
    late = st == "기한 지남"
    if late:
        st = "모집 중"
    if st == "진행 중":
        st = _date_state(dts) or G.PREP_STATE[G.ctype(camp)]
    return st, late


def evidence(r):
    """선정 근거(대시보드 make_evidence 와 같은 꼴) — 이 캠페인 난수로"""
    bi = None
    if r.random() < 0.75:
        score = round(r.uniform(2.0, 9.6), 1)
        grade = "최적화" if score >= 7 else "준최적화" if score >= 5 else "일반"
        bi = {"score": score, "grade": grade, "visit": r.choice([40, 120, 380, 860, 1500, 3200]),
              "post30": r.randint(0, 28), "neighbor": r.choice([120, 480, 1300, 2600, 5400])}
    part = r.choice([0, 0, 1, 3, 6, 12, 24])
    hist = None
    if part:
        hist = {"part": part, "ontime": r.choice([100, 96, 90, 83, 70]), "pass": r.choice([100, 95, 88, 75]),
                "rating": round(r.uniform(3.4, 5.0), 1), "ours": r.choice([0, 0, 1, 2]), "penalty": r.random() < 0.12}
    return bi, hist


def _iss(b, camp):
    """이 캠페인에 걸린 이슈 {key: (건수, 가장 이른 기한)}"""
    out = {}
    for k, it in b["issues"].items():
        ds = [d for c, d in it["items"] if c == camp]
        if ds:
            out[k] = (len(ds), min(ds))
    return out


def _people(r, c):
    """신청자·리뷰·지급 줄 — 상태와 이슈 숫자에 맞춘다"""
    g, n, iss = STATE_GROUP[c["state"]], c["n"], c["iss"]
    nicks = r.sample(G.REVIEWERS, len(G.REVIEWERS))
    if g == "draft":
        return [], [], []
    applied = (iss.get("apply", (0,))[0] + r.randint(1, n)) if g == "rec" else n + r.randint(1, n * 2)
    sel = 0 if g == "rec" else r.randint(max(0, n - 3), n - 1) if g == "sel" else n
    rows = []
    for i in range(min(applied, SHOW_APPS)):
        bi, hist = evidence(r)
        st = "sel" if i < sel else ("wait" if g in ("rec", "sel") else "no")
        if g == "rec" and i < iss.get("apply", (0,))[0]:
            st = "new"
        rows.append({"nick": nicks[i % len(nicks)] + ("" if i < len(nicks) else str(i)), "bi": bi, "hist": hist,
                     "memo": r.choice(MEMOS), "st": st, "ago": r.randint(0, 6)})
    if g in ("exp", "rev") and r.random() < .3 and rows:
        rows[-1]["st"] = "cancel"         # 기존 취소 요청(cancelReq)
    c["applied"], c["sel"] = applied, sel
    revs, pays = [], []
    if g in ("rev", "pay", "end") and c["state"] != "중단":
        pend = iss.get("review", (0,))[0]
        unreg = iss.get("nudge", (0,))[0]
        for i in range(n):
            st = "pend" if i < pend else "unreg" if i < pend + unreg else "ok"
            if g == "rev" and st == "ok" and r.random() < .15:
                st = "fix"
            revs.append({"nick": nicks[i], "ch": c["ch"], "st": st, "ago": r.randint(1, 5)})
        payn = iss.get("pay", (0,))[0]
        for i, rv in enumerate(x for x in revs if x["st"] == "ok"):
            st = "done" if g == "end" else ("wait" if i < max(payn, 1 if g == "pay" else 0) else "done")
            if st == "wait" and r.random() < .12:
                st = "noacc"                   # 계좌 미등록
            pays.append({"nick": rv["nick"], "amt": c["reward"], "st": st})
    return rows, revs, pays


def _make(b, name, cid, r, state=None, late=False, dts=None, rnd_no=None):
    ty, ch = G.CAMP_META[name]
    n = r.choice([3, 5, 5, 8, 10])
    reward = r.choice(REWARDS)
    c = {"id": cid, "b": b, "bid": b["id"], "name": name, "ty": ty, "ch": ch, "round": rnd_no or r.randint(1, 4),
         "n": n, "reward": reward, "dts": dts, "state": state, "late": late, "iss": {}, "watch": "", "past": False}
    return c


def _finish(c, r):
    c["group"] = STATE_GROUP[c["state"]]
    c["deposit"] = int(c["n"] * c["reward"] * (1 + FEE))
    c["rows"], c["revs"], c["pays"] = _people(r, c)
    if "applied" not in c:
        c["applied"], c["sel"] = 0, 0
    owner = c["b"]["owner"]
    if owner and c["group"] in ACTIVE and r.random() < .22:
        # "OOO님이 보고 있습니다"(6-4 동시 처리 — MVP 는 표시만): 같은 팀 다른 사람
        mates = [s for s in G.STAFF if s[3] == owner[3] and s[0] != owner[0]] or [G.STAFF[0]]
        c["watch"] = r.choice(mates)[1]
    return c


def build():
    out = []
    for b in P.BIZS:
        for name in b["camps"]:
            cid = P.cp_id(b, name)
            r = random.Random(f"camp-{cid}")
            dts = P.camp_dates(b, name)
            st, late = state_of(b, name, dts)
            c = _make(b, name, cid, r, st, late, dts)
            c["iss"] = _iss(b, name)
            out.append(_finish(c, r))
        # 지난 캠페인(완료·중단)과 작성 중 — 업체마다 0~2개
        r = random.Random(f"past-{b['id']}")
        for k in range(r.choice([0, 1, 1, 2])):
            name = r.choice(G.CAMPAIGNS)
            st = "중단" if r.random() < .15 else "완료"
            base = -r.randint(20, 70)
            c = _make(b, name, f'{b["id"]}-x{k}', r, st, False,
                      {"rec": base, "sel": base + 2, "exp": base + 4, "rev": base + 14}, rnd_no=1)
            c["past"] = True
            out.append(_finish(c, r))
        if r.random() < .25:
            name = r.choice(G.CAMPAIGNS)
            c = _make(b, name, f'{b["id"]}-d0', r, "작성 중", False, None)
            out.append(_finish(c, r))
    return out


CAMPS = build()
BY_ID = {c["id"]: c for c in CAMPS}


def next_due(c):
    """다음 일정(종류 · 일수) — 지난 캠페인·작성 중은 없음"""
    if not c["dts"] or c["group"] in ("end", "draft"):
        return None
    fut = [(off, k) for k, off in c["dts"].items() if off >= 0]
    if c["late"]:
        return ("rec", c["dts"]["rec"])
    if not fut:
        return None
    off, k = min(fut)
    return (k, off)
