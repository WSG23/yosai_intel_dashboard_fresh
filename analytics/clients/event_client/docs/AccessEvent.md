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

# TODO update the JSON string below
json = "{}"
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


