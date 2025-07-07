(function(){
  const AREA_ID = 'drag-drop-upload-area';
  const UPLOAD_ID = 'drag-drop-upload';
  const PROGRESS_ID = 'upload-progress';

  function byId(id){
    return document.getElementById(id);
  }

  function sanitizeFilename(name){
    if(!name){ return ''; }
    let norm;
    try{ norm = name.normalize('NFC'); }catch(_e){ norm = name; }
    let out = '';
    for(const ch of norm){
      const cp = ch.codePointAt(0);
      if(cp >= 32 && !(cp >= 0xD800 && cp <= 0xDFFF)){
        out += ch;
      }
    }
    return out;
  }

  function getConfig(upload){
    const attr = upload && upload.getAttribute('data-validator-config');
    if(attr){
      try{ return JSON.parse(attr); }catch(_e){}
    }
    return window.uploadValidatorConfig || {};
  }

  function validateFile(file, cfg){
    const ext = '.' + file.name.toLowerCase().split('.').pop();
    if(cfg.allowed_ext && Array.isArray(cfg.allowed_ext) &&
       !cfg.allowed_ext.includes(ext)){
      return 'unsupported_type';
    }
    const limit = (cfg.size_limits && cfg.size_limits[ext]) || cfg.max_size;
    if(limit && file.size > limit){ return 'too_large'; }
    return '';
  }

  function updateProgress(bar, val){
    if(!bar){ return; }
    const v = Math.min(100, Math.max(0, Math.round(val)));
    bar.setAttribute('value', v);
    bar.textContent = v + '%';
  }

  document.addEventListener('DOMContentLoaded', function(){
    const area = byId(AREA_ID);
    const upload = byId(UPLOAD_ID);
    if(!area || !upload){ return; }
    const input = upload.querySelector('input[type="file"]');
    const progress = byId(PROGRESS_ID);
    const status = byId(UPLOAD_ID + '-status');
    const previews = byId(UPLOAD_ID + '-previews');
    const cfg = getConfig(upload);

    window.uploadEnhancementLog = [];

    area.addEventListener('dragenter', e=>{
      e.preventDefault();
      area.classList.add('drag-drop-upload--hover');
    });
    area.addEventListener('dragover', e=>{
      e.preventDefault();
      area.classList.add('drag-drop-upload--dragging');
    });
    ['dragleave','drop'].forEach(evt=>{
      area.addEventListener(evt, ()=>{
        area.classList.remove('drag-drop-upload--hover','drag-drop-upload--dragging');
      });
    });

    area.addEventListener('keydown', e=>{
      if(e.key === 'Enter' || e.key === ' '){
        e.preventDefault();
        input && input.click();
      }
    });

    if(!input){ return; }

    input.addEventListener('change', async function(){
      const files = Array.from(input.files || []);
      const dt = new DataTransfer();
      let processed = 0;
      updateProgress(progress, 0);
      window.uploadEnhancementLog.length = 0;
      for(const file of files){
        const issue = validateFile(file, cfg);
        if(issue){
          window.uploadEnhancementLog.push({file: file.name, error: issue});
          continue;
        }
        const cleanName = sanitizeFilename(file.name);
        const newFile = cleanName !== file.name ? new File([file], cleanName, {type: file.type}) : file;
        dt.items.add(newFile);
        processed += 1;
        const val = processed / files.length * 100;
        updateProgress(progress, val);
        window.uploadEnhancementLog.push({file: newFile.name, progress: val});
      }
      input.files = dt.files;
      if(previews){
        previews.innerHTML = '';
        Array.from(dt.files).forEach(f => {
          const li = document.createElement('li');
          li.className = 'drag-drop-upload__preview';
          li.textContent = f.name;
          previews.appendChild(li);
        });
      }
      if(status){
        status.textContent = processed ? 'Ready to upload' : 'No valid files';
      }
      if(processed === files.length){ updateProgress(progress, 100); }
    });
  });
})();
