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

This folder is source. You build it with Xcode on a Mac, or, without a Mac, download the **unsigned
`.ipa`** that CI builds and sign it with Sideloadly (section C). A free Apple ID is enough either way. It targets an **iPhone 12 (A14, 4 GB)** and anything newer.

| | |
|---|---|
| Model | `ClarkeYoursaTee (deepseek-r2-1.5b)`, `deepseek-r2-1.5b-Q4_K_M.gguf`, 1 117 320 640 bytes (1.12 GB), sha256 `80a49c2f…79e5c1`, from this repo's release [`model-deepseek-r2-1.5b-q4km-v1`](https://github.com/AxiomicCoreness/hello_world.py/releases/tag/model-deepseek-r2-1.5b-q4km-v1) (`Sources/PocketCore/ModelPin.swift`). Selectable in code: `ModelPin.selected` (default `.deepseekR2_1p5b`; `.deepseekR2_1p8b` = `deepseek-r2-1p8b-Q4_K_M.gguf`, 1 259 979 680 bytes, sha256 `f19e0c500c4f734c6e8860e9f6e730e36d544c5f9500f74dce5339b188253af4`, release `model-deepseek-r2-1p8b-q4km-v1`, not the default until its eval is reviewed) |
| Engines | **Primary: MLX Swift** with Clarke Yoursa Tee's own MLX-converted model (`MLXEngine`, pin `MLXModelPin`). **Not active yet**: the MLX Swift package is not linked in this build and no MLX-converted model is published, so `EngineSelector` always picks the fallback today. **Fallback: llama.cpp** (`LlamaEngine`, the pinned 1.5B GGUF). The fallback is chosen automatically in the Simulator, without Metal, when MLX is not linked, or when the MLX model is missing or fails its SHA-256 check. It can also be forced with the Chat tab **ENGINE** menu, and the Chat header names the active engine |
| Fallback inference | llama.cpp release **b11960** (the build behind llama.cpp v0.8.0, commit `8642541b255bfb5dc39cd351a178be09013a55d6`), built from source by this repo's workflow `.github/workflows/pocket-llama-xcframework.yml` into one universal XCFramework (ios-arm64, ios-arm64_x86_64-simulator, macos-arm64_x86_64), published as the asset `llama-b11960-universal-xcframework.zip` of this repo's release `pocket-llama-b11960-xcf` and pinned by checksum in `LlamaBinary/Package.swift` |
| Settings | context 2048 tokens · all layers on Metal · 2 generation / 4 batch threads on the A14 (from its 2 performance cores) · temperature 0.6, top-p 0.95 (read from the GGUF) · chat template from the GGUF |
| IRC | `wss://irc.abjects.net:6680/`, starts in `#axiomiccoreness`, nick `Clarke_iOS_<4 digits>` |
| Look | the TeaVM rhythm page's chat column (`Theme.swift`, copied from PR #165) |
| Minimum iOS | **16.4** (the llama.cpp framework is built for 16.4+). Runs on a real iPhone **and in the iOS Simulator** (CI builds, tests, installs and launches it there on every PR) |

## Files

