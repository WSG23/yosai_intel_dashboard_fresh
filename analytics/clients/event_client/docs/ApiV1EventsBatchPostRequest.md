# ApiV1EventsBatchPostRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**events** | [**List[AccessEvent]**](AccessEvent.md) |  | [optional] 

## Example

```python
from openapi_client.models.api_v1_events_batch_post_request import ApiV1EventsBatchPostRequest

# Example request payload for the batch endpoint
json = "{\n  \"events\": [\n    {\n      \"event_id\": \"12345\",\n      \"timestamp\": \"2024-05-01T12:34:56Z\",\n      \"access_result\": \"GRANTED\"\n    }\n  ]\n}"
# create an instance of ApiV1EventsBatchPostRequest from a JSON string
api_v1_events_batch_post_request_instance = ApiV1EventsBatchPostRequest.from_json(json)
# print the JSON string representation of the object
print(ApiV1EventsBatchPostRequest.to_json())

# convert the object into a dict
api_v1_events_batch_post_request_dict = api_v1_events_batch_post_request_instance.to_dict()
# create an instance of ApiV1EventsBatchPostRequest from a dict
api_v1_events_batch_post_request_from_dict = ApiV1EventsBatchPostRequest.from_dict(api_v1_events_batch_post_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


