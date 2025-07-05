(function(){
  const STORE_ID = 'client-validation-store';
  const UPLOAD_ID = 'upload-data';

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
    const upload = document.getElementById(UPLOAD_ID);
    if(!upload){ return; }
    const input = upload.querySelector('input[type="file"]');
    if(!input){ return; }
    const maxBytes = parseInt(upload.getAttribute('data-max-size') || '0', 10);

    input.addEventListener('change', async function(e){
      e.stopImmediatePropagation();
      e.preventDefault();
      const files = Array.from(input.files);
      const {results, valid} = await validateFiles(files, maxBytes);
      updateStore(results);
      const dt = new DataTransfer();
      valid.forEach(f => dt.items.add(f));
      input.files = dt.files;
      if(valid.length){
        input.dispatchEvent(new Event('change', {bubbles:true}));
      }
    }, true);

  });
})();
