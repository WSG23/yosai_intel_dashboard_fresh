(function(){
  function updateNavbarTitle(){
    var header = document.querySelector('h1.text-primary');
    var navTitle = document.getElementById('navbar-title');
    if(navTitle && header){
      var text = header.textContent.trim();
      if(navTitle.textContent.trim() !== text){
        navTitle.textContent = text;
      }
    }
    document.querySelectorAll('.navbar-title').forEach(function(el){
      if(el.tagName.toLowerCase() === 'h5'){ el.remove(); }
    });
  }
  document.addEventListener('DOMContentLoaded', updateNavbarTitle);
  document.addEventListener('dash:page-load', updateNavbarTitle);
})();
