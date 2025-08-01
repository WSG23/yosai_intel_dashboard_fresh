from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path
from typing import List

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.protocols import UnicodeProcessorProtocol
from ..format_detector import FormatDetector

from .base import BaseReader
from .csv_reader import CSVReader
from .excel_reader import ExcelReader
from .fwf_reader import FWFReader
from .json_reader import JSONReader


class ArchiveReader(BaseReader):
    """Read archives containing a single supported file."""

    format_name = "archive"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.callback_controller = TrulyUnifiedCallbacks()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        path = Path(file_path)
        if not path.is_file():
            raise ArchiveReader.CannotParse("not a file")
        if path.suffix.lower() not in {".zip", ".tar", ".gz", ".tgz"}:
            raise ArchiveReader.CannotParse("extension mismatch")
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as zf:
                    names = [n for n in zf.namelist() if not n.endswith("/")]
                    if not names:
                        raise ArchiveReader.CannotParse("empty archive")
                    with zf.open(names[0]) as fh:
                        tmp_bytes = fh.read()
            elif tarfile.is_tarfile(path):
                with tarfile.open(path) as tf:
                    members = [m for m in tf.getmembers() if m.isfile()]
                    if not members:
                        raise ArchiveReader.CannotParse("empty archive")
                    fh = tf.extractfile(members[0])
                    assert fh is not None
                    tmp_bytes = fh.read()
            else:
                raise ArchiveReader.CannotParse("unsupported archive")
        except Exception as exc:
            raise ArchiveReader.CannotParse(str(exc)) from exc

        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_bytes(tmp_bytes)
        try:
            detector = FormatDetector(
                [
                    CSVReader(unicode_processor=self.unicode_processor),
                    JSONReader(unicode_processor=self.unicode_processor),
                    ExcelReader(unicode_processor=self.unicode_processor),
                    FWFReader(unicode_processor=self.unicode_processor),
                ],
                unicode_processor=self.unicode_processor,
            )
            df, _ = detector.detect_and_load(str(tmp_path), hint=hint)
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return df
