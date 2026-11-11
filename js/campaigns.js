/* [2026-11-10 v0.8] 캠페인 리스트 · 캠페인 상세 — 꼭 필요한 동작만 JS 로
   [2026-11-11 v0.9] 마크업이 광고주 것(.cmp-card · .applicants-table · .rv-table)으로 바뀌어 고르는 class 만 맞춤
   CSS 로 안 되는 것만:
   1) 리스트 검색(글자) · 담당자 고르기 → 카드 숨김(.s-out) — 업체는 맨 위 "업체 범위"(js/scope.js)
   2) 신청자 [블로그 보기] → 근거 없는 리뷰어의 [선정] 켜기 / [선정] → "선정대기"로 바꾸고 선정대기 수 세기 / [해제] → 되돌림
   3) 선정된 리뷰어 [전체선택] → 줄 체크 모두 켜기/끄기 · "N명 선택됨" 세기 (체크 상자가 표 밖이라 ops.js .js-ckall 을 못 씀)
   4) 그 밖의 버튼 안내 한 줄은 js/ops.js 가 같이 처리(시안이라 저장 없음)
   상세 열기 · 탭 · 상태 탭 · 채널/유형 · 정렬 · 보기 방식은 주소(#c-...) · 라디오/체크박스/select + CSS 만으로 처리함. */
(function () {
	'use strict';

	function flash(text) {
		var f = document.createElement('div');
		f.className = 'flash';
		f.setAttribute('role', 'status');
		f.textContent = text;
		document.body.appendChild(f);
		setTimeout(function () { f.remove(); }, 2400);
	}
	function el(tag, cls, text) {
		var x = document.createElement(tag);
		x.className = cls;
		x.textContent = text;
		if (tag === 'button') x.type = 'button';
		return x;
	}
	// 광고주 .applicants-action-wait 조각(아이콘 + 글)
	function waitBadge() {
		var d = el('div', 'applicants-action-wait', '');
		var i = el('span', 'material-symbols-outlined', 'schedule');
		i.setAttribute('aria-hidden', 'true');
		d.append(i, el('span', '', '선정대기'));
		return d;
	}

	// ── 1) 리스트 거르기(글자 · 담당자) ──────────────
	var q = document.querySelector('.js-csearch');
	var selOwn = document.querySelector('.js-cown');
	var empty = document.querySelector('.js-cempty');
	function filterCards() {
		var t = (q.value || '').trim().toLowerCase();
		var shown = 0;
		document.querySelectorAll('.cmp-card').forEach(function (r) {
			var out = (t && r.dataset.name.toLowerCase().indexOf(t) < 0) || (selOwn.value && r.dataset.owner !== selOwn.value);
			r.classList.toggle('s-out', !!out);
			if (r.offsetParent !== null) shown++;
		});
		if (empty) empty.hidden = shown > 0;
	}
	if (q && selOwn) {
		q.addEventListener('input', filterCards);
		selOwn.addEventListener('change', filterCards);
		// 상태 탭·채널·유형(CSS)을 바꿨을 때도 "없음" 안내를 맞춘다
		document.querySelectorAll('.camp-page > input, .clist input, .dropdown-panel input').forEach(function (i) {
			i.addEventListener('change', filterCards);
		});
	}

	// 선정대기 수 — 같은 신청자 탭 안 숫자(요약 줄 · 확정 띠) 모두, 0 이면 확정 띠 숨김(광고주는 $waitCnt > 0 일 때만 그림)
	function bump(row, d) {
		var pane = row.closest('.detail-panel');
		var n = 0;
		pane.querySelectorAll('.js-wait').forEach(function (x) { n = Number(x.textContent) + d; x.textContent = String(n); });
		var bar = pane.querySelector('.js-cbar');
		if (bar) bar.hidden = n <= 0;
	}

	// ── 2) 신청자 선정 ─────────────────────
	document.addEventListener('click', function (e) {
		var b = e.target.closest('.js-blog, .js-pick, .js-unpick');
		if (!b) return;
		var row = b.closest('tr');
		if (b.classList.contains('js-blog')) {
			e.preventDefault();
			// 근거 없는 첫 참여 리뷰어 — 블로그를 열어 봤으면 [선정]을 켠다(대행사 규칙)
			var pick = row && row.querySelector('.js-pick');
			if (pick) { pick.disabled = false; pick.removeAttribute('title'); }
			flash('시안: 리뷰어 블로그가 새 창으로 열립니다');
			return;
		}
		var cell = row.querySelector('.js-ast');
		if (b.classList.contains('js-pick')) {
			cell.replaceChildren(waitBadge(), el('button', 'btn-applicant-cancel js-unpick', '해제'));
			row.classList.add('applicants-row-waiting');
			bump(row, 1);
			return;
		}
		cell.replaceChildren(el('button', 'btn-applicant-select js-pick', '선정'));
		row.classList.remove('applicants-row-waiting');
		bump(row, -1);
	});

	// ── 3) 선정된 리뷰어 전체선택 · 선택 수 ─────────────────────
	document.addEventListener('change', function (e) {
		var c = e.target.closest('.rv-check-all, .rv-check');
		if (!c) return;
		var pane = c.closest('.detail-panel');
		if (c.classList.contains('rv-check-all')) {
			pane.querySelectorAll('.rv-check').forEach(function (x) { x.checked = c.checked; });
		}
		var n = pane.querySelectorAll('.rv-check:checked').length;
		pane.querySelector('.rv-bulk-num').textContent = String(n);
	});
})();
