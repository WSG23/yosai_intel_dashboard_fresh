from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from analytics.clients.analytics_client.analytics_service_client import errors
from analytics.clients.analytics_client.analytics_service_client.client import (
    AuthenticatedClient,
    Client,
)
from analytics.clients.analytics_client.analytics_service_client.models.post_api_v1_analytics_get_dashboard_summary_response_200 import (
    PostApiV1AnalyticsGetDashboardSummaryResponse200,
)
from analytics.clients.analytics_client.analytics_service_client.types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/analytics/get_dashboard_summary",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    if response.status_code == 200:
        response_200 = PostApiV1AnalyticsGetDashboardSummaryResponse200.from_dict(
            response.json()
        )

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    """Get dashboard summary

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostApiV1AnalyticsGetDashboardSummaryResponse200]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    """Get dashboard summary

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostApiV1AnalyticsGetDashboardSummaryResponse200
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    """Get dashboard summary

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostApiV1AnalyticsGetDashboardSummaryResponse200]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[PostApiV1AnalyticsGetDashboardSummaryResponse200]:
    """Get dashboard summary

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostApiV1AnalyticsGetDashboardSummaryResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
