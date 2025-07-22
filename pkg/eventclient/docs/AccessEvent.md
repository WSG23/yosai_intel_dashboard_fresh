# AccessEvent

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**EventId** | **string** |  | 
**Timestamp** | **time.Time** |  | 
**PersonId** | Pointer to **NullableString** |  | [optional] 
**DoorId** | Pointer to **NullableString** |  | [optional] 
**BadgeId** | Pointer to **NullableString** |  | [optional] 
**AccessResult** | **string** |  | 
**BadgeStatus** | Pointer to **NullableString** |  | [optional] 
**DoorHeldOpenTime** | Pointer to **NullableFloat64** |  | [optional] 
**EntryWithoutBadge** | Pointer to **NullableBool** |  | [optional] 
**DeviceStatus** | Pointer to **NullableString** |  | [optional] 

## Methods

### NewAccessEvent

`func NewAccessEvent(eventId string, timestamp time.Time, accessResult string, ) *AccessEvent`

NewAccessEvent instantiates a new AccessEvent object
This constructor will assign default values to properties that have it defined,
and makes sure properties required by API are set, but the set of arguments
will change when the set of required properties is changed

### NewAccessEventWithDefaults

`func NewAccessEventWithDefaults() *AccessEvent`

NewAccessEventWithDefaults instantiates a new AccessEvent object
This constructor will only assign default values to properties that have it defined,
but it doesn't guarantee that properties required by API are set

### GetEventId

`func (o *AccessEvent) GetEventId() string`

GetEventId returns the EventId field if non-nil, zero value otherwise.

### GetEventIdOk

`func (o *AccessEvent) GetEventIdOk() (*string, bool)`

GetEventIdOk returns a tuple with the EventId field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetEventId

`func (o *AccessEvent) SetEventId(v string)`

SetEventId sets EventId field to given value.


### GetTimestamp

`func (o *AccessEvent) GetTimestamp() time.Time`

GetTimestamp returns the Timestamp field if non-nil, zero value otherwise.

### GetTimestampOk

`func (o *AccessEvent) GetTimestampOk() (*time.Time, bool)`

GetTimestampOk returns a tuple with the Timestamp field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetTimestamp

`func (o *AccessEvent) SetTimestamp(v time.Time)`

SetTimestamp sets Timestamp field to given value.


### GetPersonId

`func (o *AccessEvent) GetPersonId() string`

GetPersonId returns the PersonId field if non-nil, zero value otherwise.

### GetPersonIdOk

`func (o *AccessEvent) GetPersonIdOk() (*string, bool)`

GetPersonIdOk returns a tuple with the PersonId field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetPersonId

`func (o *AccessEvent) SetPersonId(v string)`

SetPersonId sets PersonId field to given value.

### HasPersonId

`func (o *AccessEvent) HasPersonId() bool`

HasPersonId returns a boolean if a field has been set.

### SetPersonIdNil

`func (o *AccessEvent) SetPersonIdNil(b bool)`

 SetPersonIdNil sets the value for PersonId to be an explicit nil

### UnsetPersonId
`func (o *AccessEvent) UnsetPersonId()`

UnsetPersonId ensures that no value is present for PersonId, not even an explicit nil
### GetDoorId

`func (o *AccessEvent) GetDoorId() string`

GetDoorId returns the DoorId field if non-nil, zero value otherwise.

### GetDoorIdOk

`func (o *AccessEvent) GetDoorIdOk() (*string, bool)`

GetDoorIdOk returns a tuple with the DoorId field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetDoorId

`func (o *AccessEvent) SetDoorId(v string)`

SetDoorId sets DoorId field to given value.

### HasDoorId

`func (o *AccessEvent) HasDoorId() bool`

HasDoorId returns a boolean if a field has been set.

### SetDoorIdNil

`func (o *AccessEvent) SetDoorIdNil(b bool)`

 SetDoorIdNil sets the value for DoorId to be an explicit nil

### UnsetDoorId
`func (o *AccessEvent) UnsetDoorId()`

UnsetDoorId ensures that no value is present for DoorId, not even an explicit nil
### GetBadgeId

`func (o *AccessEvent) GetBadgeId() string`

GetBadgeId returns the BadgeId field if non-nil, zero value otherwise.

### GetBadgeIdOk

`func (o *AccessEvent) GetBadgeIdOk() (*string, bool)`

GetBadgeIdOk returns a tuple with the BadgeId field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetBadgeId

`func (o *AccessEvent) SetBadgeId(v string)`

SetBadgeId sets BadgeId field to given value.

### HasBadgeId

`func (o *AccessEvent) HasBadgeId() bool`

HasBadgeId returns a boolean if a field has been set.

### SetBadgeIdNil

`func (o *AccessEvent) SetBadgeIdNil(b bool)`

 SetBadgeIdNil sets the value for BadgeId to be an explicit nil

### UnsetBadgeId
`func (o *AccessEvent) UnsetBadgeId()`

UnsetBadgeId ensures that no value is present for BadgeId, not even an explicit nil
### GetAccessResult

