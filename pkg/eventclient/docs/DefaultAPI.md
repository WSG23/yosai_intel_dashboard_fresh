# \DefaultAPI

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ApiV1EventsBatchPost**](DefaultAPI.md#ApiV1EventsBatchPost) | **Post** /api/v1/events/batch | Submit a batch of access events
[**ApiV1EventsPost**](DefaultAPI.md#ApiV1EventsPost) | **Post** /api/v1/events | Submit an access event



## ApiV1EventsBatchPost

> ApiV1EventsBatchPost200Response ApiV1EventsBatchPost(ctx).ApiV1EventsBatchPostRequest(apiV1EventsBatchPostRequest).Execute()

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
	apiV1EventsBatchPostRequest := *openapiclient.NewApiV1EventsBatchPostRequest() // ApiV1EventsBatchPostRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.ApiV1EventsBatchPost(context.Background()).ApiV1EventsBatchPostRequest(apiV1EventsBatchPostRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.ApiV1EventsBatchPost``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ApiV1EventsBatchPost`: ApiV1EventsBatchPost200Response
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.ApiV1EventsBatchPost`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiApiV1EventsBatchPostRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiV1EventsBatchPostRequest** | [**ApiV1EventsBatchPostRequest**](ApiV1EventsBatchPostRequest.md) |  | 

### Return type

[**ApiV1EventsBatchPost200Response**](ApiV1EventsBatchPost200Response.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ApiV1EventsPost

> EventResponse ApiV1EventsPost(ctx).AccessEvent(accessEvent).Execute()

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
	resp, r, err := apiClient.DefaultAPI.ApiV1EventsPost(context.Background()).AccessEvent(accessEvent).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.ApiV1EventsPost``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ApiV1EventsPost`: EventResponse
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.ApiV1EventsPost`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiApiV1EventsPostRequest struct via the builder pattern


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

