<!-- SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com> -->
<!-- SPDX-License-Identifier: MIT -->
# AxiomicCoreness Chat (iOS, SwiftUI source)

A small iPhone app that joins **`#axiomiccoreness` on Libera.Chat** and lets you talk to the
`!llm` bot (deepseek-r2-1.5b tutor, `sovereign-irc-bridge/src/irc_llm_bot.py`). The phone connects
**straight to Libera's WebSocket gateway**, so your PC exposes nothing: no open port, no tunnel,
no all-interfaces bind. The bot runs wherever you run it (home PC / VPS) and answers in the same channel.

This folder is **source only**. There is no `.ipa`: building one needs a Mac with Xcode and an
Apple signing identity. A free Apple ID is enough to put it on your own iPhone.

| | |
|---|---|
| Gateway | `wss://web.libera.chat/webirc/websocket/` (constant `IRCConfig.gatewayURL`) |
| Channel | `#axiomiccoreness` (`IRCConfig.channel`) |
| Nick | `Clarke_iOS_<4 digits>`; a new number is tried if the nick is taken (433) |
| Look | the TeaVM rhythm page's left chat column, colour for colour (`Theme.swift`) |
| Minimum iOS | 16.0 |

## Files

| File | What it is |
|---|---|
| `AxiomicCorenessChat/AxiomicCorenessChatApp.swift` | `@main` app entry |
| `AxiomicCorenessChat/ChatView.swift` | title bar (status dot · RECONNECT) · history · `›` input row |
| `AxiomicCorenessChat/LiberaIRCClient.swift` | WebSocket IRC client: registration, 001 → JOIN, 433 retry, PING/PONG, backoff |
| `AxiomicCorenessChat/IRCLine.swift` | pure-Foundation IRC line parser, frame splitter, outgoing sanitiser, `[thinking]` tracker |
| `AxiomicCorenessChat/Theme.swift` | colours, font, radii, paddings from `games/teavm-rhythm/src/main/webapp/index.html`, each with its line |
| `AxiomicCorenessChatTests/IRCLineTests.swift` | XCTest unit tests for `IRCLine.swift` |
| `Package.swift` | lets `swift test` run the parser tests on a Mac or Linux without Xcode |

## Build and install (Xcode on a Mac — a library Mac works)

1. **Xcode → File → New → Project… → iOS → App.**
   Product Name `AxiomicCorenessChat`, Interface **SwiftUI**, Language **Swift**, Storage **None**,
   tick **Include Tests**. Save anywhere.
2. In the new project, **delete** the generated `AxiomicCorenessChatApp.swift` and `ContentView.swift`
   (Move to Trash).
3. **Drag the five `.swift` files** from this repo's `AxiomicCorenessChat/` folder into the project's
   `AxiomicCorenessChat` group. In the dialog tick **Copy items if needed** and the **AxiomicCorenessChat**
   app target.
4. (Optional) Drag `AxiomicCorenessChatTests/IRCLineTests.swift` into the `AxiomicCorenessChatTests`
   group, ticking only the **AxiomicCorenessChatTests** target. Delete the generated test file there.
   Run with **⌘U**.
5. Target **AxiomicCorenessChat → General → Minimum Deployments → iOS 16.0** (or newer).
6. **Signing & Capabilities:** tick *Automatically manage signing*, Team = your Apple ID
   (*Add an Account…* if it isn't listed; a free account shows as "Personal Team"). If Xcode says
   the bundle identifier is taken, change it to something unique such as
   `com.mrteanotcoffee.axiomiccorenesschat`.
7. Plug in the iPhone, pick it as the run destination, press **▶ Run**.
   First time only, on the iPhone:
   - **Settings → Privacy & Security → Developer Mode → On** (iOS 16+), restart when asked.
   - **Settings → General → VPN & Device Management →** your Apple ID → **Trust**.
8. Free-account apps expire after **7 days**; press Run again from Xcode to renew.

No Info.plist changes are needed: the gateway is `wss://` (TLS), so App Transport Security allows it.

## Using it

- The dot in the title bar: teal = connected (after the server's `001` welcome), amber = connecting,
  grey = offline.
- Type `!llm what is the golden ratio?` and press **Send** (or Return). Your line is shown right away
  (IRC does not echo your own messages back).
- The bot's `[thinking]` … `[/thinking]` block (sent when the bot runs with `IRC_SHOW_THINKING=1`) and
  its "`(thinking: N line(s) hidden …)`" line are drawn at 55 % opacity.
- **RECONNECT** drops the socket and dials again now. A dropped connection retries by itself after
  1, 2, 4, 8 … seconds (never more than 60 s), but only while the app is on screen. When you leave the
  app it sends `QUIT` and closes; coming back reconnects. iOS would suspend a background socket anyway,
  so the phone is a chat window, not a server.
- Typed text has CR/LF removed and is cut to 400 UTF-8 bytes so one message is one IRC line.

## Tests

`IRCLineTests.swift` covers tags/prefix/params/trailing parsing, CR LF vs LF vs bare frames, the
outgoing sanitiser and the `[thinking]` tracker. Run them with **⌘U** in Xcode, or without Xcode:

```sh
cd ios/AxiomicCorenessChat && swift test
```

The repo has **no macOS CI job**, so GitHub Actions does not run these. The SwiftUI files need the iOS
SDK and are only compiled by Xcode.

## Troubleshooting

- **Stays amber, then "receive failed … 403" / "bad response"**: Libera's gateway sits behind
  Cloudflare, which refuses some networks (datacenter and some VPN / library IPs). Try mobile data or
  another Wi-Fi.
- **"nick … unavailable"**: handled automatically with a new number.
- **No answer to `!llm`**: the bot is not in the channel. Start it on your PC (see
  `sovereign-irc-bridge/serving/IRC_BOT.md`); the app cannot start it for you.
