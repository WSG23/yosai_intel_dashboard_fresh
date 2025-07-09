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
