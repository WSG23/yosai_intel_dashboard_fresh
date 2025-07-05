(function(){
  var source;
  window.startUploadProgress = function(taskId){
    if(!taskId){return;}
    if(source){source.close();}
    var progressBar = document.getElementById('upload-progress');
    source = new EventSource('/upload/progress/' + taskId);
    source.onmessage = function(e){
      var val = parseInt(e.data);
      if(progressBar){
        progressBar.setAttribute('value', val);
        progressBar.textContent = val + '%';
      }
      if(val >= 100){
        source.close();
        var btn = document.getElementById('progress-done-trigger');
        if(btn){btn.click();}
      }
    };
  };
})();
