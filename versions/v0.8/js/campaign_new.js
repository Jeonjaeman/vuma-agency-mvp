/* [2026-11-10 v0.6] 캠페인 등록 · 복제 — 꼭 필요한 동작만 JS 로
   CSS 로 안 되는 것만:
   1) 업체 검색(글자) · 업체를 고르면 담당자 자동 표시(요약 · 노출 지역 · 회차)
   2) 비용 미리보기 계산(인원 × 1인당 지급 + 수수료 = 예치 예정액, 잔액과 비교 → 부족하면 버튼 바꿈)
   3) 복제: 고른 캠페인의 조건을 칸에 채움 · 같은 업체면 회차 +1, 다른 업체면 회차 1 + 안내
      주소 #copy=<캠페인 id> 로 들어오면(캠페인 페이지 [복제]) 처음부터 채움
   4) 저장·등록 버튼 → 안내 한 줄(시안이라 저장 없음)
   단계 이동 · 유형별 칸 · 보는 사람(관리자/담당자) 바꾸기는 라디오 + CSS 만으로 처리함. */
(function () {
	'use strict';

	var DATA = JSON.parse(document.getElementById('new-data').textContent);
	var TYPE = { v: '방문형', s: '배송형', p: '기자단' };
	var $ = function (s) { return document.querySelector(s); };
	var copySrc = null;           // 복제 중인 캠페인 조건

	function won(n) { return n.toLocaleString('ko-KR') + 'P'; }
	function flash(text) {
		var f = document.createElement('div');
		f.className = 'flash';
		f.setAttribute('role', 'status');
		f.textContent = text;
		document.body.appendChild(f);
		setTimeout(function () { f.remove(); }, 2400);
	}
	function setText(sel, text, muted) {
		var el = $(sel);
		if (!el) return;
		el.textContent = text;
		if (muted !== undefined) el.classList.toggle('muted', muted);
	}
	function pickedBiz() { return $('input[name=biz]:checked'); }

	// ── 2) 비용 미리보기 ─────────────────────────
	function calc() {
		var n = Math.max(0, parseInt($('.js-n').value, 10) || 0);
		var rw = Math.max(0, parseInt($('.js-reward').value, 10) || 0);
		var pay = n * rw;
		var fee = Math.round(pay * DATA.fee);
		var total = pay + fee;
		var after = DATA.bal - total;
		setText('.js-c-f', '(' + n + '명 × ' + won(rw) + ')');
		setText('.js-c-pay', won(pay));
		setText('.js-c-fee', won(fee));
		setText('.js-c-total', won(total));
		setText('.js-c-after', won(after));
		setText('.js-s-n', n + '명 × ' + won(rw));
		setText('.js-s-total', won(total));
		var short = after < 0;
		$('.cost').classList.toggle('is-short', short);
		$('.js-c-after').classList.toggle('bad', short);
		$('.js-s-total').classList.toggle('bad', short);
		$('.js-short').hidden = !short;
		if (short) setText('.js-c-gap', won(-after));
		var sub = $('.js-submit');
		sub.disabled = short;
		sub.title = short ? '잔액이 부족합니다' : '';
	}

	// ── 1) 업체 고르기 · 3) 회차 ────────────────────
	function roundMsg() {
		var b = pickedBiz();
		var msg = $('.js-copy-msg');
		if (!copySrc) { setText('.js-round', '1회차'); msg.hidden = true; return; }
		msg.hidden = false;
		if (!b || b.value === copySrc.biz) {
			setText('.js-round', (copySrc.round + 1) + '회차');
			msg.className = 'cb-msg js-copy-msg';
			msg.textContent = '같은 업체(' + copySrc.bname + ')로 복제 — ' + copySrc.round + '회차 → ' + (copySrc.round + 1) + '회차';
		} else {
			setText('.js-round', '1회차');
			msg.className = 'cb-msg warn js-copy-msg';
			msg.textContent = '다른 업체로 복제 — 1회차로 시작합니다. 주소·연락처·플레이스 링크는 새 업체(' + b.dataset.name + ') 정보로 바뀌니 확인하세요.';
		}
	}
	function onBiz() {
		var b = pickedBiz();
		if (!b) return;
		var own = b.dataset.owner;
		setText('.js-s-biz', b.dataset.name, false);
		setText('.js-s-own', own ? own + ' (' + b.dataset.team + ') — 업체 담당자' : '미담당 — 알림이 관리자에게만 갑니다', false);
		var sum = $('.js-pick-sum');
		sum.textContent = b.dataset.name + ' · 담당자 ' + (own || '없음(미담당)') + ' — 업체 담당자로 자동';
		sum.classList.add('on');
		setText('.js-reg', b.dataset.reg + ' (업체 주소)', false);
		var addr = $('.js-addr');
		if (addr) addr.value = b.dataset.reg + ' ○○로 ***';
		roundMsg();
	}
	function onType() {
		var t = $('input[name=ctype]:checked').value;
		var ch = $('input[name=chan]:checked').value;
		setText('.js-s-type', TYPE[t] + ' · ' + ch);
	}
	function onName() {
		var v = $('.js-cname').value.trim();
		setText('.js-s-name', v || '—', !v);
	}

	// ── 3) 복제 채우기 ─────────────────────────
	function check(sel) { var el = $(sel); if (el) el.checked = true; }
	function applyCopy(id) {
		copySrc = DATA.camps[id] || null;
		if (copySrc) {
			$('.js-cname').value = copySrc.name;
			$('.js-n').value = copySrc.n;
			$('.js-reward').value = copySrc.reward;
			check('input[name=ctype][value="' + copySrc.ty + '"]');
			check('input[name=chan][value="' + copySrc.ch + '"]');
			// 담당자로 보는 중이어도 남의 업체를 강제로 고르지는 않는다(내 업체가 아니면 비워 둠)
			var target = document.querySelector('input[name=biz][value="' + copySrc.biz + '"]');
			if (target && target.closest('.bpick').offsetParent !== null) target.checked = true;
		}
		onBiz(); onType(); onName(); calc(); roundMsg();
	}

	document.addEventListener('change', function (e) {
		var t = e.target;
		if (t.name === 'biz') onBiz();
		else if (t.name === 'ctype' || t.name === 'chan') onType();
		else if (t.classList.contains('js-copy')) applyCopy(t.value);
		else if (t.name === 'role') {
			// 담당자로 바꿨는데 고른 업체가 내 업체가 아니면 선택을 푼다
			var b = pickedBiz();
			if (b && b.closest('.bpick').offsetParent === null) {
				b.checked = false;
				setText('.js-s-biz', '—', true);
				setText('.js-s-own', '업체를 고르면 자동', true);
				var sum = $('.js-pick-sum');
				sum.textContent = '업체를 고르세요';
				sum.classList.remove('on');
			}
		}
	});
	document.addEventListener('input', function (e) {
		var t = e.target;
		if (t.classList.contains('js-n') || t.classList.contains('js-reward')) calc();
		else if (t.classList.contains('js-cname')) onName();
		else if (t.classList.contains('js-nsearch')) {
			var q = t.value.trim().toLowerCase();
			document.querySelectorAll('.bpick').forEach(function (c) {
				c.classList.toggle('s-out', !!q && c.dataset.name.toLowerCase().indexOf(q) < 0);
			});
		}
	});

	// ── 4) 버튼 안내 ───────────────────────────
	var MSG = {
		'js-save': '작성 중으로 저장했습니다 · 캠페인 목록 "작성 중"에서 이어서 씁니다',
		'js-charge': '시안: 포인트 충전 화면으로 이동합니다',
		'js-req': '관리자에게 충전 요청을 보냈습니다 · 충전되면 [예치하고 진행] 한 번이면 시작',
		'js-submit': '등록했습니다 · 예치 후 모집이 시작됩니다(시안 — 저장 없음)'
	};
	document.addEventListener('click', function (e) {
		var b = e.target.closest('.js-save, .js-charge, .js-req, .js-submit');
		if (!b) return;
		if (!pickedBiz()) { flash('먼저 1단계에서 업체를 고르세요'); return; }
		var k = Object.keys(MSG).filter(function (c) { return b.classList.contains(c); })[0];
		flash(MSG[k]);
	});

	var m = location.hash.match(/^#copy=([\w-]+)/);
	if (m && DATA.camps[m[1]]) { $('.js-copy').value = m[1]; applyCopy(m[1]); }
	else { onType(); calc(); }
})();
