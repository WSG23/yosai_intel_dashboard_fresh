from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_api_v1_analytics_get_access_patterns_analysis_body import (
    PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
)
from ...models.post_api_v1_analytics_get_access_patterns_analysis_response_200 import (
    PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200,
)
from ...types import Response


def _get_kwargs(
    *,
    body: PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/analytics/get_access_patterns_analysis",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    if response.status_code == 200:
        response_200 = PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
) -> Response[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    """Get access patterns analysis

    Args:
        body (PostApiV1AnalyticsGetAccessPatternsAnalysisBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
) -> Optional[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    """Get access patterns analysis

    Args:
        body (PostApiV1AnalyticsGetAccessPatternsAnalysisBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
) -> Response[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    """Get access patterns analysis

    Args:
        body (PostApiV1AnalyticsGetAccessPatternsAnalysisBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostApiV1AnalyticsGetAccessPatternsAnalysisBody,
) -> Optional[PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200]:
    """Get access patterns analysis

    Args:
        body (PostApiV1AnalyticsGetAccessPatternsAnalysisBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostApiV1AnalyticsGetAccessPatternsAnalysisResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
