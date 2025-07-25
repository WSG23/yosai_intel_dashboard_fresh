# AccessEvent Schema

Namespace: `com.yosai.access`

| Field | Type | Default |
|-------|------|---------|
| `event_id` | `string` | `` |
| `timestamp` | `long (timestamp-millis)` | `` |
| `person_id` | `null | string` | `null` |
| `door_id` | `null | string` | `null` |
| `badge_id` | `null | string` | `null` |
| `access_result` | `string` | `` |
| `badge_status` | `null | string` | `null` |
| `door_held_open_time` | `null | double` | `0.0` |
| `entry_without_badge` | `null | boolean` | `false` |
| `device_status` | `null | string` | `"normal"` |
