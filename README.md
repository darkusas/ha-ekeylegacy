# Home Assistant Integration - ekey (legacy)

Home Assistant integration for legacy ekey fingerprint systems.

The integration listens for UDP packets sent by an ekey controller and exposes them as a Home Assistant **Event** entity. It now supports all three legacy controller formats used by this repository:

- `home` - text-based ekey home payloads
- `multi` - text-based ekey multi payloads
- `rare` - binary RARE payloads used by some ekey home installations

Whenever the controller reports a scan result, the entity fires one of these events:

- `authenticated` - successful authentication
- `failed` - rejected or unknown finger

The integration uses the Home Assistant event type `ekeylegacy_event`.

It also provides a YAML-only `binary_sensor` platform that can turn matching ekey events into short pulse sensors.

## Installation

1. Install the integration with HACS.
2. Restart Home Assistant if HACS asks for it.
3. Open **Settings → Devices & Services**.
4. Select **Add Integration**.
5. Search for **ekey (legacy)**.

## Integration setup

During setup you will be asked for:

| Field | Description | Default |
|-------|-------------|---------|
| **Port** | UDP port Home Assistant listens on | `56000` |
| **Delimiter** | Separator used in text payloads (`home` / `multi`) | `_` |
| **Type** | Protocol type: `home`, `multi`, or `rare` | `home` |

### Important notes

- Use a unique UDP port for each configured device/protocol pair.
- The `Delimiter` value is ignored when `Type = rare`.
- Home Assistant must be reachable from the ekey controller on the configured UDP port.
- If your network firewall filters local UDP traffic, allow incoming packets to the selected port.

## Device-side configuration

### ekey home

Configure the controller to send `home` UDP packets to the IP address of Home Assistant on the same port that you configured in the integration. Use the same delimiter on both sides, usually `_`.

Example payload:

```text
0_001_1_0A1B2C3D4E5F_1_1
```

Generated event payload:

```yaml
type: "0"
user: "1"
finger: "1"
scanner: "0A1B2C3D4E5F"
action: "1"
relay: "1"
```

`action = 1` produces `authenticated`. Any other action value produces `failed`.

### ekey multi

Configure the controller to send `multi` UDP packets to the Home Assistant IP and configured UDP port. Keep the delimiter consistent with the controller configuration.

Example payload:

```text
0_001_John_1_1_1_0A1B2C3D4E5F_Front door_1_0
```

Generated event payload:

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

`action = 1` produces `authenticated`. Any other action value produces `failed`.

### ekey rare

Select `rare` when the controller sends the binary RARE protocol described in `custom_components/ekeylegacy/doc/rare_protocol.md`.

The integration expects a fixed 72-byte packet with:

- version `3`
- command `136` (`0x88`, accepted finger) or `137` (`0x89`, rejected finger)
- terminal ID and terminal serial
- relay ID
- user ID
- finger ID
- event text
- time text
- name / personal ID fields

Generated event payload:

```yaml
version: "3"
command: "136"
action: "open"
terminal_id: "1"
terminal_serial: "80123456789012"
relay: "0"
user: "7"
finger: "2"
event: "OPEN"
timestamp: "2026-05-18 12:00"
name: "0"
personal_id: "0"
```

RARE event mapping:

- `command = 136` → `authenticated`
- `command = 137` → `failed`

Finger values are reported exactly as sent by the controller. In the original ekey documentation:

- `0..8` = fingers `1..9`
- `9` = finger `0`
- `13` = RFID

## Using the events in Home Assistant

After setup you will see one event entity such as `event.ekey_home`, `event.ekey_multi`, or `event.ekey_rare`.

### Example automation - react to successful authentication

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
          message: >-
            User {{ trigger.event.data.user }} opened the door
```

### Example automation - only for a specific RARE terminal

```yaml
automation:
  - alias: "Rare scanner accepted user 7"
    trigger:
      - platform: event
        event_type: ekeylegacy_event
        event_data:
          event_type: authenticated
          terminal_serial: "80123456789012"
          user: "7"
    action:
      - service: logbook.log
        data:
          name: "ekey"
          message: "User 7 authenticated on the RARE controller"
```

## YAML binary sensors (trigger-like pulses)

You can create `binary_sensor` entities that become `on` for a short time whenever an `ekeylegacy_event` matches configured attributes.

- Default pulse time: `2` seconds
- Custom pulse time: set `duration` (seconds)
- Matching keys: one, many, or all event attributes (for example `event_type`, `terminal_serial`, `relay`, `user`, `finger`, `action`, ...)

### Example - single matcher (all successful authentications)

```yaml
binary_sensor:
  - platform: ekeylegacy
    name: "ekey authenticated pulse"
    event_type: authenticated
```

### Example - multiple matchers for RARE events

```yaml
binary_sensor:
  - platform: ekeylegacy
    name: "RARE terminal user 7 relay 0"
    duration: 5
    event_type: authenticated
    terminal_serial: "80123456789012"
    user: "7"
    relay: "0"
```

### Example - strict matcher using many fields

```yaml
binary_sensor:
  - platform: ekeylegacy
    name: "Exact RARE trigger"
    duration: 3
    event_type: failed
    terminal_serial: "80123456789012"
    terminal_id: "1"
    user: "0"
    finger: "13"
    relay: "0"
    action: reject
```

## Troubleshooting

- No events arrive: verify the Home Assistant IP, UDP port, firewall rules, and selected protocol type.
- Wrong parsing: check whether the controller uses `home`, `multi`, or `rare`.
- Text payloads are ignored: confirm the configured delimiter matches the controller setting.
- RARE payloads are ignored: confirm the controller sends protocol version `3` and command `136` or `137`.

### Debug logging for full RARE events

If you enable debug logging for this integration in `configuration.yaml`, every parsed RARE event is logged with all parsed fields.

```yaml
logger:
  default: info
  logs:
    custom_components.ekeylegacy.event: debug
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
