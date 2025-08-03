# Configuration Reference

See [unified_config.md](unified_config.md) for details on regenerating the
protobuf schema and the `YosaiConfig` loader.

## App

| Field | Default | Env Var |
|-------|--------|--------|
| `title` | `Yōsai Intel Dashboard` | `` |
| `debug` | `True` | `` |
| `host` | `127.0.0.1` | `YOSAI_HOST` |
| `port` | `8050` | `YOSAI_PORT` |
| `secret_key` | `PydanticUndefined` | `SECRET_KEY` |
| `environment` | `development` | `` |

## Database

| Field | Default | Env Var |
|-------|--------|--------|
| `type` | `sqlite` | `` |
| `host` | `localhost` | `DB_HOST` |
| `port` | `5432` | `DB_PORT` |
| `name` | `yosai.db` | `DB_NAME` |
| `user` | `user` | `DB_USER` |
| `password` | `` | `DB_PASSWORD` |
| `url` | `` | `DATABASE_URL` |
| `connection_timeout` | `30` | `` |
| `initial_pool_size` | `10` | `` |
| `max_pool_size` | `20` | `` |
| `async_pool_min_size` | `10` | `` |
| `async_pool_max_size` | `20` | `` |
| `async_connection_timeout` | `30` | `` |
| `shrink_timeout` | `60` | `` |
| `shrink_interval` | `0` | `` |
| `use_intelligent_pool` | `False` | `` |

## Security

| Field | Default | Env Var |
|-------|--------|--------|
| `secret_key` | `` | `SECRET_KEY` |
| `session_timeout` | `3600` | `` |
| `session_timeout_by_role` | `{}` | `` |
| `cors_origins` | `[]` | `` |
| `csrf_enabled` | `True` | `` |
| `max_failed_attempts` | `5` | `` |
| `max_upload_mb` | `50` | `MAX_UPLOAD_MB` |
| `allowed_file_types` | `['.csv', '.json', '.xlsx']` | `` |

## Sample Files

| Field | Default | Env Var |
|-------|--------|--------|
| `csv_path` | `data/sample_data.csv` | `` |
| `json_path` | `data/sample_data.json` | `` |

## Analytics

| Field | Default | Env Var |
|-------|--------|--------|
| `cache_timeout_seconds` | `60` | `` |
| `max_records_per_query` | `500000` | `` |
| `enable_real_time` | `True` | `` |
| `batch_size` | `25000` | `` |
| `chunk_size` | `100000` | `ANALYTICS_CHUNK_SIZE` |
| `enable_chunked_analysis` | `True` | `` |
| `anomaly_detection_enabled` | `True` | `` |
| `ml_models_path` | `models/ml` | `` |
| `data_retention_days` | `30` | `` |
| `query_timeout_seconds` | `600` | `QUERY_TIMEOUT_SECONDS` |
| `force_full_dataset_analysis` | `True` | `` |
| `max_memory_mb` | `500` | `ANALYTICS_MAX_MEMORY_MB` |
| `max_display_rows` | `10000` | `` |

## Monitoring

| Field | Default | Env Var |
|-------|--------|--------|
| `health_check_enabled` | `True` | `` |
| `metrics_enabled` | `True` | `` |
| `health_check_interval` | `30` | `` |
| `performance_monitoring` | `False` | `` |
| `error_reporting_enabled` | `True` | `` |
| `sentry_dsn` | `None` | `` |
| `log_retention_days` | `30` | `` |

## Cache

| Field | Default | Env Var |
|-------|--------|--------|
| `enabled` | `True` | `` |
| `ttl` | `3600` | `` |
| `max_size` | `1000` | `` |
| `redis_url` | `None` | `` |
| `use_memory_cache` | `True` | `` |
| `use_redis` | `False` | `` |
| `prefix` | `yosai_` | `` |
| `host` | `localhost` | `CACHE_HOST` |
| `port` | `6379` | `CACHE_PORT` |

## Uploads

| Field | Default | Env Var |
|-------|--------|--------|
| `folder` | `/tmp/uploads` | `UPLOAD_FOLDER` |
| `max_file_size_mb` | `16` | `MAX_FILE_SIZE_MB` |

## Secret Validation

| Field | Default | Env Var |
|-------|--------|--------|
| `severity` | `low` | `` |
