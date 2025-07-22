# openapi_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**v1_events_batch_post**](DefaultApi.md#v1_events_batch_post) | **POST** /v1/events/batch | Submit a batch of access events
[**v1_events_post**](DefaultApi.md#v1_events_post) | **POST** /v1/events | Submit an access event


# **v1_events_batch_post**
> V1EventsBatchPost200Response v1_events_batch_post(v1_events_batch_post_request)

Submit a batch of access events

### Example


```python
import openapi_client
from openapi_client.models.v1_events_batch_post200_response import V1EventsBatchPost200Response
from openapi_client.models.v1_events_batch_post_request import V1EventsBatchPostRequest
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
    v1_events_batch_post_request = openapi_client.V1EventsBatchPostRequest() # V1EventsBatchPostRequest | 

    try:
        # Submit a batch of access events
        api_response = api_instance.v1_events_batch_post(v1_events_batch_post_request)
        print("The response of DefaultApi->v1_events_batch_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->v1_events_batch_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **v1_events_batch_post_request** | [**V1EventsBatchPostRequest**](V1EventsBatchPostRequest.md)|  | 

### Return type

[**V1EventsBatchPost200Response**](V1EventsBatchPost200Response.md)

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

# **v1_events_post**
> EventResponse v1_events_post(access_event)

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
        api_response = api_instance.v1_events_post(access_event)
        print("The response of DefaultApi->v1_events_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->v1_events_post: %s\n" % e)
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

