# openapi_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**api_v1_events_batch_post**](DefaultApi.md#api_v1_events_batch_post) | **POST** /api/v1/events/batch | Submit a batch of access events
[**api_v1_events_post**](DefaultApi.md#api_v1_events_post) | **POST** /api/v1/events | Submit an access event


# **api_v1_events_batch_post**
> ApiV1EventsBatchPost200Response api_v1_events_batch_post(api_v1_events_batch_post_request)

Submit a batch of access events

### Example


```python
import openapi_client
from openapi_client.models.api_v1_events_batch_post200_response import ApiV1EventsBatchPost200Response
from openapi_client.models.api_v1_events_batch_post_request import ApiV1EventsBatchPostRequest
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)
    api_v1_events_batch_post_request = openapi_client.ApiV1EventsBatchPostRequest() # ApiV1EventsBatchPostRequest | 

    try:
        # Submit a batch of access events
        api_response = api_instance.api_v1_events_batch_post(api_v1_events_batch_post_request)
        print("The response of DefaultApi->api_v1_events_batch_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->api_v1_events_batch_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **api_v1_events_batch_post_request** | [**ApiV1EventsBatchPostRequest**](ApiV1EventsBatchPostRequest.md)|  | 

### Return type

[**ApiV1EventsBatchPost200Response**](ApiV1EventsBatchPost200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Batch status |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **api_v1_events_post**
> EventResponse api_v1_events_post(access_event)

Submit an access event

### Example


```python
import openapi_client
from openapi_client.models.access_event import AccessEvent
from openapi_client.models.event_response import EventResponse
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)
    access_event = openapi_client.AccessEvent() # AccessEvent | 

    try:
        # Submit an access event
        api_response = api_instance.api_v1_events_post(access_event)
        print("The response of DefaultApi->api_v1_events_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->api_v1_events_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **access_event** | [**AccessEvent**](AccessEvent.md)|  | 

### Return type

[**EventResponse**](EventResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Acknowledgement |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

