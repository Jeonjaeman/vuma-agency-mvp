/* [2026-11-09] 대행사 대시보드 시안 — 꼭 필요한 동작만 JS 로
   CSS 로 안 되는 것만 여기서 한다:
   1) 격자 칸/업체명/패널 칩 클릭 → 오른쪽 처리 패널 바꾸기
   2) 열 머리 클릭 → table[data-filter] 값만 바꿈 (숨김·표시는 CSS)
   3) 처리 버튼 → 카드에 "처리됨" 표시, 칸·합계 다시 세기 (시안이라 저장 없음)
      칸 하나에 기한·유형이 다른 건이 섞여 있다(data-dues · data-types, 같은 순서).
      처리한 건을 빼고 칸 글자·색 = 남은 건 중 가장 급한 기한, 업체 행도 맞는 묶음으로 옮긴다.
   4) [다음 ▶] → 보이는 격자 순서대로 다음 칸 열기 (처리를 다 해도 자동으로 넘어가지 않음 — 사람이 누를 때만)
   5) 유형 칩(방문형·배송형·기자단) → 칸 숫자를 그 유형 건만으로 다시 그림
   6) 선정 근거 — 근거 없는 신청자는 블로그 확인 후 [선정]
   7) 추가모집 비용 미리보기
   9) [v0.4] 수시 알림 — 받은 알림 띠·알림 패널·업체 알림 점·토스트·[처리]/[나중에] (읽기만으로는 안 사라짐)
   8) 캠페인 줄(업체 행 아래) — 숫자는 업체 칸의 건 목록에서 그 캠페인 건만 세어 그린다
   업체별/담당자별 전환, 이슈 없음 펼치기, 빈 묶음 숨김, 추가모집 상자 열기는 CSS·HTML 만으로 처리함. */
