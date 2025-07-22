# ApiV1EventsBatchPost200Response

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**Results** | Pointer to [**[]EventResponse**](EventResponse.md) |  | [optional] 

## Methods

### NewApiV1EventsBatchPost200Response

`func NewApiV1EventsBatchPost200Response() *ApiV1EventsBatchPost200Response`

NewApiV1EventsBatchPost200Response instantiates a new ApiV1EventsBatchPost200Response object
This constructor will assign default values to properties that have it defined,
and makes sure properties required by API are set, but the set of arguments
will change when the set of required properties is changed

### NewApiV1EventsBatchPost200ResponseWithDefaults

`func NewApiV1EventsBatchPost200ResponseWithDefaults() *ApiV1EventsBatchPost200Response`

NewApiV1EventsBatchPost200ResponseWithDefaults instantiates a new ApiV1EventsBatchPost200Response object
This constructor will only assign default values to properties that have it defined,
but it doesn't guarantee that properties required by API are set

### GetResults

`func (o *ApiV1EventsBatchPost200Response) GetResults() []EventResponse`

GetResults returns the Results field if non-nil, zero value otherwise.

### GetResultsOk

`func (o *ApiV1EventsBatchPost200Response) GetResultsOk() (*[]EventResponse, bool)`

GetResultsOk returns a tuple with the Results field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetResults

`func (o *ApiV1EventsBatchPost200Response) SetResults(v []EventResponse)`

SetResults sets Results field to given value.

### HasResults

`func (o *ApiV1EventsBatchPost200Response) HasResults() bool`

HasResults returns a boolean if a field has been set.


[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


