# V1EventsBatchPostRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**Events** | Pointer to [**[]AccessEvent**](AccessEvent.md) |  | [optional] 

## Methods

### NewV1EventsBatchPostRequest

`func NewV1EventsBatchPostRequest() *V1EventsBatchPostRequest`

NewV1EventsBatchPostRequest instantiates a new V1EventsBatchPostRequest object
This constructor will assign default values to properties that have it defined,
and makes sure properties required by API are set, but the set of arguments
will change when the set of required properties is changed

### NewV1EventsBatchPostRequestWithDefaults

`func NewV1EventsBatchPostRequestWithDefaults() *V1EventsBatchPostRequest`

NewV1EventsBatchPostRequestWithDefaults instantiates a new V1EventsBatchPostRequest object
This constructor will only assign default values to properties that have it defined,
but it doesn't guarantee that properties required by API are set

### GetEvents

`func (o *V1EventsBatchPostRequest) GetEvents() []AccessEvent`

GetEvents returns the Events field if non-nil, zero value otherwise.

### GetEventsOk

`func (o *V1EventsBatchPostRequest) GetEventsOk() (*[]AccessEvent, bool)`

GetEventsOk returns a tuple with the Events field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetEvents

`func (o *V1EventsBatchPostRequest) SetEvents(v []AccessEvent)`

SetEvents sets Events field to given value.

### HasEvents

`func (o *V1EventsBatchPostRequest) HasEvents() bool`

HasEvents returns a boolean if a field has been set.


[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