(function () {
	'use strict';

	var grid = document.getElementById('grid');
	var panel = document.querySelector('.panel');
	var filterNote = document.querySelector('.filter-note');
	var ISSUE_NAME = { apply: '신청 확인', select: '선정 임박', prep: '체험 준비', review: '검수', nudge: '리뷰 독촉', pay: '지급', point: '포인트 부족', owner: '미담당 업체', late: '마감 지남' };
	var current = null;     // 지금 열린 칸 id (예: "b3-review")
	var mode = 'grid';      // 'grid' = 격자 순서 / 'biz' = 같은 업체 안에서
	var typeFilter = '';    // '' = 전체 유형 / 'v' 방문형 / 's' 배송형 / 'p' 기자단
	// [2026-11-12] 보기 범위 — '' 전체 / 'me' 내 업체 / 'team' 우리 팀. 기준 = 보는 사람(<body data-me data-team>, js/scope.js)
	var viewFilter = '';
	var ME = document.body.dataset.me || '', MY_TEAM = document.body.dataset.team || '';

	// ── 기한 표기 (gen_dashboard.py 의 due_label / due_class 와 같은 규칙) ──
	function dueLabel(d) { return d < 0 ? (-d) + '일 지남' : d === 0 ? '오늘' : 'D-' + d; }
	function dueClass(d) { return d <= 0 ? 'is-hot' : d <= 3 ? 'is-soon' : 'is-later'; }
	function dueGroup(d) { return d === null ? 'none' : d < 0 ? 'late' : d === 0 ? 'today' : d <= 3 ? 'soon' : 'later'; }
	function byDue(a, b) { return a.d - b.d; }
	function mixText(items) {
		var seen = {};
		items.forEach(function (it) { seen[it.d] = (seen[it.d] || 0) + 1; });
		return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; })
			.map(function (d) { return dueLabel(d) + ' ' + seen[d] + '건'; }).join(' · ');
	}

	// 칸의 건 목록 [{d: 기한, t: 유형}] — 유형이 없는 이슈(미담당 등)는 t = ''
	function readItems(c) {
		if (!c.dataset.dues) return [];
		var ds = c.dataset.dues.split(','), ts = (c.dataset.types || '').split(','), cs = (c.dataset.camps || '').split(',');
		return ds.map(function (d, i) { return { d: Number(d), t: ts[i] || '', c: cs[i] || '' }; });
	}
	function writeItems(c, items) {
		items.sort(byDue);
		c.dataset.dues = items.map(function (x) { return x.d; }).join(',');
		c.dataset.types = items.map(function (x) { return x.t; }).join(',');
		c.dataset.camps = items.map(function (x) { return x.c; }).join(',');
	}
	// 지금 보이는 건 = 유형 칩으로 거른 건
	function shownItems(c) {
		var items = readItems(c);
		return typeFilter ? items.filter(function (x) { return x.t === typeFilter; }) : items;
	}

	// 화면에 보이는(남은) 칸 목록 — 숨겨진 묶음·처리 끝난 칸·유형으로 걸러진 칸은 뺀다
	function visibleCells() {
		return Array.prototype.filter.call(grid.querySelectorAll('.cell:not(.ccell)'), function (el) {
			return el.offsetParent !== null && !el.classList.contains('ag-done') && !el.classList.contains('t-zero');
		});
	}

	// 1) 처리 패널 열기
	function openPane(id) {
		var pane = panel.querySelector('[data-panel="' + id + '"]');
		if (!pane) return;
		panel.querySelectorAll('.pane').forEach(function (p) { p.hidden = true; });
		panel.querySelector('.pane-done').hidden = true;
		pane.hidden = false;
		panel.classList.add('has-pane');
		grid.querySelectorAll('.cell.sel').forEach(function (c) { c.classList.remove('sel'); });
		grid.querySelectorAll('[data-cell="' + id + '"]').forEach(function (c) { c.classList.add('sel'); });
		current = id;
		var vis = grid.querySelector('.cell.sel');
		if (vis && vis.offsetParent) vis.scrollIntoView({ block: 'nearest', inline: 'nearest' });
	}

	// 4) 다음 칸
	function next() {
		var cells = visibleCells();
		if (mode === 'biz' && current) {
			var biz = current.split('-')[0];
			var same = cells.filter(function (c) { return c.dataset.cell.indexOf(biz + '-') === 0 && c.dataset.cell !== current; });
			if (same.length) return openPane(same[0].dataset.cell);
			mode = 'grid';
		}
		// 처음 누를 때는 빨강(기한 지남·오늘) 칸부터
		if (!current) {
			var hot = cells.filter(function (c) { return c.classList.contains('is-hot'); })[0];
			if (hot) return openPane(hot.dataset.cell);
		}
		var ids = cells.map(function (c) { return c.dataset.cell; });
		var i = ids.indexOf(current);
		var target = ids[i + 1] || (i === -1 ? ids[0] : null);
		if (target) return openPane(target);
		// 남은 칸이 없으면 완료 화면
		panel.querySelectorAll('.pane').forEach(function (p) { p.hidden = true; });
		panel.querySelector('.pane-done').hidden = false;
		panel.classList.add('has-pane');
	}

	// 칸 다시 그리기 — 숫자, 가장 급한 기한, 섞임 막대, 툴팁 (유형 칩 반영)
	function renderCell(c) {
		var all = readItems(c), items = shownItems(c);
		c.dataset.n = all.length;
		c.classList.remove('is-hot', 'is-soon', 'is-later', 't-zero');
		var old = c.querySelector('.mixbar');
		if (old) old.remove();
		if (!all.length) { c.classList.add('ag-done'); c.querySelector('b').textContent = 0; c.querySelector('small').textContent = '처리'; c.title = '처리 완료'; return 0; }
		if (!items.length) { c.classList.add('t-zero', 'is-later'); c.querySelector('b').textContent = 0; c.querySelector('small').textContent = '다른 유형'; c.title = '이 유형의 건 없음'; return 0; }
		items.sort(byDue);
		c.classList.add(dueClass(items[0].d));
		c.querySelector('b').textContent = items.length;
		c.querySelector('small').textContent = dueLabel(items[0].d);
		var distinct = items.filter(function (x, i) { return items.findIndex(function (y) { return y.d === x.d; }) === i; });
		if (distinct.length > 1) {
			var bar = document.createElement('i');
			bar.className = 'mixbar';
			bar.setAttribute('aria-hidden', 'true');
			['is-hot', 'is-soon', 'is-later'].forEach(function (cls) {
				var n = items.filter(function (x) { return dueClass(x.d) === cls; }).length;
				if (!n) return;
				var s = document.createElement('span');
				s.className = cls;
				s.style.flex = n;
				bar.appendChild(s);
			});
			c.appendChild(bar);
		}
		c.title = mixText(items);
		c.setAttribute('aria-label', c.getAttribute('aria-label').replace(/\d+건 · .*$/, items.length + '건 · ' + c.title));
		return items.length;
	}

	// 8) 캠페인 줄 칸 — 업체 칸(data-of)의 건 중 이 캠페인(data-camp) 건만
	function renderCCell(cc) {
		var base = grid.querySelector('.tb-biz [data-cell="' + cc.dataset.of + '"]');
		var items = base ? shownItems(base).filter(function (x) { return x.c === cc.dataset.camp; }) : [];
		cc.classList.remove('is-hot', 'is-soon', 'is-later', 'ag-done', 't-zero');
		if (!items.length) {
			var anyLeft = base && readItems(base).some(function (x) { return x.c === cc.dataset.camp; });
			cc.classList.add(anyLeft ? 't-zero' : 'ag-done');
			cc.querySelector('b').textContent = 0;
			cc.querySelector('small').textContent = anyLeft ? '다른 유형' : '처리';
			return 0;
		}
		items.sort(byDue);
		cc.classList.add(dueClass(items[0].d));
		cc.querySelector('b').textContent = items.length;
		cc.querySelector('small').textContent = dueLabel(items[0].d);
		return items.length;
	}

	// 합계 행 · 담당자 머리 · 업체 행 합계를 칸에서 다시 센다 (유형 칩이 바뀌어도 맞게)
	function recount() {
		var sums = {};
		function add(k, n) { sums[k] = (sums[k] || 0) + n; }
		grid.querySelectorAll('.tb-biz tr.biz').forEach(function (row) {
			var rowTot = 0;
			var out = row.classList.contains('o-out');
			row.querySelectorAll('.cell:not(.ccell)').forEach(function (c) {
				var n = out || c.classList.contains('ag-done') || c.classList.contains('t-zero') ? 0 : shownItems(c).length;
				var key = c.dataset.cell.split('-')[1];
				rowTot += n;
				add('all-' + key, n); add('all-total', n);
				if (c.dataset.owner) { add('s-' + c.dataset.owner + '-' + key, n); add('s-' + c.dataset.owner + '-total', n); }
			});
			row.classList.toggle('t-empty', rowTot === 0);
			// 같은 업체의 담당자별 보기 행에도 같은 합계·숨김
			var id = row.querySelector('.bizlink').dataset.biz;
			grid.querySelectorAll('.bizlink[data-biz="' + id + '"]').forEach(function (l) {
				var r = l.closest('tr');
				r.querySelector('.tot').textContent = rowTot || '';
				r.classList.toggle('t-empty', rowTot === 0);
			});
		});
		grid.querySelectorAll('[data-sum]').forEach(function (el) {
			var n = sums[el.dataset.sum] || 0;
			el.textContent = n || '·';
			el.classList.toggle('zero', !n);
		});
		grid.querySelectorAll('tr.camp').forEach(function (r) {
			var n = 0;
			r.querySelectorAll('.ccell').forEach(function (cc) { n += renderCCell(cc); });
			r.querySelector('.tot').textContent = n || '';
			r.classList.toggle('t-empty', n === 0);
		});
		// 묶음 머리의 "N곳"
		grid.querySelectorAll('.tb-biz tr.grp').forEach(function (h) {
			var n = 0, r = h.nextElementSibling;
			while (r && !r.classList.contains('grp')) { if (r.classList.contains('biz') && !r.classList.contains('o-out') && !(typeFilter && r.classList.contains('t-empty'))) n++; r = r.nextElementSibling; }
			var em = h.querySelector('.js-gcount');
			if (em) em.textContent = n + '곳';
			h.classList.toggle('g-empty', n === 0);
		});
	}

	// 업체 행을 남은 이슈의 가장 급한 기한에 맞는 묶음으로 옮김 (업체별 보기만)
	function minOf(row) {
		var ds = [];
		row.querySelectorAll('.cell:not(.ccell):not(.ag-done)').forEach(function (c) { readItems(c).forEach(function (x) { ds.push(x.d); }); });
		return ds.length ? Math.min.apply(null, ds) : null;
	}
	function campRowsOf(row) {
		var subs = [], n = row.nextElementSibling;
		while (n && n.classList.contains('camp')) { subs.push(n); n = n.nextElementSibling; }
		return subs;
	}
	function placeAfter(row, subs) {
		var ref = row;
		subs.forEach(function (s) { ref.parentNode.insertBefore(s, ref.nextElementSibling); ref = s; });
	}
	function regroup(row) {
		var subs = campRowsOf(row);
		var min = minOf(row);
		var g = dueGroup(min);
		row.dataset.min = min === null ? 99 : min;
		// 왼쪽 색 선(data-g)은 업체별·담당자별 두 행 모두 바꾼다
		var bizId = row.querySelector('.bizlink').dataset.biz;
		grid.querySelectorAll('.bizlink[data-biz="' + bizId + '"]').forEach(function (l) { l.closest('tr').dataset.g = g; });
		if (g === 'none') {
			row.classList.add('quiet');
			grid.querySelector('.tb-none').appendChild(row);
			placeAfter(row, subs);
			return;
		}
		var head = grid.querySelector('.tb-biz tr.grp[data-g="' + g + '"]');
		var at = head.nextElementSibling;
		// 같은 묶음 안에서 급한 순 자리 — 캠페인 줄은 앞 업체에 딸린 것이므로 건너뛴다
		while (at && (at.classList.contains('camp') || (at.classList.contains('biz') && (at === row || (at.dataset.min ? Number(at.dataset.min) : (minOf(at) === null ? 99 : minOf(at))) <= min)))) at = at.nextElementSibling;
		head.parentNode.insertBefore(row, at);
		placeAfter(row, subs);
	}

	// 3) 처리 반영 — removes = [{d, t}] 한 건씩 뺀다. 남은 건수(전체)를 돌려줌
	function update(id, removes) {
		var cells = grid.querySelectorAll('[data-cell="' + id + '"]');   // 업체별·담당자별 두 군데
		var left = [];
		cells.forEach(function (c) {
			left = readItems(c);
			removes.forEach(function (r) {
				var i = left.findIndex(function (x) { return x.d === r.d && (!r.t || x.t === r.t) && (!r.c || x.c === r.c); });
				if (i > -1) left.splice(i, 1);
			});
			writeItems(c, left);
			renderCell(c);
		});
		// 패널 머리 ("검수 5건 [오늘]" + "오늘 1건 · D-2 1건")
		var pane = panel.querySelector('[data-panel="' + id + '"]');
		pane.querySelector('h2 em').textContent = left.length + '건';
		var chip = pane.querySelector('.js-due');
		if (left.length) {
			chip.className = 'due js-due ' + dueClass(left[0].d);
			chip.textContent = dueLabel(left[0].d);
			pane.querySelector('.js-mix').textContent = mixText(left);
		} else {
			chip.className = 'due js-due is-later';
			chip.textContent = '처리 완료';
			pane.querySelector('.js-mix').textContent = '남은 건 없음';
		}
		// 같은 업체 패널들의 이슈 칩("신청 확인 5")도 남은 건수로
		var key = id.split('-')[1];
		panel.querySelectorAll('.pchip[data-go="' + id + '"]').forEach(function (p) { p.textContent = ISSUE_NAME[key] + ' ' + left.length; });
		var row = grid.querySelector('.tb-biz [data-cell="' + id + '"]');
		if (row) regroup(row.closest('tr'));
		recount();
		return left.length;
	}
	function itemOf(li) { return { d: Number(li.dataset.due), t: li.dataset.type || '', c: li.dataset.camp || '' }; }

	/* [2026-11-09] 이슈를 다 처리해도 패널을 자동으로 넘기지 않는다
	     사용자: "완료되면 자동으로 급한 일정으로 패널이 바뀌어 매니저가 혼란스러울 수 있다"
	     → 그 자리에 "처리 완료" 안내만 띄우고, 다음으로 갈지는 사람이 [다음 ▶]으로 정한다. */
	function finished(pane) {
		if (pane.querySelector('.pane-fin')) return;
		var fin = document.createElement('p');
		fin.className = 'pane-fin';
		fin.setAttribute('role', 'status');
		fin.textContent = '✓ 이 이슈를 모두 처리했습니다. 다음 이슈로 가려면 아래 [다음 ▶]을 누르세요.';
		pane.querySelector('.pane-b').prepend(fin);
		pane.querySelector('.pane-b').scrollTop = 0;
		pane.querySelector('.js-next').classList.add('is-ready');
	}

	function doneTag(text) {
		var tag = document.createElement('span');
		tag.className = 'done-tag';
		tag.textContent = text;
		return tag;
	}

	function markDone(btn) {
		var pane = btn.closest('.pane');
		var id = pane.dataset.panel;
		// 표시만 하는 버튼(선정 마감의 신청자 선정) — 숫자는 [선정 완료] 때 줄어듦
		if (btn.hasAttribute('data-mark')) {
			var li = btn.closest('.item');
			li.querySelector('.acts').replaceWith(doneTag(btn.dataset.ag-done));
			li.classList.add('is-done');
			return;
		}
		var left;
		if (btn.hasAttribute('data-gwhole')) {
			// 캠페인 묶음 하나를 한 번에 (예: 기자단 자료 올리기 → 그 캠페인 미전달 전부 해결)
			var grp = btn.closest('.cgroup');
			var lis = Array.prototype.slice.call(grp.querySelectorAll('.item:not(.is-done)'));
			btn.closest('.upload').replaceWith(doneTag(btn.dataset.ag-done));
			lis.forEach(function (l) { l.classList.add('is-done'); });
			left = update(id, lis.map(itemOf));
		} else if (btn.hasAttribute('data-whole')) {
			// 이슈 전체를 한 번에 처리 — 남은 건 전부
			var host = btn.closest('.acts, .assign') || btn;
			host.replaceWith(doneTag(btn.dataset.ag-done));
			pane.querySelectorAll('.item:not(.is-done)').forEach(function (i) { i.classList.add('is-done'); });
			left = update(id, readItems(grid.querySelector('[data-cell="' + id + '"]')));
		} else {
			// 한 건 처리 — 그 건의 기한·유형만 뺀다
			var item = btn.closest('.item');
			var host2 = item.querySelector('.acts, .ship-f');
			host2.replaceWith(doneTag(btn.dataset.ag-done));
			item.classList.add('is-done');
			left = update(id, [itemOf(item)]);
		}
		if (left === 0) finished(pane);
	}

	// 5) 유형 칩
	function setType(btn) {
		typeFilter = btn.dataset.type;
		document.querySelectorAll('.tchip').forEach(function (b) { b.classList.toggle('ag-on', b === btn); });
		if (typeFilter) grid.dataset.type = typeFilter; else delete grid.dataset.type;
		grid.querySelectorAll('.cell:not(.ccell)').forEach(renderCell);
		grid.querySelectorAll('.ccell').forEach(renderCCell);
		// 패널 안에서도 다른 유형 캠페인 묶음은 흐리게
		panel.querySelectorAll('.cgroup').forEach(function (g) { g.classList.toggle('t-off', !!typeFilter && g.dataset.type !== typeFilter); });
		recount();
	}

	// [2026-11-12] 5-1) 보기 범위 [내 업체] [우리 팀] [전체] — 요청 "현재 개인 지정해서 내 업체 · 우리 팀도 작동하게"
	//   행의 data-own(담당자) · data-team(팀)을 보는 사람과 견줘 o-out(숨김)을 붙이고, 합계를 다시 셈
	function rowOut(r) {
		if (!viewFilter || !r.hasAttribute('data-team')) return false;
		if (viewFilter === 'team') return r.dataset.team !== MY_TEAM;
		return r.hasAttribute('data-own') ? r.dataset.own !== ME : r.dataset.team !== MY_TEAM;   // 팀 머리줄 = 내 팀만
	}
	function setView(vw) {
		viewFilter = vw;
		document.querySelectorAll('.js-vw').forEach(function (b) { b.classList.toggle('ag-on', b.dataset.vw === vw); });
		grid.querySelectorAll('tr[data-team]').forEach(function (r) {
			var out = rowOut(r);
			r.classList.toggle('o-out', out);
			if (r.classList.contains('biz')) campRowsOf(r).forEach(function (s) { s.classList.toggle('o-out', out); });
		});
		recount();
		var note = document.querySelector('.js-vw-note');
		var who = document.body.dataset.meName || '대표님';
		var mine = grid.querySelectorAll('.tb-biz tr.biz:not(.o-out)');
		var hot = Array.prototype.filter.call(mine, function (r) { return !r.classList.contains('t-empty'); }).length;
		var head = vw === 'me' ? who + ' 담당 ' : vw === 'team' ? MY_TEAM + ' ' : '';
		if (note) note.textContent = vw ? head + mine.length + '곳 · 이슈 있는 곳 ' + hot : '';
	}
	(function initView() {
		var bMe = document.querySelector('.js-vw[data-vw="me"]'), bTeam = document.querySelector('.js-vw[data-vw="team"]');
		if (!bMe) return;
		// 대표(관리자) = 맡은 업체 · 팀 없음 → 두 버튼을 끄고 이유를 보여 줌 / 팀 없는 직원 = [우리 팀]만 끔
		var hint = '사이드바 이름(대표님 ▾)을 눌러 보는 사람을 고르세요';
		if (!ME) { bMe.disabled = bTeam.disabled = true; bMe.title = bTeam.title = hint; }
		else if (!MY_TEAM) { bTeam.disabled = true; bTeam.title = '팀이 없는 담당자입니다'; }
		document.querySelectorAll('.js-vw').forEach(function (b) { b.addEventListener('click', function () { setView(b.dataset.vw); }); });
		if (ME) setView('me');      // 직원으로 보면 처음부터 내 업체
		else { var note = document.querySelector('.js-vw-note'); if (note) note.textContent = '보는 사람: 대표님(관리자) · 이름을 눌러 바꾸기'; }
	})();

	// 6) 선정 근거 — 근거(지수·이력)가 없는 신청자는 블로그를 열어 봐야 [선정]이 켜진다
	//   시안에서는 실제 블로그로 나가지 않고 "확인함" 표시만 한다.
	function checkBlog(a) {
		var li = a.closest('.item');
		li.classList.remove('need-check');
		li.classList.add('checked');
		var pick = li.querySelector('.js-pick');
		if (pick) { pick.disabled = false; pick.removeAttribute('title'); }
		var gate = li.querySelector('.gate');
		if (gate) gate.textContent = '✓ 블로그 확인함';
		a.textContent = '블로그 다시 보기 ↗';
	}
	// 신청자 정렬 — 같은 캠페인 묶음 안에서만 (높은 값 먼저, '신청순'은 처음 순서)
	function sortApplicants(btn) {
		var pane = btn.closest('.pane');
		var key = btn.dataset.sort;
		pane.querySelectorAll('.sort').forEach(function (s) { s.classList.toggle('ag-on', s === btn); });
		pane.querySelectorAll('.cgroup .items').forEach(function (ul) {
			var lis = Array.prototype.slice.call(ul.children);
			lis.forEach(function (li, i) { if (!li.dataset.i) li.dataset.i = i; });
			lis.sort(function (a, b) {
				if (!key) return a.dataset.i - b.dataset.i;
				return (Number(b.dataset[key]) || 0) - (Number(a.dataset[key]) || 0);
			});
			lis.forEach(function (li) { ul.appendChild(li); });
		});
	}

	// 7) 추가모집(= 초과모집 + 재모집) — 비용 미리보기 (시안 — 실제 차감 없음)
	function won(n) { return n.toLocaleString('ko-KR') + 'P'; }
	function calcRecruit(box) {
		var n = Math.max(1, Math.min(20, Number(box.querySelector('.rc-n').value) || 1));
		var free = Math.min(n, Number(box.dataset.free));
		var over = (n - free) * Number(box.dataset.unit);
		var reward = n * Number(box.dataset.reward);
		var total = reward + over;
		var bal = Number(box.dataset.bal);
		box.querySelector('.js-c-reward').textContent = n + '명 × ' + won(Number(box.dataset.reward)) + ' = ' + won(reward);
		box.querySelector('.js-c-free').textContent = free + '명 무료';
		box.querySelector('.js-c-over').textContent = (n - free) ? (n - free) + '명 × ' + won(Number(box.dataset.unit)) + ' = ' + won(over) : '없음';
		box.querySelector('.js-c-total').textContent = won(total);
		var balEl = box.querySelector('.js-c-bal');
		balEl.textContent = won(bal) + (total > bal ? '  ✕ 부족' : '  ✓ 충분');
		balEl.className = 'js-c-bal ' + (total > bal ? 'bad' : 'ok');
		// 잔액이 모자라면 시작 대신 충전 요청 (→ 포인트 부족 이슈로 넘어감, 8-4)
		var btn = box.querySelector('.js-recruit');
		btn.dataset.short = total > bal ? '1' : '';
		btn.textContent = total > bal ? '충전 요청' : box.querySelector('.rc-t').textContent + ' 시작';
	}
	document.querySelectorAll('.recruit').forEach(calcRecruit);
	document.addEventListener('input', function (e) {
		var box = e.target.closest('.recruit');
		if (box) calcRecruit(box);
	});
	function startRecruit(btn) {
		var box = btn.closest('.recruit');
		var pane = btn.closest('.pane');
		var ext = box.querySelector('.rc-ext').value.replace('+', '');
		var n = box.querySelector('.rc-n').value;
		var msg = btn.dataset.short ? '충전 요청 보냄 · 관리자에게 알림'
			: box.querySelector('.rc-t').textContent + ' 시작 · ' + n + '명' + (Number(ext) ? ' · 모집 마감 11/' + (9 + Number(ext)) : '');
		btn.closest('.acts').replaceWith(doneTag(msg));
		box.querySelectorAll('input, select').forEach(function (f) { f.disabled = true; });
		// 선정 마감 패널의 [추가 모집] = 모집 중으로 돌아가므로 이 이슈는 닫힌다
		if (btn.dataset.kind === 'add' && !btn.dataset.short) {
			var left = update(pane.dataset.panel, readItems(grid.querySelector('[data-cell="' + pane.dataset.panel + '"]')));
			pane.querySelectorAll('.acts:not(.rc-b .acts)').forEach(function (a) { a.remove(); });
			if (left === 0) finished(pane);
		}
	}

	// ── 9) 수시 알림 [2026-11-10 v0.4] ─────────────────────────────
	//   순차 흐름(격자)과 따로 오는 일. 즉시·확인 등급은 [처리] 또는 [나중에]를 눌러야 목록에서 빠진다.
	var alPane = panel.querySelector('[data-panel="alerts"]');
	var KIND_NAME = { cancel: '취소 요청', report: '신고 접수', payfail: '지급 실패', deleted: '리뷰 삭제·비공개', msg: '쪽지·문의', rereview: '리뷰 재등록', assigned: '담당 배정', paid: '입금 완료', charged: '충전 완료' };
	var baseTitle = document.title;

	function openAlerts() { return Array.prototype.slice.call(alPane.querySelectorAll('.js-al-list .al-card:not([hidden])')); }
	function kindsText(list) {
		var seen = {};
		list.forEach(function (a) { seen[a.dataset.kind] = (seen[a.dataset.kind] || 0) + 1; });
		return Object.keys(seen).sort(function (a, b) { return seen[b] - seen[a]; }).slice(0, 2)
			.map(function (k) { return KIND_NAME[k] + ' ' + seen[k]; }).join(' · ');
	}
	function setText(sel, txt) { document.querySelectorAll(sel).forEach(function (el) { el.textContent = txt; }); }

	// 숫자 다시 세기 — 띠 · 패널 칩 · 종 · 탭 제목 · 업체 알림 점
	function recountAlerts() {
		var open = openAlerts();
		var by = { u: [], c: [], i: [] };
		open.forEach(function (a) { by[a.dataset.lv].push(a); });
		setText('.js-ab-u', by.u.length); setText('.js-ab-c', by.c.length); setText('.js-ab-i', by.i.length);
		setText('.js-ab-ukinds', kindsText(by.u)); setText('.js-ab-ckinds', kindsText(by.c));
		setText('.js-alv-all', open.length); setText('.js-alv-u', by.u.length); setText('.js-alv-c', by.c.length); setText('.js-alv-i', by.i.length);
		setText('.js-al-open', (by.u.length + by.c.length) + '건');
		document.querySelector('.alertbar').classList.toggle('has-u', by.u.length > 0);
		var need = by.u.length + by.c.length;          // 처리해야 하는 것만 센다(참고 제외)
		// [2026-11-12 v0.9] 위 막대의 종(.bell)이 광고주 사이드바 아이콘 줄로 바뀜 — 없는 .bell 을 건드려 스크립트가 멈추고
		//   대시보드 클릭이 모두 안 되던 문제. 이제 사이드바 [알림] 아이콘의 빨간 점을 처리할 알림이 있을 때만 보인다
		var bell = document.querySelector('.bell i');
		if (bell) { bell.textContent = need; bell.hidden = !need; }
		var dot = document.querySelector('.sidebar-icons .icon-btn[title="알림"] .badge-dot');
		if (dot) dot.hidden = !need;
		document.title = (need ? '(' + need + ') ' : '') + baseTitle;
		// 업체 알림 점: 즉시·확인 건수, 즉시가 있으면 빨강
		var perBiz = {};
		by.u.concat(by.c).forEach(function (a) {
			var b = perBiz[a.dataset.biz] || (perBiz[a.dataset.biz] = { n: 0, u: false });
			b.n++; if (a.dataset.lv === 'u') b.u = true;
		});
		grid.querySelectorAll('.adot').forEach(function (d) {
			var b = perBiz[d.dataset.abiz];
			d.hidden = !b;
			d.classList.toggle('lv-u', !!(b && b.u));
			d.querySelector('em').textContent = b ? b.n : '';
			d.setAttribute('aria-label', b ? '처리할 알림 ' + b.n + '건' : '');
			d.closest('tr').classList.toggle('has-alert', !!b);
		});
		alPane.querySelector('.js-al-later summary em').textContent = alPane.querySelectorAll('.js-al-later .al-card').length;
		alPane.querySelector('.js-al-done summary em').textContent = alPane.querySelectorAll('.js-al-done .al-card').length;
	}

	// 알림 패널 열기 — lv = 등급 거르기('' 전체), biz = 업체 하나만
	function setAlertLevel(lv) {
		alPane.dataset.lv = lv;
		alPane.querySelectorAll('.alv').forEach(function (b) { b.classList.toggle('ag-on', b.dataset.alv === lv); });
	}
	function showAlerts(lv, biz) {
		panel.querySelectorAll('.pane').forEach(function (p) { p.hidden = true; });
		panel.querySelector('.pane-done').hidden = true;
		alPane.hidden = false;
		panel.classList.add('has-pane');
		grid.querySelectorAll('.cell.sel').forEach(function (c) { c.classList.remove('sel'); });
		current = null;
		setAlertLevel(lv || '');
		alPane.dataset.biz = biz || '';
		alPane.querySelectorAll('.al-card').forEach(function (a) { a.classList.toggle('f-out', !!biz && a.dataset.biz !== biz); });
		var note = alPane.querySelector('.al-bizf');
		note.hidden = !biz;
		if (biz) note.querySelector('.js-al-bizname').textContent = grid.querySelector('.bizlink[data-biz="' + biz + '"]').textContent;
	}
	function closeAlerts() {
		alPane.hidden = true;
		panel.classList.remove('has-pane');
	}

	// 처리 / 나중에 — 카드를 아래 접힌 묶음으로 옮긴다
	function alertDone(btn) {
		var a = btn.closest('.al-card');
		a.querySelector('.al-acts').replaceWith(doneTag(btn.dataset.adone));
		a.classList.remove('is-new', 'is-snoozed');
		a.classList.add('is-done');
		alPane.querySelector('.js-al-done .al-list').prepend(a);
		recountAlerts();
		if (btn.classList.contains('js-al-go') && a.dataset.go) openPane(a.dataset.go);
	}
	function alertSnooze(btn) {
		var a = btn.closest('.al-card');
		a.classList.remove('is-new');
		a.classList.add('is-snoozed');
		var old = a.querySelector('.al-sz');
		if (old) old.remove();
		var sz = document.createElement('p');
		sz.className = 'al-sz';
		sz.textContent = btn.dataset.snooze;
		a.querySelector('.al-acts').before(sz);
		btn.closest('details').open = false;
		alPane.querySelector('.js-al-later .al-list').prepend(a);
		recountAlerts();
	}

	// 시연: 화면을 연 뒤 잠시 후 새 취소 요청이 들어온다
	// [2026-11-12] 오른쪽 아래 토스트는 뺌(요청 "우측 하단 알림은 제거") — 받은 알림 띠·목록 숫자만 늘어난다
	setTimeout(function () {
		var demo = alPane.querySelector('.al-card[data-demo]');
		if (!demo) return;
		demo.hidden = false;
		demo.removeAttribute('data-demo');
		alPane.querySelector('.js-al-list').prepend(demo);
		recountAlerts();
	}, 4000);
	recountAlerts();

	// [2026-11-10 v0.5] 다른 화면에서 바로 오기 — 일정·업체 화면의 이슈 칩
	//   #open=b3-review → 그 칸을 연다 / #biz=b3 → 그 업체의 가장 급한 칸부터(다음 = 같은 업체 안에서)
	(function deepLink() {
		var h = location.hash;
		var mo = h.match(/^#open=(b\d+-[a-z]+)/);
		if (mo && panel.querySelector('[data-panel="' + mo[1] + '"]')) { mode = 'biz'; return openPane(mo[1]); }
		var mb = h.match(/^#biz=(b\d+)/);
		if (mb) {
			var link = grid.querySelector('.tb-biz .bizlink[data-biz="' + mb[1] + '"]');
			if (link) link.click();
		}
	})();

	// 이벤트 하나로 묶어서 처리 (위임)
	document.addEventListener('click', function (e) {
		var card = e.target.closest('.al-card.is-new');
		if (card) card.classList.remove('is-new');      // 읽음 표시만 — 목록에서는 안 빠진다
		var blog = e.target.closest('a.js-blog');
		if (blog) { e.preventDefault(); return checkBlog(blog); }
		var t = e.target.closest('button');
		if (!t) return;
		if (t.matches('[data-open-alerts]')) return showAlerts(t.dataset.openAlerts, '');
		if (t.matches('.adot')) return showAlerts('', t.dataset.abiz);
		if (t.matches('.alv')) return setAlertLevel(t.dataset.alv);
		if (t.matches('.js-al-allbiz')) return showAlerts(alPane.dataset.lv, '');
		if (t.matches('.js-close-alerts')) return closeAlerts();
		if (t.matches('[data-adone]')) return alertDone(t);
		if (t.matches('[data-snooze]')) return alertSnooze(t);
		if (t.matches('.js-afilter')) {
			var on = !grid.dataset.alert;
			if (on) grid.dataset.alert = '1'; else delete grid.dataset.alert;
			t.classList.toggle('ag-on', on);
			return;
		}
		if (t.matches('.ccell')) {
			mode = 'grid';
			openPane(t.dataset.of);
			var area = document.getElementById('cg-' + t.dataset.of + '-' + t.dataset.camp);
			if (area) { area.scrollIntoView({ block: 'start' }); area.classList.add('is-focus'); setTimeout(function () { area.classList.remove('is-focus'); }, 1200); }
			return;
		}
		if (t.matches('.cell')) { mode = 'grid'; return openPane(t.dataset.cell); }
		if (t.matches('.bizlink')) {
			// 업체명 = 그 업체의 가장 급한 칸부터, [다음]은 같은 업체 안에서
			var cells = Array.prototype.slice.call(t.closest('tr').querySelectorAll('.cell:not(.ccell):not(.ag-done):not(.t-zero)'));
			cells.sort(function (a, b) { return shownItems(a)[0].d - shownItems(b)[0].d; });
			if (cells[0]) { mode = 'biz'; openPane(cells[0].dataset.cell); }
			return;
		}
		if (t.matches('.pchip')) { mode = 'biz'; return openPane(t.dataset.go); }
		if (t.matches('.js-next')) return next();
		if (t.matches('.sort')) return sortApplicants(t);
		if (t.matches('.js-recruit')) return startRecruit(t);
		if (t.matches('.tchip')) return setType(t);
		if (t.matches('.colh')) {
			// 2) 같은 열을 다시 누르면 거르기 해제
			var col = t.dataset.col;
			if (grid.dataset.filter === col) { delete grid.dataset.filter; filterNote.hidden = true; }
			else {
				grid.dataset.filter = col;
				filterNote.hidden = false;
				filterNote.querySelector('.js-filter-name').textContent = ISSUE_NAME[col];
			}
			mode = 'grid';
			return;
		}
		if (t.matches('.js-clear')) { delete grid.dataset.filter; filterNote.hidden = true; return; }
		if (t.matches('[data-done]')) return markDone(t);
	});

	// [2026-11-13] 캠페인 창(가운데 모달) — 요청 "대시보드에서 업무와 연계된 클릭은 대시보드를 벗어나지 않게, 캠페인은 가운데 모달로"
	//   왜 JS 인가: 누른 링크마다 창 안 화면 주소(iframe src)를 바꿔 넣어야 하는데 CSS 로는 못 한다. 여닫기는 <dialog>.
	//   창 안 = 캠페인 화면 삽입 모드(?embed=1 — 사이드바 없이, js/scope.js). [새 창으로 ↗] 는 원래 화면.
	var cm = document.getElementById('cmodal');
	if (cm) {
		var cmFrame = cm.querySelector('.js-cm-frame'), cmLoad = cm.querySelector('.js-cm-load');
		var embedUrl = function (href) {
			var i = href.indexOf('#');
			var path = i < 0 ? href : href.slice(0, i), hash = i < 0 ? '' : href.slice(i);
			return path + (path.indexOf('?') < 0 ? '?' : '&') + 'embed=1' + hash;
		};
		document.addEventListener('click', function (e) {
			var a = e.target.closest('a.js-cm');
			if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;   // 새 탭으로 열기는 그대로 둠
			e.preventDefault();
			var href = a.getAttribute('href');
			cm.querySelector('.js-cm-title').textContent = a.dataset.cmTitle || '캠페인';
			cm.querySelector('.js-cm-full').setAttribute('href', href);
			cmLoad.hidden = false;
			cmFrame.src = embedUrl(href);
			if (!cm.open) cm.showModal();
		});
		cmFrame.addEventListener('load', function () { if (cmFrame.src !== 'about:blank') cmLoad.hidden = true; });
		cm.addEventListener('close', function () { cmFrame.src = 'about:blank'; });
		// 바깥(어두운 곳)을 누르면 닫기
		cm.addEventListener('click', function (e) { if (e.target === cm) cm.close(); });
	}
})();
