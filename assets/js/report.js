/* TOC highlight, progress, image zoom, table row filters (report pages). Theme toggle lives in site.js. */

(function(){
  var root=document.documentElement;
  var toc=document.getElementById('toc'),tg=document.getElementById('tocToggle');
  tg.onclick=function(){var o=toc.dataset.open!=='true';toc.dataset.open=o;tg.setAttribute('aria-expanded',o)};
  var links=[].slice.call(document.querySelectorAll('#tocBody a')),map={};
  links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a; a.addEventListener('click',function(){if(innerWidth<1180){toc.dataset.open=false}})});
  var heads=[].slice.call(document.querySelectorAll('#article h2[id],#article h3[id]'));
  var prog=document.getElementById('progress'),tp=document.getElementById('tocProg'),body=document.getElementById('tocBody');
  function onScroll(){
    var y=scrollY+180,cur=null;
    for(var i=0;i<heads.length;i++){if(heads[i].getBoundingClientRect().top+scrollY<=y)cur=heads[i];else break}
    links.forEach(function(a){a.classList.remove('active')});
    if(cur&&map[cur.id]){var a=map[cur.id];a.classList.add('active');
      var p=a.closest('ul').parentElement; if(p&&p.tagName==='LI'){var pa=p.querySelector(':scope>a');pa&&pa.classList.add('active')}
      var ar=a.getBoundingClientRect(),br=body.getBoundingClientRect(); if(ar.top<br.top+20||ar.bottom>br.bottom-20)body.scrollTop+=ar.top-br.top-body.clientHeight/2}
    var h=document.documentElement.scrollHeight-innerHeight,pc=h>0?Math.min(100,Math.round(scrollY/h*100)):0;
    prog.style.width=pc+'%';tp.textContent=pc+'%';
  }
  addEventListener('scroll',onScroll,{passive:true});addEventListener('resize',onScroll);onScroll();
  var z=document.getElementById('imgZoom'),zi=document.getElementById('imgZoomImg');
  document.querySelectorAll('[data-zoom]').forEach(function(im){im.addEventListener('click',function(){zi.src=im.src;z.classList.add('open')})});
  z.onclick=function(){z.classList.remove('open')};
  addEventListener('keydown',function(e){if(e.key==='Escape')z.classList.remove('open')});
})();

document.querySelectorAll('.row-filter').forEach(function(bar){var box=bar.nextElementSibling,tb=box&&box.querySelector('table');if(!tb)return;
bar.addEventListener('click',function(e){var b=e.target.closest('.rf-btn');if(!b)return;bar.querySelectorAll('.rf-btn').forEach(function(x){x.classList.toggle('on',x===b)});tb.dataset.f=b.dataset.f;box.scrollTop=0})});
