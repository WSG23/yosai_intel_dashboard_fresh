import sys
import types

import pytest

import validation.security_validator as sv

# ensure globals required by SecurityValidator are present
sv.redis_client = None
sv.rate_limit = 1
sv.window_seconds = 60

SecurityValidator = sv.SecurityValidator
ValidationError = sv.ValidationError


def _stub_magic(mime: str):
    fake_magic = types.SimpleNamespace(from_buffer=lambda buf, mime=True: mime)
    sys.modules['magic'] = fake_magic


def _stub_clamd(result):
    class _FakeClamd:
        def instream(self, stream):
            return {'stream': result}
    fake_clamd = types.SimpleNamespace(ClamdNetworkSocket=lambda: _FakeClamd())
    sys.modules['clamd'] = fake_clamd


def test_eicar_sample_rejected():
    eicar = (
        b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    )
    _stub_magic('text/plain')
    _stub_clamd(('FOUND', 'Eicar-Test-Signature'))
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_file_meta('eicar.txt', eicar)


def test_wrong_mime_detected():
    _stub_magic('image/png')
    _stub_clamd(('OK', None))
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_file_meta('data.csv', b'col1,col2')
