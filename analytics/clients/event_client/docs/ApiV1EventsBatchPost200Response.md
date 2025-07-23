# ApiV1EventsBatchPost200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[EventResponse]**](EventResponse.md) |  | [optional] 

## Example

```python
from openapi_client.models.api_v1_events_batch_post200_response import ApiV1EventsBatchPost200Response

# Example batch response returned by the server
json = "{\n  \"results\": [\n    {\n      \"event_id\": \"12345\",\n      \"status\": \"accepted\"\n    },\n    {\n      \"event_id\": \"67890\",\n      \"status\": \"rejected\"\n    }\n  ]\n}"
# create an instance of ApiV1EventsBatchPost200Response from a JSON string
api_v1_events_batch_post200_response_instance = ApiV1EventsBatchPost200Response.from_json(json)
# print the JSON string representation of the object
print(ApiV1EventsBatchPost200Response.to_json())

# convert the object into a dict
api_v1_events_batch_post200_response_dict = api_v1_events_batch_post200_response_instance.to_dict()
# create an instance of ApiV1EventsBatchPost200Response from a dict
api_v1_events_batch_post200_response_from_dict = ApiV1EventsBatchPost200Response.from_dict(api_v1_events_batch_post200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


