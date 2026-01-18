# Troubleshooting

## Cloud vs local connectivity

- Cloud servers require internet access and valid vendor credentials.
- Local servers require direct access to the gateway on your LAN.

## SSL and .local hostnames

If the gateway uses a self-signed certificate, pass `verify_ssl=False` when creating `OverkizClient` for local access.

## Authentication failures

- Confirm the server matches your vendor region.
- Re-run `login()` and retry the call.
- For unsupported auth flows, switch to local token authentication.

## Rate limits and concurrency

- Reduce polling frequency.
- Back off on `TooManyRequestsException` or `TooManyConcurrentRequestsException`.

## Listener drops

- Re-register the event listener when you see `InvalidEventListenerIdException`.
- Ensure your fetch loop is running every few seconds.

## Device not found

- Refresh setup with `get_setup()` and re-fetch devices.
- Confirm you are using the correct gateway and server.

## Logging tips

Enable debug logging in your application to inspect request/response details.

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```
