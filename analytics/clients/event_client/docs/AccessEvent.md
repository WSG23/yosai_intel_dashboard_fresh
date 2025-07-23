# AccessEvent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **str** |  | 
**timestamp** | **datetime** |  | 
**person_id** | **str** |  | [optional] 
**door_id** | **str** |  | [optional] 
**badge_id** | **str** |  | [optional] 
**access_result** | **str** |  | 
**badge_status** | **str** |  | [optional] 
**door_held_open_time** | **float** |  | [optional] 
**entry_without_badge** | **bool** |  | [optional] 
**device_status** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.access_event import AccessEvent

# Example JSON describing an access event
json = "{\n  \"event_id\": \"12345\",\n  \"timestamp\": \"2024-05-01T12:34:56Z\",\n  \"person_id\": \"user-42\",\n  \"door_id\": \"door-1\",\n  \"badge_id\": \"badge-100\",\n  \"access_result\": \"GRANTED\",\n  \"badge_status\": \"ACTIVE\",\n  \"door_held_open_time\": 0.0,\n  \"entry_without_badge\": false,\n  \"device_status\": \"ONLINE\"\n}"
# create an instance of AccessEvent from a JSON string
access_event_instance = AccessEvent.from_json(json)
# print the JSON string representation of the object
print(AccessEvent.to_json())

# convert the object into a dict
access_event_dict = access_event_instance.to_dict()
# create an instance of AccessEvent from a dict
access_event_from_dict = AccessEvent.from_dict(access_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


