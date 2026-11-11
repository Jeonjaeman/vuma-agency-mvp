/* [2026-11-12 v0.9] 캠페인 등록 · 복제 — 광고주 등록창(campaignCreate.inc.html) 마크업 위에서 꼭 필요한 동작만
   단계 이동 · 유형별 3단계 · 채널별 키워드 줄 · 펼치기/접기 · 지급/미지급 · 닫기 확인은 CSS(css/bridge/create.css)가 한다.
   여기 남은 것은 CSS 로 안 되는 것뿐이다 — 각 묶음 위에 이유를 적었다. 요소는 createElement · textContent 로만 만든다. */
(function () {
	'use strict';

	var DATA = JSON.parse(document.getElementById('new-data').textContent);
	var form = document.forms.campaignForm;
	var $ = function (s, root) { return (root || document).querySelector(s); };
	var $$ = function (s, root) { return Array.prototype.slice.call((root || document).querySelectorAll(s)); };
	var copySrc = null;           // 복제 중인 캠페인 조건

	function num(v) { return parseInt(String(v).replace(/[^0-9]/g, ''), 10) || 0; }
	function setText(sel, text) { var el = $(sel); if (el) el.textContent = text; }

	/* [2026-11-12 v0.9] 안내 한 줄 — 시안이라 저장·이동이 없는 버튼에 "눌렀을 때 무슨 일이 생기는지"를 잠깐 보여 준다.
	   글자를 만들어 넣었다 지우는 일이라 CSS 로 안 된다. */
	function flash(text) {
		var f = document.createElement('div');
		f.className = 'ag-flash';
		f.setAttribute('role', 'status');
		f.textContent = text;
		document.body.appendChild(f);
		setTimeout(function () { f.remove(); }, 2400);
	}
	function pickedBiz() { return $('input[name=agBiz]:checked'); }
	function typeNow() { var t = $('input[name=campaignType]:checked'); return t ? t.value : '1'; }

	/* ── 총사용 포인트 (광고주 calcUsePoint) ──────────────────
	   [2026-11-12 v0.9] 인원 × 1인당 지급 + 수수료를 계산해 칸에 숫자로 적고, 잔액보다 크면 부족 문구를 띄운다.
	   숫자 계산 · 글자 바꾸기라 CSS 로 안 된다. (지급/미지급에 따른 줄 감춤은 CSS) */
	function calcUsePoint() {
		var cnt = num(form.cnt.value);
		var point = num(form.rewardPoint.value);
		var rewardsY = $('input[name=rewards][value=Y]').checked;
		var feeText = $('#feeText').value;
		var base = rewardsY ? cnt * point : 0;
		var total = base + Math.round(base * DATA.fee);
		$('#usePoint').value = total.toLocaleString();
		var feePart = (DATA.fee > 0 && feeText !== '') ? ' x 수수료 ' + feeText : '';
		setText('#usePointHint', 'P (모집인원 ' + cnt.toLocaleString() + ' x 지급포인트 ' + point.toLocaleString() + feePart + ')');
		var avail = num($('#myBalance').value) + num($('#reservedHold').value);
		$('#pointShortMsg').style.display = (rewardsY && total > avail) ? '' : 'none';
	}

	/* ── 노출 지역 요약 (광고주 zoneSyncLabel · zonePaintCounts · interestAreaSelect) ──
	   [2026-11-12 v0.9] 고른 지역 이름을 이어 붙여 요약줄과 접힌 시/도 줄에 적는다 · 시/도 '전체'를 누르면 그 아래를 함께 켜고 끈다.
	   다른 칸의 체크를 바꾸고 이름을 글자로 모으는 일이라 CSS 로 안 된다. */
	function zoneRowNames(row) {
		var all = $('input[parentArea=""]', row);
		if (all && all.checked) return [all.getAttribute('areaName') + ' 전체'];
		return $$('input[parentArea]:checked', row).filter(function (cb) { return cb.getAttribute('parentArea') !== ''; })
			.map(function (cb) { return cb.getAttribute('areaName'); });
	}
	function zoneSync() {
		var picked = [];
		$$('#zoneArea .p-region-row').forEach(function (row) {
			var names = zoneRowNames(row);
			var cnt = $('[data-zone-count]', row);
			var all = $('input[parentArea=""]', row);
			cnt.textContent = (all && all.checked) ? all.getAttribute('areaName') + '전체'
				: names.length > 3 ? names.slice(0, 3).join(', ') + ' 외 ' + (names.length - 3) : names.join(', ');
			cnt.classList.toggle('is-on', names.length > 0);
			picked = picked.concat(names);
		});
		var empty = typeNow() === '1' ? '주소를 입력하면 지역이 선택됩니다.' : '[펼쳐서 수정] 에서 지역을 고르세요.';
		setText('#zonePicked', picked.length === 0 ? empty
			: picked.length > 5 ? picked.slice(0, 5).join(', ') + ' 외 ' + (picked.length - 5) : picked.join(', '));
	}
	function onArea(cb) {
		var parent = cb.getAttribute('parentArea');
		if (parent === '') {
			$$('input[name="area[]"][parentArea="' + cb.value + '"]').forEach(function (x) { x.checked = cb.checked; });
		} else if (!cb.checked) {
			var all = $('input[name="area[]"][parentArea=""][value="' + parent + '"]');
			if (all) all.checked = false;
		}
		zoneSync();
	}
	// 업체 주소(예: "서울 강남구")로 지역을 잡는다 — 광고주 zoneFromAddress 와 같은 일(주소 → 지역 자동)
	function zoneFromAddress(reg) {
		var p = reg.split(' ');
		$$('#zoneArea .p-region-row').forEach(function (row) {
			if ($('.p-region-head__name', row).textContent !== p[0]) return;
			var gu = $$('input[parentArea]', row).filter(function (cb) { return cb.getAttribute('areaName') === p[1]; })[0];
			if (gu) gu.checked = true;
		});
		zoneSync();
	}

	/* ── 시/도 줄 접기 (광고주 zoneSidoToggle) ──
	   [2026-11-12 v0.9] 광고주 마크업은 <button aria-expanded> + 본문 hidden 속성이고, 화살표 모양도 aria-expanded 로 바뀐다.
	   button 을 그대로 두려면 속성을 바꿔야 해서 CSS 로 안 된다. */
	function sidoToggle(btn) {
		var open = btn.getAttribute('aria-expanded') !== 'true';
		btn.setAttribute('aria-expanded', open ? 'true' : 'false');
		btn.nextElementSibling.hidden = !open;
	}

	/* ── 유형을 누르면 '관심지역 설정하지 않음' 기본값 · 일정 칸 안내글 (광고주 campaignTypeChange) ──
	   [2026-11-12 v0.9] 방문형 → 체크 해제, 그 밖 → 체크. 다른 입력칸의 체크와 placeholder 를 바꾸는 일이라 CSS 로 안 된다.
	   (3단계 칸 · 라벨 글자 · 배송시작일 줄은 CSS) */
	function onType(byUser) {
		var t = typeNow();
		var nr = $('#noRegion');
		if (t === '1') nr.checked = false;
		else if (byUser) nr.checked = true;
		var del = t === '2';
		$('#campaignSTDate').placeholder = del ? '리뷰등록 시작일' : '체험시작일';
		$('#campaignEDDate').placeholder = del ? '리뷰등록 마감일' : '체험마감일';
		zoneSync();
	}

	/* ── 준수사항 '기본내용' → 글상자에 기본 문구 (광고주 abidanceTypeChange) ──
	   [2026-11-12 v0.9] def 속성의 문구를 비어 있는 글상자에 넣고, '없음'이면 비운다. 값을 바꾸는 일이라 CSS 로 안 된다. */
	function onAbidance(radio) {
		var ta = $('#' + radio.name.replace('Type', ''));
		if (!ta) return;
		if (radio.value === 'N') ta.value = '';
		else if (ta.value.trim() === '') ta.value = ta.getAttribute('def') || '';
	}

	/* ── 키워드 · 해시태그 추가/삭제 (광고주 keywordAdd · hashtagAdd · tagAdd · *Delete) ──
	   [2026-11-12 v0.9] 적은 글자로 태그를 새로 만들어 목록에 붙인다. 요소를 만드는 일이라 CSS 로 안 된다. */
	var TAG_LIST = { addkeyword: ['keywordListArea', 'cc-keyword-tag'], addhashtag: ['hashtagListArea', 'cc-hash-tag'] };
	function tagAdd(input) {
		var v = input.value.trim();
		if (!v) return;
		var map = TAG_LIST[input.id] || [input.id.replace(/^add_/, '') + 'ListArea', 'cc-hash-tag'];
		var list = document.getElementById(map[0]);
		var exists = $$('[data-tag]', list).some(function (t) { return t.dataset.tag === v; });
		if (exists) { flash('이미 추가된 키워드입니다'); return; }
		var t = document.createElement('span');
		t.className = map[1];
		t.dataset.tag = v;
		t.textContent = v;
		var x = document.createElement('span');
		x.className = 'material-symbols-outlined';
		x.textContent = 'close';
		t.appendChild(x);
		list.appendChild(t);
		input.value = '';
	}

	/* ── 대행사: 업체 고르기 → 담당자 · 연락처 · 주소 · 지역 자동, 회차 ──
	   [2026-11-12 v0.9] 고른 업체의 정보를 다른 칸에 글자로 채운다. CSS 로 안 된다. */
	function roundMsg() {
		var b = pickedBiz();
		var msg = $('#agCopyMsg');
		if (!copySrc) { setText('#agRound', '1회차'); msg.hidden = true; return; }
		msg.hidden = false;
		var same = !b || b.value === copySrc.biz;
		setText('#agRound', (same ? copySrc.round + 1 : 1) + '회차');
		msg.classList.toggle('ag-is-warn', !same);
		msg.textContent = same
			? '같은 업체(' + copySrc.bname + ')로 복제 — ' + copySrc.round + '회차 → ' + (copySrc.round + 1) + '회차 · 일정은 새 기본 일정으로 채웠습니다'
			: '다른 업체로 복제 — 1회차로 시작합니다. 주소·연락처·플레이스 링크는 새 업체(' + b.dataset.name + ') 정보로 바뀌니 확인하세요.';
	}
	function clearBiz() {
		setText('#agSumBiz', '—');
		setText('#agSumOwn', '업체를 고르면 자동');
		var sum = $('#agPickSum');
		sum.textContent = '업체를 고르세요';
		sum.classList.remove('ag-on');
	}
	function onBiz() {
		var b = pickedBiz();
		if (!b) { clearBiz(); return; }
		var own = b.dataset.owner;
		setText('#agSumBiz', b.dataset.name);
		setText('#agSumOwn', own ? own + ' (' + b.dataset.team + ') — 업체 담당자' : '미담당 — 알림이 관리자에게만 갑니다');
		var sum = $('#agPickSum');
		sum.textContent = b.dataset.name + ' · 담당자 ' + (own || '없음(미담당)') + ' — 업체 담당자로 자동';
		sum.classList.add('ag-on');
		form.phone.value = b.dataset.tel;
		form.zipCode.value = '0' + (4000 + num(b.value));       // 시안 우편번호(가짜)
		form.addr1.value = b.dataset.reg + ' ○○로 ***';
		if (typeNow() === '1') zoneFromAddress(b.dataset.reg);
		roundMsg();
	}

	/* ── 대행사: 복제 채우기 (#copy=<캠페인 id> 로 들어와도) ──
	   [2026-11-12 v0.9] 고른 캠페인 조건을 여러 칸에 채운다. 일정은 광고주 '이전 캠페인 불러오기'처럼 가져오지 않는다. CSS 로 안 된다. */
	function applyCopy(id) {
		copySrc = DATA.camps[id] || null;
		if (copySrc) {
			form.campaignName.value = copySrc.name;
			form.cnt.value = copySrc.n;
			form.rewardPoint.value = copySrc.reward.toLocaleString();
			$('input[name=rewards][value=' + (copySrc.reward > 0 ? 'Y' : 'N') + ']').checked = true;
			$('input[name=campaignType][value="' + copySrc.ty + '"]').checked = true;
			var code = DATA.chan[copySrc.ch];
			$$('input[name="channel[]"]').forEach(function (c) { c.checked = c.value === code; });
			// 담당자로 보는 중이어도 남의 업체를 강제로 고르지는 않는다(내 업체가 아니면 비워 둠)
			var target = $('input[name=agBiz][value="' + copySrc.biz + '"]');
			if (target && target.closest('.ag-bpick').offsetParent !== null) target.checked = true;
		}
		onType(false); onBiz(); calcUsePoint(); roundMsg();
	}

	document.addEventListener('change', function (e) {
		var t = e.target;
		if (t.name === 'agBiz') onBiz();
		else if (t.name === 'campaignType') onType(true);
		else if (t.name === 'rewards') calcUsePoint();
		else if (t.name === 'area[]') onArea(t);
		else if (/AbidanceType$/.test(t.name)) onAbidance(t);
		else if (t.id === 'agCopy') applyCopy(t.value);
		else if (t.name === 'ccStep') {
			// [2026-11-12 v0.9] 단계를 옮기면 본문을 맨 위로(광고주 setCreateStep 끝) — 스크롤 위치는 CSS 로 못 바꾼다
			$('.create-modal-body').scrollTop = 0;
		} else if (t.name === 'agRole') {
			// 담당자로 바꿨는데 고른 업체가 내 업체가 아니면 선택을 푼다
			var b = pickedBiz();
			if (b && b.closest('.ag-bpick').offsetParent === null) { b.checked = false; clearBiz(); }
		}
	});
	document.addEventListener('input', function (e) {
		var t = e.target;
		if (t.id === 'cnt' || t.id === 'rewardPoint') calcUsePoint();
		else if (t.id === 'agBizSearch') {
			// [2026-11-12 v0.9] 업체 글자 검색 — 적은 글자와 비교해 거르는 일이라 CSS 로 안 된다
			var q = t.value.trim().toLowerCase();
			$$('.ag-bpick').forEach(function (c) { c.classList.toggle('ag-out', !!q && c.dataset.q.toLowerCase().indexOf(q) < 0); });
		}
	});
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Enter' && e.target.matches && e.target.matches('.cc-form-group input[id^=add]')) { e.preventDefault(); tagAdd(e.target); }
	});

	// 버튼 — 시안이라 서버로 가는 것은 안내 한 줄로
	var MSG = {
		ccTempSave: '임시저장했습니다 · 캠페인 리스트 "작성 중"에서 이어서 씁니다',
		ccSubmit: '등록했습니다 · 심사 후 모집이 시작됩니다(시안 — 저장 없음)',
		ccZipBtn: '시안: 우편번호 검색은 광고주 화면 그대로 씁니다(서버 필요) · 업체를 고르면 업체 주소가 채워집니다',
		ccKwSearch: '시안: 연관키워드검색 창은 광고주 화면 그대로 씁니다(서버 필요)',
		agChargeReq: '관리자에게 충전 요청을 보냈습니다 · 충전되면 [캠페인 등록] 한 번이면 시작'
	};
	document.addEventListener('click', function (e) {
		var head = e.target.closest('.p-region-head');
		if (head) { sidoToggle(head); return; }
		var del = e.target.closest('.cc-keyword-tag > .material-symbols-outlined, .cc-hash-tag > .material-symbols-outlined');
		if (del) { del.parentNode.remove(); return; }
		var b = e.target.closest('button');
		if (!b) return;
		if (b.id === 'ccLoadBtn') { $('#agCopy').focus(); flash('대행사: 위 [복제해서 만들기]에서 지난 캠페인을 고르세요'); return; }
		var grp = b.closest('.cc-form-group');
		if (grp && b.textContent.trim() === '추가') { tagAdd($('input[id^=add]', grp)); return; }
		if (!MSG[b.id]) return;
		if ((b.id === 'ccSubmit' || b.id === 'ccTempSave') && !pickedBiz()) {
			flash('먼저 1단계 [업체 선택]에서 업체를 고르세요');
			$('#ccStep1').checked = true;
			return;
		}
		flash(MSG[b.id]);
	});

	var m = location.hash.match(/^#copy=([\w-]+)/);
	if (m && DATA.camps[m[1]]) { $('#agCopy').value = m[1]; applyCopy(m[1]); }
	else { onType(false); calcUsePoint(); }
})();
