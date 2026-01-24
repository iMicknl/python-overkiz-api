# Core concepts

## Servers and gateways

A server describes where the API calls go. A gateway is the physical hub in your home. Cloud servers route through vendor infrastructure; local servers talk directly to the gateway on your network.

## Setup and devices

The setup describes the current gateway configuration and device inventory. Devices expose metadata like `uiClass` and `widget`, plus a list of current `states`.

## Actions, action groups, and commands

Commands are sent as `Action` objects, grouped into an action group. Each action targets a device URL and a set of commands with parameters.

## States

States are name/value pairs that represent the current device status, such as closure position or temperature.

## Events and listeners

The API uses an event listener that you register once per session. Fetching events drains the server-side buffer.

## Execution model

Commands are executed asynchronously by the platform. You can poll execution state via events or refresh device states after a delay.

## Relationship diagram

```
Client
  |
  |-- Server (cloud or local)
  |
  |-- Gateway
        |
        |-- Setup
        |     |
        |     |-- Devices
        |            |
        |            |-- States
        |            |-- Actions -> Commands -> Parameters
        |
        |-- Event Listener -> Events
```
