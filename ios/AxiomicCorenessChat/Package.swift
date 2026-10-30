// swift-tools-version:5.9
// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Only for `swift test` of the pure-Foundation IRC parser (IRCLine.swift) on a Mac or Linux.
// The app itself is built from an Xcode iOS App project — see README.md.
import PackageDescription

let package = Package(
    name: "AxiomicCorenessChat",
    targets: [
        .target(name: "AxiomicCorenessChat", path: "AxiomicCorenessChat",
                // SwiftUI/Combine app files are built by Xcode, not by SwiftPM.
                exclude: ["AxiomicCorenessChatApp.swift", "ChatView.swift", "IRCClient.swift", "Theme.swift"]),
        .testTarget(name: "AxiomicCorenessChatTests", dependencies: ["AxiomicCorenessChat"],
                    path: "AxiomicCorenessChatTests"),
    ]
)
