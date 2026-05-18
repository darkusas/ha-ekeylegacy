# Home Assistant Integration - ekey (legacy)

Home Assistant integration for ekey home or multi (legacy) fingerprint readers.

This integration listens for UDP packets sent by ekey home or ekey multi devices and exposes them as Home Assistant **Event** entities. When a fingerprint is recognized (or rejected), an event is fired with details such as user, finger, scanner, relay, and action outcome.

[![Static Badge](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)](https://github.com/hacs/integration) 
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/klein0r/ha-ekeylegacy/total?style=for-the-badge)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/klein0r/ha-ekeylegacy?style=for-the-badge)

![GitHub Release Date](https://img.shields.io/github/release-date-pre/klein0r/ha-ekeylegacy?style=for-the-badge&label=Latest%20Beta%20Release) [![GitHub Release](https://img.shields.io/github/v/release/klein0r/ha-ekeylegacy?include_prereleases&style=for-the-badge)](https://github.com/klein0r/ha-ekeylegacy/releases)

![GitHub Release Date](https://img.shields.io/github/release-date/klein0r/ha-ekeylegacy?style=for-the-badge&label=Latest%20Release) [![GitHub Release](https://img.shields.io/github/v/release/klein0r/ha-ekeylegacy?style=for-the-badge)](https://github.com/klein0r/ha-ekeylegacy/releases)

## Setup

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=klein0r&repository=ha-ekeylegacy&category=Integration)

## Configuration

After installing via HACS, add the integration through **Settings → Devices & Services → Add Integration → ekey (legacy)**.

| Field | Description | Default |
|-------|-------------|---------|
| **Port** | UDP port the ekey device sends packets to | `56000` |
| **Delimiter** | Character used to separate fields in the UDP packet | `_` |
| **Type** | Device type: `home` or `multi` | `home` |

### Example – ekey home

Configure the ekey home device to send UDP packets to your Home Assistant IP on port `56000` using `_` as the delimiter. After adding the integration you will have an event entity that fires:

- `authenticated` – fingerprint recognised (action = `1`), with event data:
  ```yaml
  type: "0"
  user: "1"
  finger: "1"
  scanner: "0A1B2C3D4E5F"
  action: "1"
  relay: "1"
  ```
- `failed` – fingerprint not recognised (action ≠ `1`), with the same fields.

### Example – ekey multi

Configure the ekey multi device to send UDP packets to your Home Assistant IP on port `56000` using `_` as the delimiter and select `multi` as the type. The fired events carry additional fields:

- `authenticated` / `failed` event data:
  ```yaml
  type: "0"
  user: "1"
  user_name: "John"
  user_status: "1"
  finger: "1"
  relay: "1"
  scanner: "0A1B2C3D4E5F"
  scanner_name: "Front door"
  action: "1"
  digital_input: "0"
  ```

### Example automation

```yaml
automation:
  - alias: "Front door opened by fingerprint"
    trigger:
      - platform: event
        event_type: ekeylegacy_event
        event_data:
          event_type: authenticated
    action:
      - service: notify.mobile_app_my_phone
        data:
          message: "User {{ trigger.event.data.user }} opened the front door"
```

## License

The MIT License (MIT)

Copyright (c) 2026 Matthias Kleine <info@haus-automatisierung.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
