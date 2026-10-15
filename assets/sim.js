/* 시뮬레이션 공통: 주소 끝 #N → N차시 화면. 목록 링크와 차시 이동 단추를 만든다. */
(function () {
  var P = Array.prototype.slice.call(document.querySelectorAll('.panel')), nav = document.getElementById('nav');
  nav.innerHTML = P.map(function (p) { return '<a href="#' + p.dataset.lesson + '">' + p.dataset.lesson + '차시</a>'; }).join('');
  function go() {
    var h = location.hash.slice(1) || P[0].dataset.lesson, hit = false;
    P.forEach(function (p) { var on = p.dataset.lesson === h; p.classList.toggle('on', on); hit = hit || on; if (on && p.onShow) p.onShow(); });
    nav.querySelectorAll('a').forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + h); });
    var soon = document.getElementById('soon'); if (soon) soon.hidden = hit;
  }
  addEventListener('hashchange', go); go();
})();
