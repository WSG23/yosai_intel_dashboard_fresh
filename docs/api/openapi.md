# Yōsai Intel Dashboard API
Physical security intelligence and access control API.

# Authentication
Use Bearer token (JWT) for inter-service communication and require an
`X-CSRF-Token` header on state-changing requests.

# Versioning
API version is included in the URL path (e.g., /v2/events).


## Version: 2.0.0

### Terms of service
https://yosai.com/terms

**Contact information:**  
api-support@yosai.com  

**License:** [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)

### /events

#### GET
##### Summary:

List access events

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Successful response |
| 400 |  |
| 404 |  |

### Models


#### AccessEvent

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| door_id | string |  | Yes |
| event_id | string |  | No |
| person_id | string |  | Yes |
| result | string |  | No |
| timestamp | dateTime |  | Yes |

#### AnalyticsUpdate

Generic analytics update broadcast over WebSocket.

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| AnalyticsUpdate | object | Generic analytics update broadcast over WebSocket. |  |

#### Error

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| code | string |  | Yes |
| details | object |  | No |
| message | string |  | Yes |

#### EventListResponse

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| events | [ [AccessEvent](#accessevent) ] |  | No |

#### WebhookAlertPayload

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| message | string |  | Yes |