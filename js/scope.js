/* [2026-11-10 v0.8] 업체 범위(맨 위 "전체 업체 ▾") — 모든 화면 공통
   왜 JS 인가: 고른 범위가 화면을 넘어 이어져야 하는데(주소 ?biz=), 주소 값을 읽어 거르는 일은 CSS 로 못 한다.
   하는 일은 셋뿐:
   1) 주소 ?biz=b3 → 위 버튼 글자를 업체 이름으로, <body class="one-biz"> (운영 화면의 업체·담당자 칸 숨김 · Q18)
   2) 운영 화면(.scoped)에서 data-biz 가 다른 줄(data-bizs 에 그 업체가 없는 줄) 숨김 — 스타일 한 줄을 넣어서
   3) 사이트 안 링크(.html)에 ?biz= 를 붙여 다음 화면에도 범위가 이어지게 (공개 보고서·이전 버전은 제외)
   범위 창(popover)을 여닫는 것은 HTML popover 로 처리함. */
(function () {
	'use strict';

	var biz = new URLSearchParams(location.search).get('biz') || '';
	var pick = biz && document.querySelector('.scope-pop [data-scope="' + biz + '"]');
	if (!pick) biz = '';                        // 없는 업체 번호면 전체로

	if (biz) {
		document.body.classList.add('one-biz');
		document.querySelectorAll('.js-scope-name').forEach(function (n) { n.textContent = pick.dataset.name; });
		var st = document.createElement('style');
		// data-biz = 그 업체 하나 / data-bizs = 여러 업체에 걸친 것(리뷰어 등, 공백으로 나눈 목록)
		st.textContent = '.scoped [data-biz]:not([data-biz="' + biz + '"]),.scoped [data-bizs]:not([data-bizs~="' + biz + '"]){display:none!important}';
		document.head.appendChild(st);
		pick.classList.add('ag-on');
	} else {
		var all = document.querySelector('.scope-pop .sp-all');
		if (all) all.classList.add('ag-on');
	}

	// 링크에 범위 붙이기 — 범위 창 안 링크는 이미 ?biz= 를 갖고 있으니 건너뜀
	if (biz) {
		document.querySelectorAll('a[href]').forEach(function (a) {
			var h = a.getAttribute('href');
			if (!/^[\w-]+\.html/.test(h) || /^report\.html/.test(h) || a.closest('.scope-pop')) return;
			var i = h.indexOf('#');
			var path = i < 0 ? h : h.slice(0, i), hash = i < 0 ? '' : h.slice(i);
			a.setAttribute('href', path + (path.indexOf('?') < 0 ? '?' : '&') + 'biz=' + biz + hash);
		});
	}

	// 범위 창: 지금 화면 주소(해시 포함)는 그대로 두고 biz 만 바꿔 이동
	document.querySelectorAll('.scope-pop [data-scope]').forEach(function (a) {
		var u = new URL(location.href);
		if (a.dataset.scope) u.searchParams.set('biz', a.dataset.scope); else u.searchParams.delete('biz');
		u.hash = '';                             // 다른 업체의 캠페인 페이지가 열려 있지 않게
		a.setAttribute('href', u.href);
	});

	// 범위 창 업체 찾기(글자)
	var q = document.querySelector('.js-sp-q');
	if (q) q.addEventListener('input', function () {
		var t = q.value.trim();
		document.querySelectorAll('.scope-pop li').forEach(function (li) {
			li.hidden = !!t && li.textContent.indexOf(t) < 0;
		});
	});
})();
