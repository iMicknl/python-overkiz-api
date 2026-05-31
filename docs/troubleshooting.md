# Troubleshooting

## Authentication failures

- Confirm the server matches your vendor and region.
- Re-run `login()` and retry the call.
- On `NotAuthenticatedError`, re-authenticate before retrying.

## Rexel (Energeasy Connect)

Rexel authenticates with OAuth2 and scopes every request to a single gateway, so its failure modes differ from username/password servers.

- `InvalidTokenError: Consent is missing or revoked for Rexel token.` — the access token does not carry the consent Rexel requires. Re-run the OAuth2 authorization flow so the user grants consent again.
- `InvalidTokenError: Error retrieving Rexel access token: ...` — the code exchange or refresh failed (expired authorization code, reused code, or invalid `code_verifier`). Restart the flow from a freshly generated PKCE pair.
- `NoGatewaySelectedError: Multiple Rexel gateways available; call discover_gateways() ...` — the account has more than one gateway and none is selected. Call `discover_gateways()` and pass one id to `select_gateway()` before making device calls. A single-gateway account is auto-selected on `login()`.
- `AccessDeniedToGatewayError` — the selected `gateway_id` is not reachable for this token. Re-discover gateways and select a valid one; if you persisted a `gateway_id`, confirm it still belongs to the account.

## Rate limits and concurrency

- Reduce polling frequency.
- Back off on `TooManyRequestsError` or `TooManyConcurrentRequestsError`.
- Use short, jittered delays for transient errors.

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.exceptions import (
    NotAuthenticatedError,
    TooManyConcurrentRequestsError,
    TooManyRequestsError,
)


async def fetch_devices_with_retry() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        for attempt in range(5):
            try:
                devices = await client.get_devices()
                print(devices)
                return
            except (TooManyRequestsError, TooManyConcurrentRequestsError):
                await asyncio.sleep(0.5 * (attempt + 1))
            except NotAuthenticatedError:
                await client.login()


asyncio.run(fetch_devices_with_retry())
```

## Common errors

- `NotAuthenticatedError`
- `BadCredentialsError`
- `TooManyRequestsError`
- `TooManyConcurrentRequestsError`
- `TooManyExecutionsError`
- `MaintenanceError`
- `AccessDeniedToGatewayError`
- `NoGatewaySelectedError`
- `InvalidTokenError`

## SSL and local certificates

- Cloud servers require internet access and valid vendor credentials.
- Local servers require direct access to the gateway on your LAN.
- If the gateway uses a self-signed certificate, pass `verify_ssl=False` when creating `OverkizClient` for local access.

## Listener drops

- Re-register the event listener when you see `InvalidEventListenerIdError`.
- Ensure your fetch loop is running every few seconds.

## Device not found

- Refresh setup with `get_setup()` and re-fetch devices.
- Confirm you are using the correct gateway and server.

## Timeouts

For long-running operations, prefer shorter request timeouts with retries rather than a single long timeout.

## Logging

Enable debug logging in your application to inspect request/response details.

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```
