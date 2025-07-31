(function(){
  var lastFocused = null;

  document.addEventListener('click', function(e){
    if(e.target.matches('#verify-columns-btn-simple, #classify-devices-btn,' +
                         ' #column-verify-confirm, #device-verify-confirm')){
      lastFocused = e.target;
    }
  }, true);

  document.addEventListener('shown.bs.modal', function(e){
    var first = e.target.querySelector('input, select, textarea, button');
    if(first){ first.focus(); }
  });

  document.addEventListener('hidden.bs.modal', function(){
    if(lastFocused){ lastFocused.focus(); }
  });
})();
