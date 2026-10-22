// RenderClient.swift
import UIKit
import Foundation

struct RenderResult {
    let image: UIImage
    let pixelWidth: Int
    let pixelHeight: Int
    let dpi: Int
}

enum RenderError: Error { case badStatus(Int, String), notPNG }

func fetchRender(base: URL, widthIn: Double = 2, heightIn: Double = 3, dpi: Int = 300) async throws -> RenderResult {
    var c = URLComponents(url: base.appendingPathComponent("render"), resolvingAgainstBaseURL: false)!
    c.queryItems = [
        URLQueryItem(name: "widthIn", value: String(widthIn)),
        URLQueryItem(name: "heightIn", value: String(heightIn)),
        URLQueryItem(name: "dpi", value: String(dpi)),
    ]
    let (data, response) = try await URLSession.shared.data(from: c.url!)
    guard let http = response as? HTTPURLResponse else { throw RenderError.notPNG }
    guard http.statusCode == 200 else {
        throw RenderError.badStatus(http.statusCode, String(decoding: data, as: UTF8.self))
    }
    // scale: 1 keeps the image's pixel size as-is
    guard http.value(forHTTPHeaderField: "Content-Type") == "image/png",
          let img = UIImage(data: data, scale: 1) else { throw RenderError.notPNG }
    func h(_ k: String) -> Int { Int(http.value(forHTTPHeaderField: k) ?? "") ?? 0 }
    return RenderResult(image: img,
                        pixelWidth: h("X-Render-Pixel-Width"),
                        pixelHeight: h("X-Render-Pixel-Height"),
                        dpi: h("X-Render-Dpi"))
}
