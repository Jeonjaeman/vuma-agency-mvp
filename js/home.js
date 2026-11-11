/* [2026-11-12 v0.9] 홈 달력 일정 띠 누르기 — 광고주 script/home/home.js renderSampleTimelines() 의 클릭 부분만
   왜 JS 인가: 한 캠페인의 띠는 주(줄)마다 따로 그려져 흩어져 있다. "누른 띠와 같은 캠페인의 다른 띠"만 부각하고
     누른 칸 옆에 팝업을 띄우는 일은 CSS 로 이을 수 없다(캠페인마다 규칙을 따로 써야 함).
   하는 일:
   1) 띠 누름 → .timeline-layer 에 is-hovering, 같은 data-event-id 띠에 is-active (광고주와 같은 class)
   2) 팝업 = <template data-pop> 을 복제해 광고주와 같은 위치 규칙으로 붙임(마크업은 생성기가 만듦 · innerHTML 안 씀)
   3) 팝업 누름 → 캠페인 화면으로(광고주는 상세 창), 바탕 누름 → 팝업 닫고 부각 해제
   달 넘기기 · 탭은 CSS(css/bridge/home.css). */
(function () {
	'use strict';

	function clear(layer) {
		layer.classList.remove('is-hovering');
		layer.querySelectorAll('.timeline-bar.is-active').forEach(function (b) { b.classList.remove('is-active'); });
	}

	function removePopup() {
		var old = document.querySelector('.timeline-layer .cal-popup');
		if (old) old.remove();
	}

	function openPopup(bar, layer) {
		var tpl = document.querySelector('template[data-pop="' + bar.dataset.cid + '"]');
		if (!tpl) return;
		var pop = tpl.content.firstElementChild.cloneNode(true);
		var top = Number(bar.dataset.top), col = Number(bar.dataset.col);
		var left = Number(bar.dataset.l), width = Number(bar.dataset.w);
		// 광고주 규칙: 띠 위 공간이 110px 보다 좁으면 아래로, 목·금·토 시작이면 오른쪽 맞춤
		if (top < 110) {
			pop.classList.add('popup-down');
			pop.style.top = (top + 26) + 'px';
		} else {
			pop.style.top = (top - 5) + 'px';
		}
		if (col >= 4) {
			pop.classList.add('popup-align-right');
			pop.style.right = 'calc(' + (100 - (left + width)) + '% + 10px)';
		} else {
			pop.style.left = 'calc(' + left + '% + 10px)';
		}
		pop.addEventListener('click', function (e) {
			e.stopPropagation();
			location.href = 'campaigns.html#c-' + bar.dataset.cid;
		});
		layer.appendChild(pop);
	}

	document.addEventListener('click', function (e) {
		var bar = e.target.closest('.timeline-bar');
		if (bar) {
			var layer = bar.closest('.timeline-layer');
			clear(layer);
			layer.classList.add('is-hovering');
			layer.querySelectorAll('.timeline-bar[data-event-id="' + bar.dataset.eventId + '"]').forEach(function (b) {
				b.classList.add('is-active');
			});
			removePopup();
			openPopup(bar, layer);
			return;
		}
		if (e.target.closest('.cal-popup')) return;
		removePopup();
		document.querySelectorAll('.timeline-layer').forEach(clear);
	});

	// 달을 바꾸면(라디오) 떠 있던 팝업 · 부각을 지움 — 광고주는 달력을 다시 그리며 지워진다
	document.addEventListener('change', function (e) {
		if (e.target.name !== 'hm-cal') return;
		removePopup();
		document.querySelectorAll('.timeline-layer').forEach(clear);
	});
})();
