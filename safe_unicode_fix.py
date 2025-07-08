#!/usr/bin/env python3
import re
import unicodedata
from pathlib import Path

def clean_surrogate_chars(text: str) -> str:
    """Remove surrogate characters from text."""
    cleaned = ''
    for char in text:
        if not (0xD800 <= ord(char) <= 0xDFFF):
            cleaned += char
    return cleaned

# 1. Create missing core/unicode_processor.py
unicode_content = '''#!/usr/bin/env python3
import re, unicodedata, logging
from typing import Any

logger = logging.getLogger(__name__)
_SURROGATE_RE = re.compile(r'[\\uD800-\\uDFFF]')
_CONTROL_RE = re.compile(r'[\\x00-\\x1f\\x7f-\\x9f]')

def sanitize_unicode_input(text: Any) -> str:
    if not isinstance(text, str):
        try: text = str(text)
        except: return ""
    try:
        text = unicodedata.normalize('NFKC', text)
        text = _SURROGATE_RE.sub('', text)
        text = _CONTROL_RE.sub('', text)
        return text
    except:
        return ''.join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF or ord(ch) < 32 or ord(ch) == 0x7F))

class UnicodeProcessor:
    @staticmethod
    def safe_decode(data: bytes, encoding: str = 'utf-8') -> str:
        try: return data.decode(encoding)
        except: return data.decode('latin-1', errors='replace')
    @staticmethod
    def safe_encode(value: Any) -> str: return sanitize_unicode_input(value)
'''

Path('core/unicode_processor.py').write_text(unicode_content, encoding='utf-8')
print("✅ Created core/unicode_processor.py")

# 2. Create tools/robust_file_reader.py
reader_content = '''#!/usr/bin/env python3
from pathlib import Path
from typing import Union
try: import chardet
except: chardet = None

class RobustFileReader:
    ENCODING_PRIORITY = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    @staticmethod
    def read_text_with_detection(file_path: Union[str, Path]) -> str:
        path = Path(file_path)
        raw_bytes = path.read_bytes()
        
        if chardet:
            detected = chardet.detect(raw_bytes)
            if detected.get("encoding"):
                try: return raw_bytes.decode(detected["encoding"])
                except: pass
        
        for encoding in RobustFileReader.ENCODING_PRIORITY:
            try: return raw_bytes.decode(encoding)
            except: continue
        return raw_bytes.decode('utf-8', errors='replace')

def safe_read_text(file_path: Union[str, Path]) -> str:
    return RobustFileReader.read_text_with_detection(file_path)
'''

Path('tools/robust_file_reader.py').write_text(reader_content, encoding='utf-8')
print("✅ Created tools/robust_file_reader.py")

# 3. Fix tools/unicode_cleanup.py safely
path = Path('tools/unicode_cleanup.py')
if path.exists():
    raw_content = path.read_bytes().decode('latin-1')
    content = clean_surrogate_chars(raw_content)  # Clean surrogates first!
    
    if 'from .robust_file_reader import safe_read_text' not in content:
        content = content.replace('from pathlib import Path', 'from pathlib import Path\nfrom .robust_file_reader import safe_read_text')
    
    content = re.sub(r'text = path\.read_text\(encoding="utf-8"\)', 'text = safe_read_text(path)', content)
    content = re.sub(r'text = path\.read_text\(encoding="utf-8", errors="replace"\)', 'text = safe_read_text(path)', content)
    
    path.write_text(content, encoding='utf-8')
    print("✅ Fixed tools/unicode_cleanup.py")

print("🎉 All fixes applied safely!")
