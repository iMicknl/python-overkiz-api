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

- Atlantic Cozytouch
- Bouygues Flexom
- Brandt Smart Control **\***
- Hitachi Hi Kumo
- Nexity Eugénie
- Rexel Energeasy Connect **\*\***
- Sauter Cozytouch
- Simu (LiveIn2)
- Somfy Connexoon IO
- Somfy Connexoon RTS
- Somfy TaHoma
- Somfy TaHoma Switch
- Thermor Cozytouch

\[*] _These servers utilize an authentication method that is currently not supported by this library. To use this library with these servers, you will need to obtain an access token (by sniffing the original app) and create a local user on the Overkiz API platform._
\[**] _Requires OAuth credentials provided by Rexel._
