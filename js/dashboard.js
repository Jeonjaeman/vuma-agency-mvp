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
		var ds = c.dataset.dues.split(','), ts = (c.dataset.types || '').split(',');
		return ds.map(function (d, i) { return { d: Number(d), t: ts[i] || '' }; });
	}
	function writeItems(c, items) {
		items.sort(byDue);
		c.dataset.dues = items.map(function (x) { return x.d; }).join(',');
		c.dataset.types = items.map(function (x) { return x.t; }).join(',');
	}
	// 지금 보이는 건 = 유형 칩으로 거른 건
	function shownItems(c) {
		var items = readItems(c);
		return typeFilter ? items.filter(function (x) { return x.t === typeFilter; }) : items;
	}

	// 화면에 보이는(남은) 칸 목록 — 숨겨진 묶음·처리 끝난 칸·유형으로 걸러진 칸은 뺀다
	function visibleCells() {
		return Array.prototype.filter.call(grid.querySelectorAll('.cell'), function (el) {
			return el.offsetParent !== null && !el.classList.contains('done') && !el.classList.contains('t-zero');
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
		if (!all.length) { c.classList.add('done'); c.querySelector('b').textContent = 0; c.querySelector('small').textContent = '처리'; c.title = '처리 완료'; return 0; }
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

	// 합계 행 · 담당자 머리 · 업체 행 합계를 칸에서 다시 센다 (유형 칩이 바뀌어도 맞게)
	function recount() {
		var sums = {};
		function add(k, n) { sums[k] = (sums[k] || 0) + n; }
		grid.querySelectorAll('.tb-biz tr.biz').forEach(function (row) {
			var rowTot = 0;
			row.querySelectorAll('.cell').forEach(function (c) {
				var n = c.classList.contains('done') || c.classList.contains('t-zero') ? 0 : shownItems(c).length;
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
		// 묶음 머리의 "N곳"
		grid.querySelectorAll('.tb-biz tr.grp').forEach(function (h) {
			var n = 0, r = h.nextElementSibling;
			while (r && !r.classList.contains('grp')) { if (r.classList.contains('biz') && !(typeFilter && r.classList.contains('t-empty'))) n++; r = r.nextElementSibling; }
			var em = h.querySelector('.js-gcount');
			if (em) em.textContent = n + '곳';
			h.classList.toggle('g-empty', n === 0);
		});
	}

	// 업체 행을 남은 이슈의 가장 급한 기한에 맞는 묶음으로 옮김 (업체별 보기만)
	function minOf(row) {
		var ds = [];
		row.querySelectorAll('.cell:not(.done)').forEach(function (c) { readItems(c).forEach(function (x) { ds.push(x.d); }); });
		return ds.length ? Math.min.apply(null, ds) : null;
	}
	function regroup(row) {
		var min = minOf(row);
		var g = dueGroup(min);
		row.dataset.min = min === null ? 99 : min;
		// 왼쪽 색 선(data-g)은 업체별·담당자별 두 행 모두 바꾼다
		var bizId = row.querySelector('.bizlink').dataset.biz;
		grid.querySelectorAll('.bizlink[data-biz="' + bizId + '"]').forEach(function (l) { l.closest('tr').dataset.g = g; });
		if (g === 'none') {
			row.classList.add('quiet');
			grid.querySelector('.tb-none').appendChild(row);
			return;
		}
		var head = grid.querySelector('.tb-biz tr.grp[data-g="' + g + '"]');
		var at = head.nextElementSibling;
		while (at && at.classList.contains('biz') && (at === row || (at.dataset.min ? Number(at.dataset.min) : (minOf(at) === null ? 99 : minOf(at))) <= min)) at = at.nextElementSibling;
		head.parentNode.insertBefore(row, at);
	}

	// 3) 처리 반영 — removes = [{d, t}] 한 건씩 뺀다. 남은 건수(전체)를 돌려줌
	function update(id, removes) {
		var cells = grid.querySelectorAll('[data-cell="' + id + '"]');   // 업체별·담당자별 두 군데
		var left = [];
		cells.forEach(function (c) {
			left = readItems(c);
			removes.forEach(function (r) {
				var i = left.findIndex(function (x) { return x.d === r.d && (!r.t || x.t === r.t); });
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
	function itemOf(li) { return { d: Number(li.dataset.due), t: li.dataset.type || '' }; }

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
			li.querySelector('.acts').replaceWith(doneTag(btn.dataset.done));
			li.classList.add('is-done');
			return;
		}
		var left;
		if (btn.hasAttribute('data-gwhole')) {
			// 캠페인 묶음 하나를 한 번에 (예: 기자단 자료 올리기 → 그 캠페인 미전달 전부 해결)
			var grp = btn.closest('.cgroup');
			var lis = Array.prototype.slice.call(grp.querySelectorAll('.item:not(.is-done)'));
			btn.closest('.upload').replaceWith(doneTag(btn.dataset.done));
			lis.forEach(function (l) { l.classList.add('is-done'); });
			left = update(id, lis.map(itemOf));
		} else if (btn.hasAttribute('data-whole')) {
			// 이슈 전체를 한 번에 처리 — 남은 건 전부
			var host = btn.closest('.acts, .assign') || btn;
			host.replaceWith(doneTag(btn.dataset.done));
			pane.querySelectorAll('.item:not(.is-done)').forEach(function (i) { i.classList.add('is-done'); });
			left = update(id, readItems(grid.querySelector('[data-cell="' + id + '"]')));
		} else {
			// 한 건 처리 — 그 건의 기한·유형만 뺀다
			var item = btn.closest('.item');
			var host2 = item.querySelector('.acts, .ship-f');
			host2.replaceWith(doneTag(btn.dataset.done));
			item.classList.add('is-done');
			left = update(id, [itemOf(item)]);
		}
		if (left === 0) finished(pane);
	}

	// 5) 유형 칩
	function setType(btn) {
		typeFilter = btn.dataset.type;
		document.querySelectorAll('.tchip').forEach(function (b) { b.classList.toggle('on', b === btn); });
		if (typeFilter) grid.dataset.type = typeFilter; else delete grid.dataset.type;
		grid.querySelectorAll('.cell').forEach(renderCell);
		// 패널 안에서도 다른 유형 캠페인 묶음은 흐리게
		panel.querySelectorAll('.cgroup').forEach(function (g) { g.classList.toggle('t-off', !!typeFilter && g.dataset.type !== typeFilter); });
		recount();
	}

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
		pane.querySelectorAll('.sort').forEach(function (s) { s.classList.toggle('on', s === btn); });
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

	// 이벤트 하나로 묶어서 처리 (위임)
	document.addEventListener('click', function (e) {
		var blog = e.target.closest('a.js-blog');
		if (blog) { e.preventDefault(); return checkBlog(blog); }
		var t = e.target.closest('button');
		if (!t) return;
		if (t.matches('.cell')) { mode = 'grid'; return openPane(t.dataset.cell); }
		if (t.matches('.bizlink')) {
			// 업체명 = 그 업체의 가장 급한 칸부터, [다음]은 같은 업체 안에서
			var cells = Array.prototype.slice.call(t.closest('tr').querySelectorAll('.cell:not(.done):not(.t-zero)'));
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
})();
