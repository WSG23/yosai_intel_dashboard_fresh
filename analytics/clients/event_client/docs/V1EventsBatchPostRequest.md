# V1EventsBatchPostRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**events** | [**List[AccessEvent]**](AccessEvent.md) |  | [optional] 

## Example

```python
from openapi_client.models.v1_events_batch_post_request import V1EventsBatchPostRequest

# TODO update the JSON string below
json = "{}"
# create an instance of V1EventsBatchPostRequest from a JSON string
v1_events_batch_post_request_instance = V1EventsBatchPostRequest.from_json(json)
# print the JSON string representation of the object
print(V1EventsBatchPostRequest.to_json())

# convert the object into a dict
v1_events_batch_post_request_dict = v1_events_batch_post_request_instance.to_dict()
# create an instance of V1EventsBatchPostRequest from a dict
v1_events_batch_post_request_from_dict = V1EventsBatchPostRequest.from_dict(v1_events_batch_post_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


