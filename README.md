# pyheos
[![CI Status](https://github.com/andrewsayre/pyheos/workflows/CI/badge.svg)](https://github.com/andrewsayre/pyheos/actions)
[![codecov](https://codecov.io/github/andrewsayre/pyheos/graph/badge.svg?token=PV4P3AN7Z1)](https://codecov.io/github/andrewsayre/pyheos)
[![image](https://img.shields.io/pypi/v/pyheos.svg)](https://pypi.org/project/pyheos/)
[![image](https://img.shields.io/pypi/pyversions/pyheos.svg)](https://pypi.org/project/pyheos/)
[![image](https://img.shields.io/pypi/l/pyheos.svg)](https://pypi.org/project/pyheos/)

An async python library for controlling HEOS devices through the HEOS CLI Protocol (version 1.17 for players with firmware 2.41.140 or newer).

## Installation
```bash
pip install pyheos
```
or
```bash
pip install --use-wheel pyheos
```

## Getting Started

The `Heos` class is the implementation providing control to all HEOS compatible devices on the local network through a single network connection.  It is suggested to connect to a device that is hard-wired.

#### `pyheos.Heos(host, *, timeout, heart_beat, all_progress_events, dispatcher)`
- `host: str`: The IP Address or hostname of a HEOS device on the local network. This parameter is required.
- `timeout: float`: Number of seconds to wait during connection and issuing commands. Default is `pyheos.const.DEFAULT_TIMEOUT = 5.0`.  This parameter is required.
- `heart_beat: Optional[float]`: Number of seconds since last activity to issue a heart-beat command. Default is `pyheos.const.DEFAULT_HEART_BEAT = 60.0`.  Set this parameter to `None` to disable heart-beat.
- `all_progress_events`: Set to `True` to receive signals for each media play-back progression or `False` to only receive a signal when media state transitions to playing or changes.  Default is `True`.  This parameter is required.
- `dispatcher: Optional[pyheos.Dispatcher]`: An instance of dispatcher to use for raising signals.  The default is `None` which results in use of the default dispatcher implementation.

#### `pyheos.Heos.connect(*, auto_reconnect, reconnect_delay)`

Connect to the specified host.  This method is a coroutine.
- `auto_reconnect: bool`: Set to `True` to automatically reconnect to the host upon disconnection.  The default is `False`.
- `reconnect_delay: float`: The number of seconds to wait before attempting to reconnect upon a connection failure. The default is `DEFAULT_RECONNECT_DELAY = 5.0`

#### `pyheos.Heos.disconnect()`

Disconnect from the specified host.  This method is a coroutine.

#### `pyheos.Heos.get_players(*, refresh)`

Retrieve the available players as a `Dict[int, pyheos.Heos.HeosPlayer]` where the key represents the `player_id` and the value the `HeosPlayer` instance.  This method is a coroutine.  This method will populate the `players` property and will begin tracking changes to the players.
- `refresh`: Set to `True` to retrieve the latest available players from the CLI. The default is `False` and will return the previous loaded players.

##### Example:
```python
import pyheos

heos = Heos('172.16.0.1')

await heos.connect(auto_reconnect=True)
players = await heos.get_players()
...
await heos.disconnect()
```