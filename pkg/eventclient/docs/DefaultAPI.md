# \DefaultAPI

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**V1EventsBatchPost**](DefaultAPI.md#V1EventsBatchPost) | **Post** /v1/events/batch | Submit a batch of access events
[**V1EventsPost**](DefaultAPI.md#V1EventsPost) | **Post** /v1/events | Submit an access event



## V1EventsBatchPost

> V1EventsBatchPost200Response V1EventsBatchPost(ctx).V1EventsBatchPostRequest(v1EventsBatchPostRequest).Execute()

Submit a batch of access events

### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
	openapiclient "github.com/GIT_USER_ID/GIT_REPO_ID"
)

func main() {
	v1EventsBatchPostRequest := *openapiclient.NewV1EventsBatchPostRequest() // V1EventsBatchPostRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.V1EventsBatchPost(context.Background()).V1EventsBatchPostRequest(v1EventsBatchPostRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.V1EventsBatchPost``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `V1EventsBatchPost`: V1EventsBatchPost200Response
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.V1EventsBatchPost`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiV1EventsBatchPostRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **v1EventsBatchPostRequest** | [**V1EventsBatchPostRequest**](V1EventsBatchPostRequest.md) |  | 

### Return type

[**V1EventsBatchPost200Response**](V1EventsBatchPost200Response.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## V1EventsPost

> EventResponse V1EventsPost(ctx).AccessEvent(accessEvent).Execute()

Submit an access event

### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
    "time"
	openapiclient "github.com/GIT_USER_ID/GIT_REPO_ID"
)

func main() {
	accessEvent := *openapiclient.NewAccessEvent("EventId_example", time.Now(), "AccessResult_example") // AccessEvent | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.V1EventsPost(context.Background()).AccessEvent(accessEvent).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.V1EventsPost``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `V1EventsPost`: EventResponse
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.V1EventsPost`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiV1EventsPostRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **accessEvent** | [**AccessEvent**](AccessEvent.md) |  | 

### Return type

[**EventResponse**](EventResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

