<!-- SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com> -->
<!-- SPDX-License-Identifier: MIT -->
# Clarke Pocket (iOS, SwiftUI source)

A small PocketPal-style iPhone app with three tabs:

- **Model**: downloads the pinned GGUF model (or imports one from Files), checks its SHA-256 and
  loads it with llama.cpp on the phone's GPU (Metal).
- **Chat**: talk to the model **on the phone**, with no server and no PC. Answers stream in, and
  **Stop** cuts one short. The model's reasoning (`<think>…</think>`) sits in a dimmed **thinking**
  disclosure. Math shows as LaTeX source in the accent colour. Every exchange is saved in the PC bridge's
  history format (Markdown + LaTeX, thinking stored separately).
- **IRC**: the same abjects client as `ios/AxiomicCorenessChat` (PR #165), plus slash commands. You can
  also switch on answering `!llm` questions with the on-device model.

This folder is **source only**. There is no `.ipa`. You build it with Xcode on a Mac, and a free
Apple ID is enough to put it on your own iPhone. It targets an **iPhone 12 (A14, 4 GB)** and anything newer.

| | |
|---|---|
| Model | `ClarkeYoursaTee (deepseek-r2-1.5b)`, `deepseek-r2-1.5b-Q4_K_M.gguf`, 1 117 320 640 bytes (1.12 GB), sha256 `80a49c2f…79e5c1`, from this repo's release [`model-deepseek-r2-1.5b-q4km-v1`](https://github.com/AxiomicCoreness/hello_world.py/releases/tag/model-deepseek-r2-1.5b-q4km-v1) (`Sources/PocketCore/ModelPin.swift`) |
| Inference | llama.cpp release **b11960** (the build behind llama.cpp v0.8.0), as the official prebuilt `llama-b11960-xcframework.zip`, pinned by checksum in `LlamaBinary/Package.swift` |
| Settings | context 2048 tokens · all layers on Metal · 2 generation / 4 batch threads on the A14 (from its 2 performance cores) · temperature 0.6, top-p 0.95 (read from the GGUF) · chat template from the GGUF |
| IRC | `wss://irc.abjects.net:6680/`, starts in `#axiomiccoreness`, nick `Clarke_iOS_<4 digits>` |
| Look | the TeaVM rhythm page's chat column (`Theme.swift`, copied from PR #165) |
| Minimum iOS | **16.4** (the llama.cpp framework is built for 16.4+). **Real iPhone only**: the framework has no simulator slice |

## Files

| Path | What it is |
|---|---|
| `project.yml` | XcodeGen spec that generates `ClarkePocket.xcodeproj` (not committed) |
| `LlamaBinary/Package.swift` | local Swift package wrapping llama.cpp's XCFramework (URL + checksum) |
| `ClarkePocket/ClarkePocketApp.swift` | `@main`, tabs, foreground/background handling |
| `ClarkePocket/LlamaEngine.swift` | llama.cpp C API wrapper (`actor`): load, chat template, tokenize, prefill, stream, stop |
| `ClarkePocket/ModelStore.swift` | download / import / SHA-256 check / load / unload, plus the generation lock for one answer at a time |
| `ClarkePocket/ModelView.swift` | Model tab |
| `ClarkePocket/ChatStore.swift`, `ChatView.swift`, `MarkdownText.swift` | Chat tab, saved history, Markdown + math rendering |
| `ClarkePocket/IRCClient.swift` | copied from PR #165, then adapted: slash commands, active channel, responder hook |
| `ClarkePocket/IRCView.swift`, `IRCResponder.swift` | IRC tab and the optional on-device `!llm` answerer |
| `ClarkePocket/MemoryMonitor.swift`, `Theme.swift`, `Info.plist` | free-memory / P-core queries, colours (copied from #165), app plist |
| `Sources/PocketCore/*.swift` | pure-Foundation core, compiled into the app and unit-tested: model pin + SHA-256 verifier, history format, Markdown/LaTeX port, IRC parser (copied from #165), slash-command builder, `!llm` reply wrapper + rate limiter, runtime policy, UTF-8 stream assembler |
| `Tests/PocketCoreTests/` | 40 XCTest cases (`swift test`), including byte-for-byte checks against the Python bridge |
| `Package.swift` | runs those tests on a Mac or Linux without Xcode |
| `Optional/IncreasedMemoryLimit.entitlements` | **not used by default** (see below) |

## Build and install

You need a Mac with **Xcode 16 or newer**, an iPhone with **iOS 16.4+** and a USB cable. A library Mac works.

### A. With XcodeGen (recommended)

```sh
brew install xcodegen          # once
git clone https://github.com/AxiomicCoreness/hello_world.py.git
cd hello_world.py/ios/ClarkePocket
xcodegen generate              # writes ClarkePocket.xcodeproj
open ClarkePocket.xcodeproj
```

Xcode fetches the llama.cpp XCFramework (about 70 MB) the first time and checks its checksum. Then:

1. Select the **ClarkePocket** target and open **Signing & Capabilities**. Tick *Automatically manage signing*
   and set Team to your Apple ID (*Add an Account…* if it isn't listed; a free account shows as
   "Personal Team"). If Xcode says the bundle identifier is taken, change
   `io.github.axiomiccoreness.clarkepocket` to something unique, e.g. `com.mrteanotcoffee.clarkepocket`.
2. Plug in the iPhone, pick **it** as the run destination (a simulator won't build because there's no
   simulator slice), and press **▶ Run**.
3. Only the first time, on the iPhone:
   - **Settings → Privacy & Security → Developer Mode → On**, then restart when asked.
   - **Settings → General → VPN & Device Management →** your Apple ID → **Trust**.
4. Apps signed with a free account **expire after 7 days**. Press Run again from Xcode to renew; the
   downloaded model and history stay on the phone.

### B. Without XcodeGen (plain Xcode)

1. **File → New → Project… → iOS → App**: name `ClarkePocket`, Interface **SwiftUI**, Language **Swift**.
   Delete the generated `ClarkePocketApp.swift` and `ContentView.swift`.
2. Drag **all `.swift` files** from `ClarkePocket/` **and** from `Sources/PocketCore/` into the app
   target. Tick *Copy items if needed* only if you don't want to keep them in the repo.
   (`SHA256Fallback.swift` compiles to nothing on iOS. It's fine to add.)
3. **File → Add Package Dependencies… → Add Local…** → choose the `LlamaBinary` folder, then add the
   **LlamaBinary** library to the ClarkePocket target.
4. Target → **General**: Minimum Deployments **iOS 16.4**. Under Supported Destinations, keep **iPhone** only.
5. Continue with step 1 of A (signing).

## Using it

1. **Model tab → Download** (1.12 GB; use Wi-Fi and keep the app open). After the download the app
   hashes the file in 4 MB pieces with CryptoKit and compares it to the pinned SHA-256. A mismatch
   deletes the file and tells you. **Cancel** keeps what was downloaded, and **Resume download** continues from there.
   - Or use **Import from Files**: pick a `.gguf` (e.g. AirDropped from your PC). It's copied into the
     app and hashed. If it's the pinned file it's marked *verified*; any other GGUF is kept as
     **custom / unverified** and still loads.
   - Models are stored in *Application Support/Models* and **excluded from iCloud/iTunes backup**.
2. **Chat tab**: type and send. The first message loads the model (a few seconds). Watch the answer stream in, and
   tap ■ to stop. Tap **thinking** to read the model's reasoning. **RESET** archives the history
   (moved aside, not deleted), like `/llm reset` on the PC bot.
3. **IRC tab**: plain text goes to the active channel. Commands:
   `/join #chan`, `/part [#chan] [reason]`, `/msg nick|#chan text`, `/me action`, `/nick newnick`,
   `/quit [reason]` (disconnects; **RECONNECT** comes back. The app never closes itself). `//text`
   sends a literal `/text`. Pasted line breaks become spaces, so one input is one IRC line.
   - **answer !llm with the on-device model** (off by default): when someone in the channel writes
     `!llm <question>`, the phone answers with up to 4 lines of ≤ 400 bytes, without the thinking.
     It only answers while the app is **open and in the foreground**, the model is loaded and idle, and
     at most once per 15 s overall and once per 60 s per person. **The PC bot (PR #163, `irc_llm_bot.py`) answers
     `!llm` in the same channel too.** If both are running, people get two answers, so turn this switch
     on only when the PC bot is off.

### Saved history

`Application Support/llm_history.jsonl` uses the same row format as the bridge (PR #166). It's one JSON object
per line with keys in this order: `role`, `content`, `format` (assistant: `"markdown"`), `thinking`
(only if there was any), `session` (`"pocket"`) and `ts`. Python's `json.dumps(…, ensure_ascii=False)`
writes byte-identical lines, and the tests check this. Math is normalised the same way (`\[…\]` → `$$…$$`,
`$…$` → `\(…\)`). The thinking is saved but never sent back to the model. One difference: `ts` carries
the phone's own offset (e.g. `2026-10-30T17:40:00-04:00`), where the bridge writes UTC.

## Memory on a 4 GB iPhone 12

- The weights are **memory-mapped** from the file (1.12 GB), so iOS can page them in and out. The KV cache
  for 2048 tokens is about 57 MB, plus Metal compute buffers.
- Before loading, the app asks iOS how much memory it may still use (`os_proc_available_memory`). If that's
  below its conservative estimate (≈ 0.5 GB + ¼ of the model), it warns and offers **Load anyway**.
- The model is unloaded when you leave the app (Metal can't run in the background) and when iOS sends a
  memory warning. The next chat message loads it again.
- **Increased Memory Limit** (`com.apple.developer.kernel.increased-memory-limit`) is **off by default**.
  Apple's capability table lists the *debugging* memory entitlement for paid programs only and doesn't list
  this one for free accounts. Some people report that a free Personal Team can sign with it, but that's
  unverified. To try it: in `project.yml`, uncomment `CODE_SIGN_ENTITLEMENTS: Optional/IncreasedMemoryLimit.entitlements`,
  then run `xcodegen generate` and Run again. (Plain Xcode: Signing & Capabilities → + Capability → Increased
  Memory Limit.) If signing then fails, remove it again. The app is designed to work without it.

## Tests: what is checked, and what isn't

```sh
cd ios/ClarkePocket && swift test     # Mac or Linux, no Xcode needed
```

- **Unit-tested (`swift test`, 40 cases, also in CI; the real-file hash case is skipped unless the variable below is set)**:
  - the SHA-256 verifier: NIST vectors, the 4 MB chunk boundary, wrong size, wrong hash, cancel, and GGUF magic.
    Set `POCKET_REAL_GGUF=/path/to/deepseek-r2-1.5b-Q4_K_M.gguf` to hash the real 1.1 GB file against the pin
    (done once while writing this: it passes).
  - the history format, byte for byte against the Python bridge.
  - Markdown/LaTeX normalisation and thinking split, also byte for byte.
  - reply segmentation.
  - the IRC parser and the slash-command builder, including CR/LF and CTCP injection attempts.
  - `!llm` wrapping and rate limiting.
  - thread / memory / BOS / prompt-window decisions.
  - UTF-8 streaming.
- **CI** (`.github/workflows/ios-clarke-pocket.yml`):
  - Ubuntu runs `swift test`.
  - macOS runs `swift test` with CryptoKit, then `xcodegen generate` and an **unsigned `xcodebuild` for a generic
    iOS device**. That fetches the pinned llama.cpp framework and **compiles every SwiftUI and llama file**,
    then checks that `llama.framework` is embedded.
- **Run against the real model, but on Linux**: `LlamaEngine.swift` was compiled unchanged against llama.cpp
  b11960's own headers and Linux libraries, and it chatted with the real GGUF on the CPU. That run covered:
  - the template detected from the GGUF.
  - BOS prepended.
  - `<think>` streamed and split off.
  - the prompt window trimmed 80 history turns to 1235 tokens.
  - Stop after 5 tokens.
  - the answer "2 plus 3 equals 5.".
- **Not tested**: running on an actual iPhone. That covers Metal speed, real memory headroom on 4 GB, the
  download UI, the Files import, and the SwiftUI screens themselves. There is no UI test, and no device was
  available. Speed on the A14 has not been measured.

## Troubleshooting

- **"No such module 'llama'" / package errors**: File → Packages → Reset Package Caches, then build again.
  The checksum in `LlamaBinary/Package.swift` must match the zip; it's pinned on purpose.
- **Build fails for a simulator**: expected, because the framework only has a device slice. Pick your iPhone.
- **The app closes while loading**: iOS ran out of memory. Close other apps and try again, or try the optional
  memory entitlement above.
- **IRC stays amber**: the network blocks port 6680 or WebSockets. Try mobile data.
- **Download stops when you switch apps**: iOS pauses it. Come back and tap **Resume download**.
