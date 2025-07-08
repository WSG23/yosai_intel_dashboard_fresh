#!/bin/bash
echo "🚀 Final Unicode Fix - Creating clean implementation..."

# 1. Remove corrupted file and create clean version
rm -f core/unicode_processor.py

cat > core/unicode_processor.py << 'PROCESSOR_EOF'
#!/usr/bin/env python3
import re, unicodedata, logging
from typing import Any

logger = logging.getLogger(__name__)
SURROGATE_RE = re.compile(r'[\uD800-\uDFFF]')

def sanitize_unicode_input(text: Any) -> str:
    if not isinstance(text, str):
        try: text = str(text)
        except: return ""
    try:
        text = unicodedata.normalize('NFKC', text)
        text = SURROGATE_RE.sub('', text)
        return text
    except:
        return ''.join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF))

class UnicodeProcessor:
    @staticmethod
    def safe_encode(value): return sanitize_unicode_input(value)
PROCESSOR_EOF

echo "✅ Created clean core/unicode_processor.py"

# 2. Ensure package structure
echo "# Core package" > core/__init__.py

# 3. Test basic import
python3 -c "from core.unicode_processor import sanitize_unicode_input; print('✅ Import works')"

# 4. Fix legacy imports causing AssertionError
python3 << 'PYTHON_EOF'
import re
from pathlib import Path

def safe_read(p):
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try: return Path(p).read_text(encoding=enc)
        except: continue
    return Path(p).read_text(encoding='utf-8', errors='replace')

def safe_write(p, content):
    clean = ''.join(ch for ch in content if not (0xD800 <= ord(ch) <= 0xDFFF))
    Path(p).write_text(clean, encoding='utf-8')

files = [
    'tools/complete_callback_cleanup.py', 'core/app_factory.py', 
    'components/device_verification.py', 'pages/file_upload.py'
]

for f in files:
    if Path(f).exists():
        try:
            content = safe_read(f)
            orig = content
            content = re.sub(r'from\s+core\.unicode_processor\s+import', 'from core.unicode import', content)
            content = re.sub(r'\bcore\.unicode_processor\.', 'core.unicode.', content)
            if content != orig:
                safe_write(f, content)
                print(f'✅ Fixed {f}')
        except Exception as e:
            print(f'⚠️ {f}: {e}')
PYTHON_EOF

echo "🎯 Testing final callback cleanup..."
