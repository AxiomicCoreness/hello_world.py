// swift-tools-version:5.9
// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// llama.cpp for the app, as ONE universal XCFramework built from llama.cpp source by this repo's
// own workflow .github/workflows/pocket-llama-xcframework.yml (llama.cpp's build-xcframework.sh
// with ios-device ios-sim macos), pinned to release b11960 — the build behind llama.cpp v0.8.0,
// commit 8642541b255bfb5dc39cd351a178be09013a55d6. No third-party binary.
//
// Published as an asset of this repo's release pocket-llama-b11960-xcf by workflow run
// https://github.com/AxiomicCoreness/hello_world.py/actions/runs/41259098995
// (workflow commit 1b972f1f4512ceea393c3f086dd8cacca02a8718), 116 269 595 bytes.
// checksum = sha256 of the zip = `swift package compute-checksum` = GitHub's asset digest.
// Slices: ios-arm64 (iPhone), ios-arm64_x86_64-simulator (iOS Simulator), macos-arm64_x86_64.
//
// The framework is dynamic (SwiftPM embeds and signs it in the app) with MinimumOSVersion 16.4,
// so the app targets iOS 16.4+. Module `llama` (`import llama`); links Metal, Accelerate, libc++.
import PackageDescription

let package = Package(
    name: "LlamaBinary",
    platforms: [.iOS("16.4"), .macOS(.v13)],
    products: [
        .library(name: "LlamaBinary", targets: ["llama"]),
    ],
    targets: [
        .binaryTarget(
            name: "llama",
            url: "https://github.com/AxiomicCoreness/hello_world.py/releases/download/pocket-llama-b11960-xcf/llama-b11960-universal-xcframework.zip",
            checksum: "62b38fdbdf8a53bc2371abb48be2677296c5f7f4956006c910fe737ce773220c"
        ),
    ]
)
