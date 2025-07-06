(function(){
  const STORE_ID = 'client-validation-store';
  const UPLOAD_ID = 'drag-drop-upload';

  function byId(id){
    return document.getElementById(id);
  }

  function bytesToHex(bytes){
    return Array.from(bytes).map(b=>b.toString(16).padStart(2,'0')).join('');
  }

  function getConfig(upload){
    const attr = upload.getAttribute('data-validator-config');
    if(attr){
      try{ return JSON.parse(attr); }catch(e){ }
    }
    if(window.uploadValidatorConfig){ return window.uploadValidatorConfig; }
    return {};
  }

  function checkMagic(file, expected){
    if(!expected || !expected.length){ return Promise.resolve(true); }
    const maxLen = Math.max.apply(null, expected.map(h=>h.length/2));
    return new Promise((resolve)=>{
      const reader = new FileReader();
      reader.onloadend = function(){
        const arr = new Uint8Array(reader.result || []);
        const hex = bytesToHex(arr.slice(0,maxLen));
        const ok = expected.some(h => hex.startsWith(h.toLowerCase()));
        resolve(ok);
      };
      reader.onerror = function(){ resolve(false); };
      reader.readAsArrayBuffer(file.slice(0,maxLen));
    });
  }

  async function validateFiles(files, config){
    const results = [];
    const valid = [];
    const seen = new Set();
    for(const file of files){
      const issues = [];
      const ext = file.name.toLowerCase().split('.').pop();
      const dotExt = '.' + ext;
      if(config.allowed_ext && config.allowed_ext.length && !config.allowed_ext.includes(dotExt)){
        issues.push('unsupported_type');
      }
      const limit = (config.size_limits && config.size_limits[dotExt]) || config.max_size;
      if(limit && file.size > limit){ issues.push('too_large'); }
      if(config.track_duplicates !== false){
        if(seen.has(file.name)){ issues.push('duplicate'); }
        seen.add(file.name);
      }
      const magicOk = await checkMagic(file, (config.magic_numbers && config.magic_numbers[dotExt]) || []);
      if(!magicOk){ issues.push('bad_magic'); }
      if(Array.isArray(config.hooks)){
        for(const fnName of config.hooks){
          const fn = window[fnName];
          if(typeof fn === 'function'){
            try{
              const res = await fn(file);
              if(res === false){ issues.push('custom_error'); }
              else if(typeof res === 'string' && res){ issues.push(res); }
            }catch(err){ issues.push('custom_error'); }
          }
        }
      }
      results.push({filename: file.name, valid: issues.length===0, issues: issues});
      if(issues.length===0){ valid.push(file); }
    }
    return {results, valid};
  }

  function updateStore(data){
    const store = document.getElementById(STORE_ID);
    if(store){
      const setter = store._dashprivate_setProps || store.setProps;
      if(typeof setter === 'function'){
        setter.call(store, {data});
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    const upload = byId(UPLOAD_ID);
    if(!upload){ return; }
    const area = byId(`${UPLOAD_ID}-area`);
    const previewList = byId(`${UPLOAD_ID}-previews`);
    const cameraBtn = byId(`${UPLOAD_ID}-camera`);
    const input = upload.querySelector('input[type="file"]');
    if(!input){ return; }
    const config = getConfig(upload);

    if(area){
      ['dragenter','dragover'].forEach(evt=>{
        area.addEventListener(evt, e=>{
          e.preventDefault();
          area.classList.add('drag-drop-upload--hover');
          if(evt==='dragover'){ area.classList.add('drag-drop-upload--dragging'); }
        });
      });
      ['dragleave','drop'].forEach(evt=>{
        area.addEventListener(evt, e=>{
          area.classList.remove('drag-drop-upload--hover','drag-drop-upload--dragging');
        });
      });
    }

    if(cameraBtn){
      cameraBtn.addEventListener('click', ()=>{
        const camInput = document.createElement('input');
        camInput.type = 'file';
        camInput.accept = 'image/*';
        camInput.capture = 'environment';
        camInput.addEventListener('change', ()=>{
          if(camInput.files.length){
            const dt = new DataTransfer();
            Array.from(input.files).forEach(f=>dt.items.add(f));
            Array.from(camInput.files).forEach(f=>dt.items.add(f));
            input.files = dt.files;
            input.dispatchEvent(new Event('change', {bubbles:true}));
          }
        });
        camInput.click();
      });
    }

    input.addEventListener('change', async function(e){
      e.stopImmediatePropagation();
      e.preventDefault();
      if(area){ area.classList.add('drag-drop-upload--uploading'); }
      const files = Array.from(input.files);
      const {results, valid} = await validateFiles(files, config);
      updateStore(results);
      const dt = new DataTransfer();
      valid.forEach(f => dt.items.add(f));
      input.files = dt.files;
      if(previewList){
        previewList.innerHTML = '';
        valid.forEach(file => {
          const li = document.createElement('li');
          li.className = 'drag-drop-upload__preview';
          if(file.type.startsWith('image/')){
            const reader = new FileReader();
            reader.onload = () => {
              const img = document.createElement('img');
              img.src = reader.result;
              img.alt = file.name;
              li.appendChild(img);
            };
            reader.readAsDataURL(file);
          } else {
            const icon = document.createElement('span');
            icon.className = 'fa fa-file';
            icon.setAttribute('aria-hidden','true');
            li.appendChild(icon);
          }
          previewList.appendChild(li);
        });
      }
      if(valid.length){
        input.dispatchEvent(new Event('change', {bubbles:true}));
      }
      if(area){ setTimeout(()=>area.classList.remove('drag-drop-upload--uploading'),500); }
    }, true);

  });
})();
