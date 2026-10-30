// swift-tools-version:5.9
// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Only for `swift test` of the pure-Foundation core (Sources/PocketCore) on a Mac or Linux.
// The iPhone app is generated from project.yml (XcodeGen), which compiles Sources/PocketCore
// straight into the app target and links llama.cpp through LlamaBinary/ — see README.md.
//
// No dependencies: Apple platforms hash with CryptoKit; on Linux (tests only) a small pure-Swift
// SHA-256 with the same API is compiled instead (Sources/PocketCore/SHA256Fallback.swift).
import PackageDescription

let package = Package(
    name: "ClarkePocket",
    platforms: [.macOS(.v13), .iOS("16.4")],
    products: [
        .library(name: "PocketCore", targets: ["PocketCore"]),
    ],
    targets: [
        .target(name: "PocketCore", path: "Sources/PocketCore"),
        .testTarget(name: "PocketCoreTests", dependencies: ["PocketCore"], path: "Tests/PocketCoreTests",
                    exclude: ["Fixtures"]),   // read from disk via #filePath
    ]
)
