/* [2026-11-10 v0.7] 정산 · 보고서 관리 — 꼭 필요한 동작만 JS 로
   CSS 로 안 되는 것만:
   1) 지급 묶음 [묶음 확정] → 체크된 줄은 "확정", 계좌 미확인·체크 해제 줄은 빠짐 표시(시안이라 저장 없음)
   2) 보고서 [링크 복사] → 클립보드에 주소 + 안내 / [끄기]·[켜기] → 상태 글자 바꾸기
   3) 보고서 검색(글자) · 그 밖의 버튼 안내 한 줄
   탭 · 보는 사람 · 구분/기간/상태 거르기 · 충전·만들기 창(popover)은 HTML/CSS 만으로 처리함. */
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
	function badge(cls, text) {
		var s = document.createElement('span');
		s.className = 'st ' + cls;
		s.textContent = text;
		return s;
	}
	function won(n) { return n.toLocaleString('ko-KR') + 'P'; }

	document.addEventListener('click', function (e) {
		var b = e.target.closest('.js-bconfirm, .js-copy, .js-toggle, .js-flash');
		if (!b) return;
		// 팝오버 안 버튼이면 안내 뒤 창을 닫는다
		var pop = b.closest('[popover]');

		if (b.classList.contains('js-bconfirm')) {
			var batch = b.closest('.batch');
			var n = 0, sum = 0;
			batch.querySelectorAll('.prow').forEach(function (r) {
				var ck = r.querySelector('.js-pck');
				var on = ck && ck.checked;
				r.classList.toggle('is-out', !on);
				r.querySelector('.js-pst').replaceChildren(on ? badge('st-purple', '확정') : badge('st-orange', '다음 묶음으로'));
				if (on) { n++; sum += Number(r.querySelector('.num').textContent.replace(/[^\d]/g, '')); }
				if (ck) ck.disabled = true;
			});
			batch.querySelector('.js-bst').replaceWith(badge('st-purple js-bst', '확정'));
			b.disabled = true;
			b.textContent = '확정됨 · ' + n + '명 ' + won(sum);
			flash('묶음을 확정했습니다 — 뷰마가 송금하면 "송금 중 → 입금 완료"로 바뀝니다');
			return;
		}
		if (b.classList.contains('js-copy')) {
			var url = b.dataset.url;
			if (navigator.clipboard) navigator.clipboard.writeText(url).catch(function () { /* 파일로 열면 막힐 수 있음 — 안내만 */ });
			flash('링크를 복사했습니다 — 업체 고객에게 붙여 넣어 보내세요');
			return;
		}
		if (b.classList.contains('js-toggle')) {
			var row = b.closest('tr');
			var on2 = b.dataset.to === 'on';
			row.querySelector('.js-rst').replaceChildren(on2 ? badge('st-green', '켜짐') : badge('st-gray', '꺼짐'));
			row.className = row.className.replace(/\br-\w+\b/, on2 ? 'r-on' : 'r-off');
			b.dataset.to = on2 ? 'off' : 'on';
			b.textContent = on2 ? '끄기' : '켜기';
			flash(on2 ? '다시 켰습니다 — 만료 30일 뒤' : '껐습니다 — 링크를 열면 "볼 수 없는 보고서" 안내가 나옵니다');
			return;
		}
		flash(b.dataset.msg || '시안: 저장되지 않습니다');
		if (pop && pop.hidePopover) pop.hidePopover();
	});

	var q = document.querySelector('.js-rsearch');
	if (q) q.addEventListener('input', function () {
		var t = q.value.trim().toLowerCase();
		document.querySelectorAll('.rrow').forEach(function (r) {
			r.classList.toggle('s-out', !!t && r.dataset.name.toLowerCase().indexOf(t) < 0);
		});
	});
})();
