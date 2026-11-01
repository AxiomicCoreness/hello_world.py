// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The connectome map the rest of the repo uses (com.fruitfly.brain.ConnectomeLoader reads the same
// file): HHMIJaneliaMap.xml. It is a PLACEHOLDER — a hand-written 3-neuron ring (A -> B -> C -> A),
// NOT HHMI Janelia FlyEM hemibrain data. The app bundles a byte-identical copy of
// src/main/resources/HHMIJaneliaMap.xml (a test keeps them identical) and always shows it as a
// placeholder. Anything computed from it here is a simulation and is labelled as one.

import Foundation
#if canImport(FoundationXML)
import FoundationXML
#endif

public struct Synapse: Equatable, Sendable {
    public let from: String
    public let to: String
    public let weight: Double
}

public enum ConnectomeError: Error, Equatable, CustomStringConvertible {
    case malformed(String)
    case unknownNeuron(String)
    case duplicateNeuron(String)
    case badWeight(String)

    public var description: String {
        switch self {
        case .malformed(let m): return "not a connectome map: \(m)"
        case .unknownNeuron(let n): return "connection uses unknown neuron \(n)"
        case .duplicateNeuron(let n): return "neuron \(n) is listed twice"
        case .badWeight(let w): return "connection weight \(w) is not a number"
        }
    }
}

/// A parsed `<hemibrain>` map: `<neuron id=…/>` and `<connection from=… to=… weight=…/>`.
public struct Connectome: Equatable, Sendable {
    /// File name of the placeholder map, as used everywhere in the repo.
    public static let placeholderFileName = "HHMIJaneliaMap.xml"
    /// The only way this app names the file in UI text.
    public static let placeholderLabel =
        "HHMIJaneliaMap.xml (placeholder: hand-written 3-neuron ring, NOT HHMI Janelia FlyEM hemibrain data)"

    public let neurons: [String]
    public let synapses: [Synapse]
    /// True for HHMIJaneliaMap.xml. There is no real connectome in this app.
    public let isPlaceholder: Bool

    public init(neurons: [String], synapses: [Synapse], isPlaceholder: Bool) {
        self.neurons = neurons
        self.synapses = synapses
        self.isPlaceholder = isPlaceholder
    }

    public static func parse(_ data: Data, isPlaceholder: Bool = true) throws -> Connectome {
        let d = Delegate()
        let p = XMLParser(data: data)
        p.delegate = d
        guard p.parse(), d.error == nil else {
            throw d.error ?? .malformed(p.parserError.map { "\($0)" } ?? "XML parse error")
        }
        guard d.sawRoot else { throw ConnectomeError.malformed("no <hemibrain> root") }
        let known = Set(d.neurons)
        for s in d.synapses {
            if !known.contains(s.from) { throw ConnectomeError.unknownNeuron(s.from) }
            if !known.contains(s.to) { throw ConnectomeError.unknownNeuron(s.to) }
        }
        return Connectome(neurons: d.neurons, synapses: d.synapses, isPlaceholder: isPlaceholder)
    }

    private final class Delegate: NSObject, XMLParserDelegate {
        var neurons: [String] = []
        var synapses: [Synapse] = []
        var sawRoot = false
        var error: ConnectomeError?

        func parser(_ parser: XMLParser, didStartElement name: String, namespaceURI: String?,
                    qualifiedName qName: String?, attributes a: [String: String] = [:]) {
            guard error == nil else { return }
            switch name {
            case "hemibrain":
                sawRoot = true
            case "neuron":
                guard let id = a["id"], !id.isEmpty else { error = .malformed("<neuron> without id"); return }
                if neurons.contains(id) { error = .duplicateNeuron(id); return }
                neurons.append(id)
            case "connection":
                guard let f = a["from"], let t = a["to"] else { error = .malformed("<connection> without from/to"); return }
                let wText = a["weight"] ?? "1.0"
                guard let w = Double(wText), w.isFinite else { error = .badWeight(wText); return }
                synapses.append(Synapse(from: f, to: t, weight: w))
            default:
                break
            }
            if error != nil { parser.abortParsing() }
        }
    }
}

/// A tiny leaky integrate-and-fire run over a connectome. A SIMULATION, not recorded neural data,
/// and on the placeholder map it says nothing about a real fly brain. Deterministic: the same
/// inputs give the same spikes on every platform.
public struct ConnectomeSimulation: Sendable {
    public static let label = "Simulation (leaky integrate-and-fire on the placeholder map; not recorded neural data)"
    public let isSimulation = true

    public var leak: Double = 0.9          // v <- v * leak each step
    public var threshold: Double = 0.75    // spike when v >= threshold, then reset to 0
    public var inputCurrent: Double = 1.0  // injected into the stimulated neuron at step 0

    public init() {}

    /// Per step, the neurons that spiked (in map order).
    public func run(_ c: Connectome, stimulate: String, steps: Int) -> [[String]] {
        var v = [String: Double](uniqueKeysWithValues: c.neurons.map { ($0, 0) })
        var spiked: Set<String> = []
        var raster: [[String]] = []
        for step in 0..<max(0, steps) {
            var next = v
            for n in c.neurons { next[n] = (v[n] ?? 0) * leak }
            for s in c.synapses where spiked.contains(s.from) { next[s.to, default: 0] += s.weight }
            if step == 0, next[stimulate] != nil { next[stimulate]! += inputCurrent }
            var now: Set<String> = []
            for n in c.neurons where (next[n] ?? 0) >= threshold {
                now.insert(n)
                next[n] = 0
            }
            raster.append(c.neurons.filter { now.contains($0) })
            v = next
            spiked = now
        }
        return raster
    }
}
