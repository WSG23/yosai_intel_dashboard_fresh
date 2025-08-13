# Audit Logging

Admin actions are captured and persisted to the centralized Elasticsearch cluster.
Each log entry includes the following fields:

- `user`: authenticated user identifier
- `timestamp`: time of the action (UTC)
- `action`: HTTP method and path
- `outcome`: `success` for 2xx/3xx responses or `failure` for 4xx/5xx responses

## Querying Logs

Use the following example queries in Kibana or the Elasticsearch API:

```sh
# Retrieve the last 50 admin actions
GET audit/_search
{
  "size": 50,
  "sort": [{"timestamp": "desc"}]
}

# Count failed admin actions
GET audit/_count
{
  "query": {"match": {"outcome": "failure"}}
}
```

## Dashboards

Create a dashboard with:

- **Successful vs Failed Actions**: pie chart on the `outcome` field.
- **Top Admin Users**: bar chart aggregating by `user`.
- **Activity Over Time**: line chart on `timestamp` with interval set to `@timestamp`.

These visualizations provide operations teams with insight into administrative activity and potential misuse.
