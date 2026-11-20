# Pi 4 / HDMI / WS2812B wiring draft (not yet physically verified)

This is a **proposed wiring sketch**, not a finalized PCB or an electrical safety certification. Confirm strip model, length, actual power requirements, and Pi OS driver configuration before assembly.

```text
                         HDMI cable
  ┌──────────────────┐  ─────────────► ┌────────────────┐
  │ Raspberry Pi 4   │                  │ 5–8 inch HDMI  │
  │ Wi-Fi + Python   │                  │ display        │
  │                  │                  └────────────────┘
  │ GPIO18 pin 12    ├───signal──►[74AHCT125 1A pin 2]
  │ GND pin 6        ├────────────┬──────────────────────┐
  └──────────────────┘            │                      │
         ▲                        ▼                      ▼
   Official Pi USB-C         [level shifter]      [WS2812B GND]
     power input            1OE pin 1 → GND          ▲
                            GND pin 7 → GND          │
  Separate regulated       VCC pin 14 → +5V         │
      5V LED supply ────────┬──────────────► WS2812B +5V
                            │
   [74AHCT125 1Y pin 3]────[330–470 Ω]────► WS2812B DIN

  Common GND: LED power supply ↔ shifter ↔ Pi ↔ LED strip.
  Do NOT tie the two power supplies' +5V terminals together.
  Do NOT power a long LED strip from a Pi GPIO/5V pin.
```

| Item | Connection / note |
|---|---|
| Pi display | micro-HDMI to HDMI monitor; display power depends on selected model |
| Pi data GPIO | BCM GPIO18 = physical pin 12; may conflict with onboard analog audio PWM; don't assume both concurrently |
| Level shifter | 74AHCT125 1A pin 2 ⇐ GPIO18; 1Y pin 3 → LED DIN via series resistor; 1OE pin 1 → GND; VCC pin 14 → +5V; GND pin 7 → GND |
| LED strip | External regulated 5V + common ground; input capacitor near strip is commonly recommended; verify polarity |
| LED power sizing | WS2812B up to ~60 mA per LED at worst-case white; 30 pixels could be ~1.8 A max, so do not choose a supply without margin |
| Speakers | Deliberately NOT connected for this display-only MVP; audio path remains separate / undecided |

The GPIO18 software LED library and OS configuration must be checked against audio use and other peripherals. Do not connect while powered.

Engineering reference: Adafruit "NeoPixels on Raspberry Pi", wiring with 74AHCT125: https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring
