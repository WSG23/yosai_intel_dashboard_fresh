(function(){
  function byId(id){ return document.getElementById(id); }
  function setState(area, state){
    var states = ['idle','hover','dragging','uploading','success','error'];
    states.forEach(function(s){ area.classList.remove('drag-drop-upload--'+s); });
    area.classList.add('drag-drop-upload--'+state);
  }

  document.addEventListener('DOMContentLoaded', function(){
    var area = byId('drag-drop-upload-area') || byId('drag-drop-upload-area');
    if(!area){
      area = document.querySelector('.drag-drop-upload');
    }
    if(!area){ return; }
    var input = area.querySelector('input[type="file"]');
    var cameraBtn = byId('drag-drop-upload-camera') || area.querySelector('[id$="-camera"]');

    area.addEventListener('dragover', function(e){
      e.preventDefault();
      setState(area, 'dragging');
    });
    area.addEventListener('dragleave', function(){
      setState(area, 'hover');
    });
    area.addEventListener('drop', function(){
      setState(area, 'uploading');
    });
    area.addEventListener('mouseover', function(){ setState(area, 'hover'); });
    area.addEventListener('mouseout', function(){ setState(area, 'idle'); });
    area.addEventListener('touchstart', function(){ setState(area, 'dragging'); });
    area.addEventListener('touchend', function(){ setState(area, 'idle'); });
    area.addEventListener('keyup', function(e){
      if(e.key === 'Enter' || e.key === ' '){
        if(input){ input.click(); }
      }
    });
    if(input){
      input.addEventListener('change', function(){ setState(area, 'uploading'); });
    }
    if(cameraBtn && input){
      cameraBtn.addEventListener('click', function(){
        input.setAttribute('capture', 'environment');
        input.click();
        setTimeout(function(){ input.removeAttribute('capture'); }, 1000);
      });
    }
  });
})();
