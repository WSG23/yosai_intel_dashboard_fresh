#!/usr/bin/env python3
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
