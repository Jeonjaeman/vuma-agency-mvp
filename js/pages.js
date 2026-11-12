/* [2026-11-10 v0.5] 일정 · 업체 화면 — 꼭 필요한 동작만 JS 로
   CSS 로 안 되는 것만:
   1) 일정 카드(주·월) 클릭 → 오른쪽 패널에 그 캠페인
   2) 업체 이름 클릭 → 오른쪽 업체 상세 / 주소 #biz=bN 이면 그 업체를 열고 시작
   3) 업체 검색(글자 거르기) · 체크박스 선택 → 일괄 작업 바(담당자 변경·보관 — 시안이라 저장 없음)
   4) 업체 등록 <dialog> 열기
   주/월·주 이동·종류·담당자 거르기, 업체 거르기 칩, 상세 탭은 라디오 + CSS 만으로 처리함. */
(function () {
	'use strict';

	var panel = document.querySelector('.panel');
	if (!panel) return;

	function show(sel) {
		var pane = panel.querySelector(sel);
		if (!pane) return null;
		panel.querySelectorAll('.pane').forEach(function (p) { p.hidden = true; });
		pane.hidden = false;
		panel.classList.add('has-pane');
		return pane;
	}
	function flash(text) {
		var f = document.createElement('div');
		f.className = 'flash';
		f.setAttribute('role', 'status');
		f.textContent = text;
		document.body.appendChild(f);
		setTimeout(function () { f.remove(); }, 2400);
	}

	// ── 1) 일정 ──────────────────────────────
	function openCamp(btn) {
		var id = btn.dataset.cp;
		show('[data-cp="' + id + '"].pane');
		document.querySelectorAll('.ev.sel-on, .mev.sel-on').forEach(function (e) { e.classList.remove('sel-on'); });
		document.querySelectorAll('[data-cp="' + id + '"]:not(.pane)').forEach(function (e) { e.classList.add('sel-on'); });
	}

	// ── 2) 업체 상세 ─────────────────────────
	function openBiz(id) {
		if (!show('[data-bdrawer="' + id + '"]')) return;
		document.querySelectorAll('.brow.ag-open').forEach(function (r) { r.classList.remove('ag-open'); });
		var row = document.querySelector('.brow[data-biz="' + id + '"]');
		if (row) { row.classList.add('ag-open'); row.scrollIntoView({ block: 'nearest' }); }
	}
	var m = location.hash.match(/^#biz=(b\d+)/);
	if (m) openBiz(m[1]);

	// ── 3) 검색 · 선택 · 일괄 작업 ──────────────
	var bulk = document.querySelector('.bulk');
	function visibleRows() {
		return Array.prototype.filter.call(document.querySelectorAll('.brow'), function (r) { return r.offsetParent !== null; });
	}
	function selected() {
		return Array.prototype.filter.call(document.querySelectorAll('.brow'), function (r) { return r.querySelector('.js-ck').checked; });
	}
	function syncBulk() {
		if (!bulk) return;
		var sel = selected();
		document.querySelectorAll('.brow').forEach(function (r) { r.classList.toggle('is-sel', r.querySelector('.js-ck').checked); });
		bulk.hidden = sel.length === 0;
		bulk.querySelector('.js-bulk-n').textContent = sel.length + '곳 선택';
		bulk.querySelector('.js-bulk-msg').textContent = '';
		// [2026-11-12] 기본값 = 지금 담당자(요청 "담당자가 배정되어 있으면 기본값이 현재 담당자") — 고른 업체 담당이 모두 같을 때만, 섞이면 비움
		var owners = sel.map(function (r) { var s = ownSel(r.dataset.biz); return s ? s.value : ''; });
		var same = owners.length && owners.every(function (o) { return o === owners[0]; });
		bulk.querySelector('.js-bulk-own').value = same ? owners[0] : '';
	}
	var search = document.querySelector('.js-bsearch');
	if (search) search.addEventListener('input', function () {
		var q = search.value.trim();
		document.querySelectorAll('.brow').forEach(function (r) { r.classList.toggle('s-out', !!q && r.dataset.name.indexOf(q) === -1); });
		document.querySelector('.js-bempty').hidden = visibleRows().length > 0;
	});
	document.addEventListener('change', function (e) {
		if (e.target.matches('.js-ckall')) {
			// 보이는 업체만 모두 선택 (걸러진 행은 건드리지 않음)
			visibleRows().forEach(function (r) { r.querySelector('.js-ck').checked = e.target.checked; });
			syncBulk();
		} else if (e.target.matches('.js-ck')) syncBulk();
		else if (e.target.matches('input[name="bf"]')) {
			// 거르기 칩이 바뀌면 안 보이게 된 행의 선택은 푼다
			document.querySelectorAll('.brow').forEach(function (r) { if (r.offsetParent === null) r.querySelector('.js-ck').checked = false; });
			syncBulk();
		}
	});
	function setOwner(row, sid, name, team) {
		row.querySelector('.js-owner').textContent = '';
		var w = document.createElement('span');
		w.className = sid ? 'who' : 'who none';
		if (sid) { var i = document.createElement('i'); i.textContent = name.charAt(0); w.appendChild(i); }
		w.appendChild(document.createTextNode(sid ? name : '미담당'));
		row.querySelector('.js-owner').appendChild(w);
		row.querySelector('.js-team').textContent = sid ? team : '—';
		row.classList.toggle('f-un', !sid);
		// [2026-11-12] 상세의 담당자 선택값도 같이 — 다시 열었을 때 기본값 = 지금 담당자
		var ds = ownSel(row.dataset.biz);
		if (ds) ds.value = sid;
	}
	function ownSel(id) {
		var b = document.querySelector('.js-own-save[data-biz="' + id + '"]');
		return b ? b.closest('.assign').querySelector('.js-own-sel') : null;
	}
	// [2026-11-12] 미담당 자리에서 바로 배정한 결과(js/scope.js) → 목록 줄 · 상세에도 반영
	document.addEventListener('ag:owner', function (e) {
		var d = e.detail;
		var row = document.querySelector('.brow[data-biz="' + d.biz + '"]');
		if (row) setOwner(row, d.sid, d.name, d.team);
	});
	function optInfo(sel) {
		var o = sel.options[sel.selectedIndex];
		var mm = o.textContent.match(/^(.+) \((.+)\)$/);
		return { sid: sel.value, name: mm ? mm[1] : '', team: mm ? mm[2] : '' };
	}

	// ── 4) 등록 dialog ──────────────────────
	var dlg = document.getElementById('dlg-reg');

	document.addEventListener('click', function (e) {
		var t = e.target.closest('button');
		if (!t) return;
		if (t.matches('.ev, .mev')) return openCamp(t);
		if (t.matches('.js-open')) return openBiz(t.dataset.biz);
		if (t.matches('.js-bulk-clear')) { selected().forEach(function (r) { r.querySelector('.js-ck').checked = false; }); document.querySelector('.js-ckall').checked = false; return syncBulk(); }
		if (t.matches('.js-bulk-apply')) {
			var info = optInfo(bulk.querySelector('.js-bulk-own'));
			var msg = bulk.querySelector('.js-bulk-msg');
			if (!info.sid) { msg.className = 'bulk-msg js-bulk-msg'; msg.textContent = '새 담당자를 고르세요'; return; }
			var rows = selected().filter(function (r) { return !r.classList.contains('f-arch'); });
			rows.forEach(function (r) { setOwner(r, info.sid, info.name, info.team); });
			msg.className = 'bulk-msg js-bulk-msg ok';
			msg.textContent = rows.length + '곳 → ' + info.name + ' · 진행 캠페인도 함께 넘어감 · 이력 기록';
			return;
		}
		if (t.matches('.js-bulk-arch')) {
			// 진행 캠페인이 있는 업체는 보관할 수 없다(기획서 6-7)
			var sel = selected();
			var blocked = sel.filter(function (r) { return Number(r.dataset.active) > 0; });
			var msg2 = bulk.querySelector('.js-bulk-msg');
			msg2.className = 'bulk-msg js-bulk-msg' + (blocked.length ? '' : ' ok');
			msg2.textContent = blocked.length
				? '진행 캠페인이 있는 ' + blocked.length + '곳은 보관할 수 없습니다 — 먼저 완료·중단하세요'
				: sel.length + '곳 보관함으로 옮김(시안)';
			return;
		}
		if (t.matches('.js-own-save')) {
			var row = document.querySelector('.brow[data-biz="' + t.dataset.biz + '"]');
			var inf = optInfo(t.closest('.assign').querySelector('.js-own-sel'));
			if (row) setOwner(row, inf.sid, inf.name, inf.team);
			return flash('담당자 변경: ' + (inf.sid ? inf.name : '미담당') + ' · 진행 캠페인도 함께 넘어감');
		}
		if (t.matches('.js-reg') && dlg) return dlg.showModal();
		if (t.matches('.js-reg-ok')) {
			var name = dlg.querySelector('input').value.trim();
			if (!name) return;          // required 가 막아 줌
			setTimeout(function () { flash('‘' + name + '’ 등록됨(시안 — 저장 없음)'); }, 50);
		}
	});
})();
