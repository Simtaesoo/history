/* 목록 페이지 그리기. <main id="app" data-book="m1"> 이면 과목 목록, data-book이 없으면 첫 화면.
   자료가 만들어지면 catalog.js의 FILES에 적은 것만 링크로 바뀝니다. */
(function () {
  var C = window.CATALOG, S = window.STANDARDS || {}, F = window.FILES || {}, SITE = window.SITE || {};
  var app = document.getElementById('app'), id = app.dataset.book, root = id ? '../' : '';
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function made(key, kind, n) { var f = F[key]; return !!(f && f[kind] && f[kind].indexOf(n) > -1); }
  function chip(href, label) { return href ? '<a class="k" href="' + esc(href) + '">' + label + '</a>' : '<span class="k">' + label + '</span>'; }
  function lessonKit(book, u, n, shared) {
    var b = book, d = u.dir, k = n;
    if (shared) { var p = shared.split('/'); b = p[0]; d = p[1]; k = +p[2]; }
    var key = b + '/' + d, base = root + key + '/';
    return chip(made(key, 'slides', k) && base + 'slides' + k + '.html', '슬라이드') +
           chip(made(key, 'sim', k) && base + 'sim.html#' + k, '시뮬레이션');
  }
  function count(book) {
    var all = 0, done = 0;
    book.units.forEach(function (u) { u.lessons.forEach(function (l, i) {
      all++; var key = book.id + '/' + u.dir, k = i + 1;
      if (l[2]) { var p = l[2].split('/'); key = p[0] + '/' + p[1]; k = +p[2]; }
      if (made(key, 'slides', k)) done++;
    }); });
    return [done, all];
  }
  var foot = '<p class="foot">' + esc(SITE.curriculum) + ' · 사진은 퍼블릭 도메인 자료를 우선 사용하며 장마다 출처를 적었습니다.' + (SITE.author ? ' · ' + esc(SITE.author) : '') + '</p>';

  if (!id) {
    document.title = SITE.name;
    var levels = ['중학교', '고등학교'];
    app.innerHTML = '<header><h1>' + esc(SITE.name) + '</h1><p class="lead">2022 개정 교육과정 중·고등 역사. 차시마다 수업 슬라이드와 시뮬레이션, 단원마다 학습지와 게임.</p></header>' +
      levels.map(function (lv) {
        return '<section class="level"><h2>' + lv + '</h2><div class="books">' + C.filter(function (b) { return b.level === lv; }).map(function (b) {
          var c = count(b);
          return '<a class="book" href="' + b.id + '/index.html"><span class="eyebrow">' + esc(b.note) + '</span><b>' + esc(b.book) + '</b><small>' + b.units.length + '개 단원 · ' + c[1] + '차시 · 슬라이드 ' + c[0] + '개 완성</small><span class="meter"><i style="width:' + (c[0] / c[1] * 100).toFixed(1) + '%"></i></span></a>';
        }).join('') + '</div></section>';
      }).join('') + foot;
    return;
  }

  var book = C.filter(function (b) { return b.id === id; })[0];
  document.title = book.book + ' · ' + SITE.name;
  app.innerHTML = '<header><a class="crumb" href="../index.html">← ' + esc(SITE.name) + '</a><p class="eyebrow" style="margin-top:14px">' + book.level + ' · ' + esc(book.note) + '</p><h1>' + esc(book.book) + '</h1></header>' +
    book.units.map(function (u) {
      var key = id + '/' + u.dir, f = F[key] || {}, last = '';
      var rows = u.lessons.map(function (l, i) {
        var std = l[1] !== last ? '<li class="std"><code>[' + l[1] + ']</code> ' + esc(S[l[1]] || '') + '</li>' : '';
        last = l[1];
        return std + '<li class="ls"><span class="n">' + (i + 1) + '</span><span class="t">' + esc(l[0]) + '</span><span class="kit">' + lessonKit(id, u, i + 1, l[2]) + '</span></li>';
      }).join('');
      return '<section class="unit" id="u' + u.no + '"><h2><span>' + u.no + '</span>' + esc(u.title) + '</h2><div class="ukit">' +
        chip(f.ws && u.dir + '/worksheet.html', '학습지') +
        chip(f.game && u.dir + '/' + f.game.href, f.game ? '게임 · ' + esc(f.game.title) : '게임') +
        '</div><ol>' + rows + '</ol></section>';
    }).join('') + foot;
})();
