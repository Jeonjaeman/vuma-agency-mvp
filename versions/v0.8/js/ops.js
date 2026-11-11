/* [2026-11-10 v0.8] 운영·계정·팀 화면 공통 — 시안이라 저장하지 않는 버튼의 안내 한 줄만
   탭·거르기·창(popover)은 HTML/CSS 로 처리함. 여기서는:
   1) .js-flash 버튼 → 화면 위에 안내 글자(data-msg) 잠깐, 창 안 버튼이면 창 닫기
   2) .js-ckall 체크 → 같은 표의 줄 체크 모두 켜기/끄기 (CSS 로는 다른 체크박스 값을 못 바꿈) */
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

	document.addEventListener('click', function (e) {
		var b = e.target.closest('.js-flash');
		if (!b) return;
		flash(b.dataset.msg || '시안: 저장되지 않습니다');
		var pop = b.closest('[popover]');
		if (pop && pop.hidePopover) pop.hidePopover();
	});

	document.addEventListener('change', function (e) {
		var all = e.target.closest('.js-ckall');
		if (!all) return;
		var t = all.closest('table');
		t.querySelectorAll('tbody input[type=checkbox]').forEach(function (c) {
			if (c.closest('tr').offsetParent) c.checked = all.checked;   // 보이는 줄만
		});
	});
})();
