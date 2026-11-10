/* [2026-11-10 v0.6] 캠페인 목록 · 캠페인 페이지 — 꼭 필요한 동작만 JS 로
   CSS 로 안 되는 것만:
   1) 목록 검색(글자) · 업체 · 담당자 고르기 → 줄 숨김(.s-out)
   2) 신청자 [블로그 보기] → 근거 없는 리뷰어의 [선정] 켜기 / [선정] · [보류] → 상태 글자 바꾸고 선정 수 세기
   3) 리뷰 [승인] · [수정 요청] · [반려] → 상태 글자 바꾸기
   4) 그 밖의 버튼(연장·마감·지급 확정 등) → 안내 한 줄(시안이라 저장 없음)
   캠페인 페이지 열기 · 탭 · 상태/유형 거르기 · 신청자 거르기는 주소(#c-...) · 라디오 + CSS 만으로 처리함. */
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
	function setStatus(row, cls, text) {
		var cell = row.querySelector('.js-ast');
		if (!cell) return;
		var s = document.createElement('span');
		s.className = 'st ' + cls;
		s.textContent = text;
		cell.replaceChildren(s);
	}

	// ── 1) 목록 거르기(글자 · 업체 · 담당자) ──────────────
	var q = document.querySelector('.js-csearch');
	var selBiz = document.querySelector('.js-cbiz');
	var selOwn = document.querySelector('.js-cown');
	var empty = document.querySelector('.js-cempty');
	function filterRows() {
		var t = (q.value || '').trim().toLowerCase();
		var shown = 0;
		document.querySelectorAll('.crow').forEach(function (r) {
			var out = (t && r.dataset.name.toLowerCase().indexOf(t) < 0)
				|| (selBiz.value && r.dataset.biz !== selBiz.value)
				|| (selOwn.value && r.dataset.owner !== selOwn.value);
			r.classList.toggle('s-out', !!out);
			if (r.offsetParent !== null) shown++;
		});
		if (empty) empty.hidden = shown > 0;
	}
	if (q) {
		q.addEventListener('input', filterRows);
		selBiz.addEventListener('change', filterRows);
		selOwn.addEventListener('change', filterRows);
		// 상태·유형 칩(CSS)을 바꿨을 때도 "없음" 안내를 맞춘다
		document.querySelectorAll('input[name=cf], .clist input[type=checkbox]').forEach(function (i) {
			i.addEventListener('change', filterRows);
		});
	}

	// ── 2~4) 캠페인 페이지 버튼 ─────────────────────
	document.addEventListener('click', function (e) {
		var b = e.target.closest('.js-blog, .js-pick, .js-hold, .js-rv, .js-flash');
		if (!b) return;
		var row = b.closest('tr');
		if (b.classList.contains('js-blog')) {
			e.preventDefault();
			// 근거 없는 첫 참여 리뷰어 — 블로그를 열어 봤으면 [선정]을 켠다(대시보드와 같은 규칙)
			if (row && row.classList.contains('need-check')) {
				row.classList.add('checked');
				var pick = row.querySelector('.js-pick');
				if (pick) { pick.disabled = false; pick.removeAttribute('title'); }
				var gate = row.querySelector('.gate');
				if (gate) gate.textContent = '블로그 확인함 · 선정할 수 있어요';
			}
			flash('시안: 리뷰어 블로그가 새 창으로 열립니다');
			return;
		}
		if (b.classList.contains('js-pick') || b.classList.contains('js-hold')) {
			var picked = b.classList.contains('js-pick');
			setStatus(row, picked ? 'st-blue' : 'st-orange', picked ? '선정' : '보류');
			row.className = row.className.replace(/\ba-\w+\b/, picked ? 'a-sel' : 'a-hold');
			row.querySelectorAll('.acts .btn').forEach(function (x) { x.disabled = true; });
			var cnt = row.closest('.ctp').querySelector('.js-selc');
			if (picked && cnt) cnt.textContent = String(Number(cnt.textContent) + 1);
			return;
		}
		if (b.classList.contains('js-rv')) {
			var to = b.dataset.to;
			setStatus(row, to === '승인' ? 'st-green' : to === '반려' ? 'st-red' : 'st-orange', to);
			row.querySelectorAll('.acts .btn, .acts input').forEach(function (x) { x.disabled = true; });
			return;
		}
		flash(b.dataset.msg || '시안: 저장되지 않습니다');
	});
})();
