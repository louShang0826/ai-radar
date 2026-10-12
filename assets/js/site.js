/* Theme toggle (all pages). Theme is stored in localStorage "report-theme"; mermaid re-renders on switch. */
(function(){
  var root=document.documentElement,b=document.getElementById('themeToggle');
  if(b)b.onclick=function(){var t=root.dataset.theme==='dark'?'light':'dark';root.dataset.theme=t;
    try{localStorage.setItem('report-theme',t)}catch(e){}
    window.renderMermaid&&window.renderMermaid();
    document.dispatchEvent(new CustomEvent('themechange',{detail:t}));};
})();