`func (o *AccessEvent) GetAccessResult() string`

GetAccessResult returns the AccessResult field if non-nil, zero value otherwise.

### GetAccessResultOk

`func (o *AccessEvent) GetAccessResultOk() (*string, bool)`

GetAccessResultOk returns a tuple with the AccessResult field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetAccessResult

`func (o *AccessEvent) SetAccessResult(v string)`

SetAccessResult sets AccessResult field to given value.


### GetBadgeStatus

`func (o *AccessEvent) GetBadgeStatus() string`

GetBadgeStatus returns the BadgeStatus field if non-nil, zero value otherwise.

### GetBadgeStatusOk

`func (o *AccessEvent) GetBadgeStatusOk() (*string, bool)`

GetBadgeStatusOk returns a tuple with the BadgeStatus field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetBadgeStatus

`func (o *AccessEvent) SetBadgeStatus(v string)`

SetBadgeStatus sets BadgeStatus field to given value.

### HasBadgeStatus

`func (o *AccessEvent) HasBadgeStatus() bool`

HasBadgeStatus returns a boolean if a field has been set.

### SetBadgeStatusNil

`func (o *AccessEvent) SetBadgeStatusNil(b bool)`

 SetBadgeStatusNil sets the value for BadgeStatus to be an explicit nil

### UnsetBadgeStatus
`func (o *AccessEvent) UnsetBadgeStatus()`

UnsetBadgeStatus ensures that no value is present for BadgeStatus, not even an explicit nil
### GetDoorHeldOpenTime

`func (o *AccessEvent) GetDoorHeldOpenTime() float64`

GetDoorHeldOpenTime returns the DoorHeldOpenTime field if non-nil, zero value otherwise.

### GetDoorHeldOpenTimeOk

`func (o *AccessEvent) GetDoorHeldOpenTimeOk() (*float64, bool)`

GetDoorHeldOpenTimeOk returns a tuple with the DoorHeldOpenTime field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetDoorHeldOpenTime

`func (o *AccessEvent) SetDoorHeldOpenTime(v float64)`

SetDoorHeldOpenTime sets DoorHeldOpenTime field to given value.

### HasDoorHeldOpenTime

`func (o *AccessEvent) HasDoorHeldOpenTime() bool`

HasDoorHeldOpenTime returns a boolean if a field has been set.

### SetDoorHeldOpenTimeNil

`func (o *AccessEvent) SetDoorHeldOpenTimeNil(b bool)`

 SetDoorHeldOpenTimeNil sets the value for DoorHeldOpenTime to be an explicit nil

### UnsetDoorHeldOpenTime
`func (o *AccessEvent) UnsetDoorHeldOpenTime()`

UnsetDoorHeldOpenTime ensures that no value is present for DoorHeldOpenTime, not even an explicit nil
### GetEntryWithoutBadge

`func (o *AccessEvent) GetEntryWithoutBadge() bool`

GetEntryWithoutBadge returns the EntryWithoutBadge field if non-nil, zero value otherwise.

### GetEntryWithoutBadgeOk

`func (o *AccessEvent) GetEntryWithoutBadgeOk() (*bool, bool)`

GetEntryWithoutBadgeOk returns a tuple with the EntryWithoutBadge field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetEntryWithoutBadge

`func (o *AccessEvent) SetEntryWithoutBadge(v bool)`

SetEntryWithoutBadge sets EntryWithoutBadge field to given value.

### HasEntryWithoutBadge

`func (o *AccessEvent) HasEntryWithoutBadge() bool`

HasEntryWithoutBadge returns a boolean if a field has been set.

### SetEntryWithoutBadgeNil

`func (o *AccessEvent) SetEntryWithoutBadgeNil(b bool)`

 SetEntryWithoutBadgeNil sets the value for EntryWithoutBadge to be an explicit nil

### UnsetEntryWithoutBadge
`func (o *AccessEvent) UnsetEntryWithoutBadge()`

UnsetEntryWithoutBadge ensures that no value is present for EntryWithoutBadge, not even an explicit nil
### GetDeviceStatus

`func (o *AccessEvent) GetDeviceStatus() string`

GetDeviceStatus returns the DeviceStatus field if non-nil, zero value otherwise.

### GetDeviceStatusOk

`func (o *AccessEvent) GetDeviceStatusOk() (*string, bool)`

GetDeviceStatusOk returns a tuple with the DeviceStatus field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetDeviceStatus

`func (o *AccessEvent) SetDeviceStatus(v string)`

SetDeviceStatus sets DeviceStatus field to given value.

### HasDeviceStatus

`func (o *AccessEvent) HasDeviceStatus() bool`

HasDeviceStatus returns a boolean if a field has been set.

### SetDeviceStatusNil

`func (o *AccessEvent) SetDeviceStatusNil(b bool)`

 SetDeviceStatusNil sets the value for DeviceStatus to be an explicit nil

### UnsetDeviceStatus
`func (o *AccessEvent) UnsetDeviceStatus()`

UnsetDeviceStatus ensures that no value is present for DeviceStatus, not even an explicit nil

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


