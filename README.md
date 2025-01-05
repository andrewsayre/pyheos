# pyheos

[![CI Status](https://github.com/andrewsayre/pyheos/workflows/CI/badge.svg)](https://github.com/andrewsayre/pyheos/actions)
[![codecov](https://codecov.io/github/andrewsayre/pyheos/graph/badge.svg?token=PV4P3AN7Z1)](https://codecov.io/github/andrewsayre/pyheos)
[![image](https://img.shields.io/pypi/v/pyheos.svg)](https://pypi.org/project/pyheos/)
[![image](https://img.shields.io/pypi/pyversions/pyheos.svg)](https://pypi.org/project/pyheos/)
[![image](https://img.shields.io/pypi/l/pyheos.svg)](https://pypi.org/project/pyheos/)

An async python library for controlling HEOS devices through the HEOS CLI Protocol (version 1.21 for HEOS firmware 3.40 or newer).

## Installation

```bash
pip install pyheos
```

## Getting Started

### `Heos` class

The `Heos` class is the implementation providing control to all HEOS compatible devices on the local network through a single network connection. It is suggested to connect to a device that is hard-wired.

#### `pyheos.Heos.create_and_connect(host: str, **kwargs) -> Heos`

Coroutine that accepts the host and options arguments (as defined in the `pyheos.HeosOptions` below), creates an instance of `Heos` and connects, returning the instance.

#### `pyheos.Heos(options: HeosOptions)`

- `options: HeosOptions`: An instance of HeosOptions that encapsulates options and configuration (see below)

#### `pyheos.Heos.connect() -> None`

Connect to the specified host. This method is a coroutine.

#### `pyheos.Heos.disconnect() -> None`

Disconnect from the specified host. This method is a coroutine.

#### `pyheos.Heos.get_players(*, refresh)`

Retrieve the available players as a `dict[int, pyheos.Heos.HeosPlayer]` where the key represents the `player_id` and the value the `HeosPlayer` instance. This method is a coroutine. This method will populate the `players` property and will begin tracking changes to the players.

- `refresh`: Set to `True` to retrieve the latest available players from the CLI. The default is `False` and will return the previous loaded players.

### `HeosOptions` class

This class encapsulates the options and configuration for connecting to a HEOS system.

#### `pyheos.HeosOptions(host, *, timeout, heart_beat, heart_beat_interval, dispatcher, auto_reconnect, auto_reconnect_delay, auto_reconnect_max_attempts, credentials)`

- `host: str`: A host name or IP address of a HEOS-capable device. This parameter is required.
- `timeout: float`: The timeout in seconds for opening a connectoin and issuing commands to the device. Default is `pyheos.const.DEFAULT_TIMEOUT = 10.0`. This parameter is required.
- `heart_beat: bool`: Set to `True` to enable heart beat messages, `False` to disable. Used in conjunction with `heart_beat_delay`. The default is `True`.
- `heart_beat_interval: float`: The interval in seconds between heart beat messages. Used in conjunction with `heart_beat`. Default is `pyheos.const.DEFAULT_HEART_BEAT = 10.0`
- `events: bool`: Set to `True` to enable event updates, `False` to disable. The default is `True`.
- `all_progress_events: bool`: Set to `True` to receive media progress events, `False` to only receive media changed events. The default is `True`.
- `dispatcher: pyheos.Dispatcher | None`: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
- `auto_reconnect: bool`: Set to `True` to automatically reconnect if the connection is lost. The default is `False`. Used in conjunction with `auto_reconnect_delay`.
- `auto_reconnect_delay: float`: The number of seconds to wait before attempting to reconnect upon a connection failure. The default is `DEFAULT_RECONNECT_DELAY = 10.0`. Used in conjunction with `auto_reconnect`.
- `auto_reconnect_max_attempts: float`: The maximum number of reconnection attempts before giving up. Set to `0` for unlimited attempts. The default is `0` (unlimited).
- `credentials`: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.

##### Example:

```python
import pyheos

heos = await Heos.create_and_connect('172.16.0.1', auto_reconnect=True)

players = await heos.get_players()
...
await heos.disconnect()
```
