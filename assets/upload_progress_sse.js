(function(){
  var source;
  var lastVal = -1;
  window.uploadProgressLog = [];
  window.startUploadProgress = function(taskId){
    if(!taskId){return;}
    if(source){source.close();}
    var progressBar = document.getElementById('upload-progress');
    source = new EventSource('/upload/progress/' + taskId);
    source.onmessage = function(e){
      var val = parseInt(e.data);
      window.uploadProgressLog.push(val);
      if(progressBar && val !== lastVal){
        progressBar.setAttribute('value', val);
        progressBar.textContent = val + '%';
        lastVal = val;
      }
      if(val >= 100){
        source.close();
      }
    };
  };
})();