| Path | What it is |
|---|---|
| `project.yml` | XcodeGen spec that generates `ClarkePocket.xcodeproj` (not committed) |
| `LlamaBinary/Package.swift` | local Swift package wrapping the universal llama.cpp XCFramework from this repo's release (URL + checksum) |
| `ClarkePocket/ClarkePocketApp.swift` | `@main`, tabs, foreground/background handling |
| `ClarkePocket/ChatEngine.swift` | `ChatEngine` protocol; `MLXEngine` (primary, refuses until MLX is linked and a model is pinned); `EngineDetector` (Simulator / Metal / MLX file check) |
| `Sources/PocketCore/EngineSelection.swift` | MLX-primary / llama.cpp-fallback selection, `MLXModelPin`, per-file SHA-256 check (tested offline in `EngineSelectionTests`) |
| `ClarkePocket/LlamaEngine.swift` | llama.cpp C API wrapper (`actor`): load, chat template, tokenize, prefill, stream, stop |
| `ClarkePocket/ModelStore.swift` | download / import / SHA-256 check / load / unload, plus the generation lock for one answer at a time |
| `ClarkePocket/ModelView.swift` | Model tab |
| `ClarkePocket/ChatStore.swift`, `ChatView.swift`, `MarkdownText.swift` | Chat tab, saved history, Markdown + math rendering |
| `ClarkePocket/IRCClient.swift` | copied from PR #165, then adapted: slash commands, active channel, responder hook |
| `ClarkePocket/IRCView.swift`, `IRCResponder.swift` | IRC tab and the optional on-device `!llm` answerer |
| `ClarkePocket/MemoryMonitor.swift`, `Theme.swift`, `Info.plist` | free-memory / P-core queries, colours (copied from #165), app plist |
| `Sources/PocketCore/*.swift` | pure-Foundation core, compiled into the app and unit-tested: model pin + SHA-256 verifier, history format, Markdown/LaTeX port, IRC parser (copied from #165), slash-command builder, `!llm` reply wrapper + rate limiter, runtime policy, UTF-8 stream assembler |
| `Tests/PocketCoreTests/` | 40 XCTest cases (`swift test`), including byte-for-byte checks against the Python bridge |
| `Tests/ClarkePocketAppTests/` | app-hosted XCTests: the linked llama.framework runs (system info, a missing path and a stub file fail cleanly, no weights), default pin stays 1.5B |
| `Tests/ClarkePocketUITests/` | UI smoke test: launch, visit Model / Chat / IRC, screenshot each |
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

Xcode fetches the universal llama.cpp XCFramework (about 116 MB) the first time and checks its checksum. Then:

1. Select the **ClarkePocket** target and open **Signing & Capabilities**. Tick *Automatically manage signing*
   and set Team to your Apple ID (*Add an Account…* if it isn't listed; a free account shows as
   "Personal Team"). If Xcode says the bundle identifier is taken, change
   `io.github.axiomiccoreness.clarkepocket` to something unique, e.g. `com.mrteanotcoffee.clarkepocket`.
2. Plug in the iPhone, pick **it** as the run destination, and press **▶ Run**. An iPhone Simulator
   works too (no signing needed there); launch argument `-ircAutoConnect NO` keeps it off IRC.
3. Only the first time, on the iPhone:
   - **Settings → Privacy & Security → Developer Mode → On**, then restart when asked.
   - **Settings → General → VPN & Device Management →** your Apple ID → **Trust**.
4. Apps signed with a free account **expire after 7 days**. Press Run again from Xcode to renew; the
   downloaded model and history stay on the phone.

### C. Without a Mac: unsigned `.ipa` + Sideloadly (Windows)

The workflow `.github/workflows/ios-clarke-pocket.yml` builds an **unsigned Release** app for iPhone on
every change and uploads it as the artifact **`ClarkePocket-unsigned-ipa`** (kept 14 days):
`ClarkePocket-unsigned.ipa` plus `ClarkePocket-unsigned.ipa.sha256`. CI checks that it holds only
`Payload/ClarkePocket.app`, has no signature and no entitlements, embeds `Frameworks/llama.framework`,
is arm64, and that its `Info.plist` says bundle id `io.github.axiomiccoreness.clarkepocket`, version 1.0 (1),
iOS 16.4+, iPhone only. Running the workflow by hand with **prerelease** ticked also attaches it to a
GitHub pre-release.

1. Open the latest green run of **iOS Clarke Pocket** under **Actions**, download
   `ClarkePocket-unsigned-ipa` (a zip; downloading needs a GitHub login) and unzip it.
   Optionally check it: `certutil -hashfile ClarkePocket-unsigned.ipa SHA256` should match the `.sha256` file.
2. Install Sideloadly. On Windows it also needs **iTunes and iCloud from apple.com** (not the Microsoft
   Store versions) so it can see the phone.
3. Plug in the iPhone, drop the `.ipa` on Sideloadly, enter your Apple ID and press **Start**.
   If it says the bundle id is unavailable, set a unique one under *Advanced options*
   (e.g. `com.mrteanotcoffee.clarkepocket`).
4. On the iPhone: **Developer Mode → On** and **VPN & Device Management → Trust**, as in section A.
5. Free-account limits: the app **expires after 7 days** (re-sign with Sideloadly to renew; the model and
   history stay if the bundle id is unchanged), at most **3 sideloaded apps** at once per device, and at most
   10 new app ids per 7 days. The optional memory entitlement below is never in this `.ipa`.

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

### Standalone, and the optional PC-bot fallback

The app needs no PC: on first launch the **Model** tab downloads the pinned GGUF from its GitHub
release, checks the exact size and SHA-256, and runs it with llama.cpp on the phone.

To change the model, edit one line in `Sources/PocketCore/ModelPin.swift`:
`public static let selected: ModelPinSpec = .deepseekR2_1p5b`. Each pin has its own file name,
size and SHA-256, so a file downloaded for one pin is never accepted as another.

**Fallback (off by default, IRC tab → "Chat fallback to the PC bot when no local model")**: when
there is no local model file, or it failed to load, Chat sends your question as a **private
message** to the PC bridge's IRC bot (`ClarkeTutorBot`, `sovereign-irc-bridge/src/irc_llm_bot.py`)
over the app's existing IRC connection and shows its `[LLM]` reply lines. The chat header then says
`VIA PC BOT`.
- Only the question is sent. The PC bot uses its own system prompt and its own per-nick history.
- The bot must be running on the PC, and the phone must be connected to IRC. The phone opens no
  port and never connects to the PC directly (the bridge stays bound to 127.0.0.1).
- IRC is plaintext to the network's operators, so leave this off for anything private.
- A reply ends after 4 quiet seconds, on the bot's `…(truncated)` line, or on a NOTICE (for example
  its rate limit). With no answer within 180 s, Chat says the PC bot may be off.
- A low-memory refusal does **not** fall back. You choose **Load anyway** instead.

## Saved history

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
- **Simulator**: supported. The universal XCFramework has an ios-arm64_x86_64-simulator slice; pass `-ircAutoConnect NO` as a launch argument to keep the Simulator off IRC.
- **The app closes while loading**: iOS ran out of memory. Close other apps and try again, or try the optional
  memory entitlement above.
- **IRC stays amber**: the network blocks port 6680 or WebSockets. Try mobile data.
- **Download stops when you switch apps**: iOS pauses it. Come back and tap **Resume download**.
