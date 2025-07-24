from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppConfig(_message.Message):
    __slots__ = ["debug", "environment", "host", "port", "secret_key", "title"]
    DEBUG_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    debug: bool
    environment: str
    host: str
    port: int
    secret_key: str
    title: str
    def __init__(self, title: _Optional[str] = ..., debug: bool = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., secret_key: _Optional[str] = ..., environment: _Optional[str] = ...) -> None: ...

class DatabaseConfig(_message.Message):
    __slots__ = ["async_connection_timeout", "async_pool_max_size", "async_pool_min_size", "connection_timeout", "host", "initial_pool_size", "max_pool_size", "name", "password", "port", "shrink_timeout", "type", "url", "use_intelligent_pool", "user"]
    ASYNC_CONNECTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ASYNC_POOL_MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    ASYNC_POOL_MIN_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    INITIAL_POOL_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_POOL_SIZE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SHRINK_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    USE_INTELLIGENT_POOL_FIELD_NUMBER: _ClassVar[int]
    async_connection_timeout: int
    async_pool_max_size: int
    async_pool_min_size: int
    connection_timeout: int
    host: str
    initial_pool_size: int
    max_pool_size: int
    name: str
    password: str
    port: int
    shrink_timeout: int
    type: str
    url: str
    use_intelligent_pool: bool
    user: str
    def __init__(self, type: _Optional[str] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., name: _Optional[str] = ..., user: _Optional[str] = ..., password: _Optional[str] = ..., url: _Optional[str] = ..., connection_timeout: _Optional[int] = ..., initial_pool_size: _Optional[int] = ..., max_pool_size: _Optional[int] = ..., async_pool_min_size: _Optional[int] = ..., async_pool_max_size: _Optional[int] = ..., async_connection_timeout: _Optional[int] = ..., shrink_timeout: _Optional[int] = ..., use_intelligent_pool: bool = ...) -> None: ...

class SecurityConfig(_message.Message):
    __slots__ = ["allowed_file_types", "cors_origins", "csrf_enabled", "max_failed_attempts", "max_upload_mb", "secret_key", "session_timeout", "session_timeout_by_role"]
    class SessionTimeoutByRoleEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    ALLOWED_FILE_TYPES_FIELD_NUMBER: _ClassVar[int]
    CORS_ORIGINS_FIELD_NUMBER: _ClassVar[int]
    CSRF_ENABLED_FIELD_NUMBER: _ClassVar[int]
    MAX_FAILED_ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    MAX_UPLOAD_MB_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    SESSION_TIMEOUT_BY_ROLE_FIELD_NUMBER: _ClassVar[int]
    SESSION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    allowed_file_types: _containers.RepeatedScalarFieldContainer[str]
    cors_origins: _containers.RepeatedScalarFieldContainer[str]
    csrf_enabled: bool
    max_failed_attempts: int
    max_upload_mb: int
    secret_key: str
    session_timeout: int
    session_timeout_by_role: _containers.ScalarMap[str, int]
    def __init__(self, secret_key: _Optional[str] = ..., session_timeout: _Optional[int] = ..., session_timeout_by_role: _Optional[_Mapping[str, int]] = ..., cors_origins: _Optional[_Iterable[str]] = ..., csrf_enabled: bool = ..., max_failed_attempts: _Optional[int] = ..., max_upload_mb: _Optional[int] = ..., allowed_file_types: _Optional[_Iterable[str]] = ...) -> None: ...

class YosaiConfig(_message.Message):
    __slots__ = ["app", "database", "environment", "security"]
    APP_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECURITY_FIELD_NUMBER: _ClassVar[int]
    app: AppConfig
    database: DatabaseConfig
    environment: str
    security: SecurityConfig
    def __init__(self, app: _Optional[_Union[AppConfig, _Mapping]] = ..., database: _Optional[_Union[DatabaseConfig, _Mapping]] = ..., security: _Optional[_Union[SecurityConfig, _Mapping]] = ..., environment: _Optional[str] = ...) -> None: ...
