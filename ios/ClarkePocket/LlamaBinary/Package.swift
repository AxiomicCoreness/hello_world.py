// swift-tools-version:5.9
// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// llama.cpp for the app, as the prebuilt XCFramework that llama.cpp's own release CI publishes
// (docs/xcframework.md upstream). Pinned to release b11960 — the build behind llama.cpp v0.8.0
// (v0.8.0's nightly-tag.txt = b11960; commit 8642541b255bfb5dc39cd351a178be09013a55d6).
//
// checksum = sha256 of the zip. Checked 2026-10-30 against GitHub's asset digest
// (sha256:feba05e0…d759, 69 691 024 bytes) and `swift package compute-checksum`.
// Slices in this zip: ios-arm64 (iPhone) and macos-arm64_x86_64. There is NO simulator slice,
// so the app builds for a real iPhone only.
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
            url: "https://github.com/ggml-org/llama.cpp/releases/download/b11960/llama-b11960-xcframework.zip",
            checksum: "feba05e0b7cb5e682ae3354abb455bf9723ae2cc95c69e24d073264e6a34d759"
        ),
    ]
)
