(function(){
  const STORE_ID = 'client-validation-store';
  const UPLOAD_ID = 'upload-data';

  function byId(id){
    return document.getElementById(id);
  }

  function bytesToHex(bytes){
    return Array.from(bytes).map(b=>b.toString(16).padStart(2,'0')).join('');
  }

  function checkMagic(file){
    return new Promise((resolve)=>{
      const reader = new FileReader();
      reader.onloadend = function(){
        const arr = new Uint8Array(reader.result || []);
        const hex = bytesToHex(arr.slice(0,4));
        let ok = false;
        if(hex.startsWith('504b0304')){ // zip based XLSX
          ok = true;
        } else if(hex.startsWith('d0cf11e0')){ // legacy XLS
          ok = true;
        } else {
          const text = new TextDecoder('utf-8').decode(arr.slice(0,4));
          ok = /^[\x20-\x7E\r\n]+$/.test(text);
        }
        resolve(ok);
      };
      reader.onerror = function(){ resolve(false); };
      reader.readAsArrayBuffer(file.slice(0,8));
    });
  }

  async function validateFiles(files, maxBytes){
    const results = [];
    const valid = [];
    const seen = new Set();
    for(const file of files){
      const issues = [];
      if(maxBytes && file.size > maxBytes){ issues.push('too_large'); }
      if(seen.has(file.name)){ issues.push('duplicate'); }
      seen.add(file.name);
      const magicOk = await checkMagic(file);
      if(!magicOk){ issues.push('bad_magic'); }
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
    const maxBytes = parseInt(upload.getAttribute('data-max-size') || '0', 10);

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
      const {results, valid} = await validateFiles(files, maxBytes);
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
