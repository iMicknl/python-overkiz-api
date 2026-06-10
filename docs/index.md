---
hide:
  - navigation
  - toc
  - title
---
<style>
  .md-content__inner > h1:first-of-type {
    display: none;
  }
</style>

pyOverkiz is an async Python library for interacting with Overkiz-based platforms, including Somfy and Atlantic. It enables authentication, device discovery, state reading, command execution, and real-time event streaming from supported gateways.

## What you can do

- Authenticate with Overkiz cloud or local gateways
- Automatically discover and list connected devices
- Read device states and attributes
- Execute commands on devices
- Receive real-time updates via event streams

## Supported hubs

| Vendor | Cloud | Local |
| --- | :-: | :-: |
| Atlantic Cozytouch | ✓ | |
| Bouygues Flexom | ✓ | |
| Brandt Smart Control † | ✓ | |
| Hexaom HexaConnect | ✓ | |
| Hitachi Hi Kumo | ✓ | |
| Nexity Eugénie | ✓ | |
| Rexel Energeasy Connect ‡ | ✓ | ✓ |
| Sauter Cozytouch | ✓ | |
| Simu LiveIn2 | ✓ | |
| Somfy | ✓ | ✓ |
| Thermor Cozytouch | ✓ | |
| Ubiwizz | ✓ | |

Local API availability depends on your specific gateway. See the [Getting started guide](getting-started.md) for the supported gateways and setup.

† _This server's authentication method isn't supported yet. To use it, obtain an access token (by sniffing the original app) and create a local user on the Overkiz API platform._

‡ _The cloud API requires OAuth credentials provided by Rexel; the local API uses a token from the EConnect app instead._

### Somfy

| Gateway | Cloud | Local |
| --- | :-: | :-: |
| Connexoon IO | ✓ | ✓ |
| Connexoon RTS | ✓ | ✓ |
| TaHoma v2 | ✓ | ✓ |
| TaHoma Beecon | ✓ | ✓ |
| TaHoma Switch | ✓ | ✓ |
| Connectivity Kit | ✓ | |

### Rexel Energeasy Connect

| Gateway | Cloud | Local |
| --- | :-: | :-: |
| Energeasy Connect | ✓ | |
| Energeasy Connect Rail Din | ✓ | ✓ |
| Energeasy Connect V2 | ✓ | ✓ |
| Energeasy Connect V3 | ✓ | ✓ |
| Energeasy Connect V3 Rail Din | ✓ | ✓ |
