# -*- coding: utf-8 -*-
"""
[2026-11-12 v0.9] 광고주 CSS ↔ 대행사 CSS 분리 검사 — 겹치면 이유를 찍고 1 로 끝난다
  css/adv/     광고주 원본(실서버에서 읽기만 해서 복사 · 고치지 않음)
  css/bridge/  광고주 화면을 시안에서 돌리는 이음(광고주 JS 대신 라디오·:has()·popover) + 광고주 셸에 대행사 것 붙이기
  css/ag/      대행사 전용
검사
  1) 대행사 CSS 의 class 이름이 광고주 CSS 에 없을 것(이름이 같으면 서로의 화면에 규칙이 먹는다)
  2) 대행사 CSS 선택자에 광고주 class 가 없을 것(대행사 규칙이 광고주 화면을 바꾸지 않게 — 그런 규칙은 css/bridge 로)
  3) 대행사 CSS 에 태그 전체 규칙 없을 것(button · svg …) — 대행사 영역 :where(.ag) 안쪽만 허용
  4) 대행사 CSS 가 정하는 변수는 --ag- 로 시작 · 광고주 변수 이름과 안 겹칠 것
  5) 이음 CSS 에도 태그 전체 규칙 없을 것 · 대행사 변수(--ag-)를 새로 정하지 않을 것
  공개 보고서(report.css)는 광고주 CSS 를 싣지 않는 따로 된 화면이라 3) 만 빼 준다
실행: python -I build/check_css.py
"""
import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parent.parent / "css"
STANDALONE = {"report.css"}          # 광고주 CSS 를 싣지 않는 화면


def strip_comments(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def selectors(text):
    """가장 안쪽 { } 앞 선택자들(@media 안쪽 포함) — (선택자, 본문)"""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", strip_comments(text)):
        sel = m.group(1).strip()
        if sel.startswith("@") or re.fullmatch(r"(from|to|[\d.]+%)(\s*,\s*(from|to|[\d.]+%))*", sel):
            continue
        for s in split_top(sel):
            yield s.strip(), m.group(2)


def split_top(sel):
    """쉼표로 나누되 :is( ) · :where( ) 괄호 안 쉼표는 그대로"""
    out, depth, cur = [], 0, ""
    for ch in sel:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    return out + [cur]


def classes(sel):
    return set(re.findall(r"\.([A-Za-z_][\w-]*)", sel))


def is_tag_rule(sel):
    """class · id · 속성 없이 태그(또는 * · ::스크롤바 · html/body)만으로 거는 규칙. :where(.ag) 로 시작하면 대행사 영역이라 허용"""
    s = sel.strip()
    if s.startswith(":where(.ag)") or s == ":root":
        return False
    return not re.search(r"[.#\[]", s)                 # 선택자 어디에도 class · id · 속성이 없으면 화면 전체에 먹는다


def declared_vars(text):
    return set(re.findall(r"(?<![\w-])(--[A-Za-z][\w-]*)\s*:", strip_comments(text)))


def main():
    adv_cls, adv_var = set(), set()
    for p in (CSS / "adv").glob("*.css"):
        t = p.read_text(encoding="utf-8")
        adv_var |= declared_vars(t)
        for s, _b in selectors(t):
            adv_cls |= classes(s)
    errs = []
    for p in sorted((CSS / "ag").glob("*.css")):
        t = p.read_text(encoding="utf-8")
        for s, _b in selectors(t):
            if s == ":root":
                continue
            hit = classes(s) & adv_cls
            if hit:
                errs.append(f"ag/{p.name}: 광고주 class 를 씀 {sorted(hit)} ← {s}")
            if p.name not in STANDALONE and is_tag_rule(s):
                errs.append(f"ag/{p.name}: 태그 전체 규칙 ← {s}")
        for v in sorted(declared_vars(t)):
            if not v.startswith("--ag-"):
                errs.append(f"ag/{p.name}: 변수 이름이 --ag- 아님 {v}")
            if v in adv_var:
                errs.append(f"ag/{p.name}: 광고주 변수와 같은 이름 {v}")
    for p in sorted((CSS / "bridge").glob("*.css")):
        t = p.read_text(encoding="utf-8")
        for s, _b in selectors(t):
            if is_tag_rule(s):
                errs.append(f"bridge/{p.name}: 태그 전체 규칙 ← {s}")
        for v in sorted(declared_vars(t)):
            if v.startswith("--ag-"):
                errs.append(f"bridge/{p.name}: 대행사 변수를 새로 정함 {v}")
    for e in errs:
        print(e)
    print(f"css 분리 검사: 문제 {len(errs)}건")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
