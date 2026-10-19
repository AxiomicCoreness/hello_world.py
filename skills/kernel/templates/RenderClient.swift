// RenderClient.swift: fetch a 300 dpi PNG from the demo Java endpoint (GET /render).
// The server binds 127.0.0.1:8025 by default. On an iPhone, 127.0.0.1 is the phone
// itself, so the phone must reach the server over the network: start it with
// -Dhost=0.0.0.0 on a LAN IP (e.g. http://192.168.1.20:8025) or put it behind HTTPS.
// Plain http:// to a LAN host also needs an App Transport Security exception
// (NSAppTransportSecurity > NSAllowsLocalNetworking) in Info.plist.
import UIKit

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
    let http = response as! HTTPURLResponse
    guard http.statusCode == 200 else {
        throw RenderError.badStatus(http.statusCode, String(decoding: data, as: UTF8.self))
    }
    // scale: 1 keeps the image's pixel size as-is; UIImage(data:) does not read pHYs.
    guard http.value(forHTTPHeaderField: "Content-Type") == "image/png",
          let img = UIImage(data: data, scale: 1) else { throw RenderError.notPNG }
    func h(_ k: String) -> Int { Int(http.value(forHTTPHeaderField: k) ?? "") ?? 0 }
    return RenderResult(image: img,
                        pixelWidth: h("X-Render-Pixel-Width"),
                        pixelHeight: h("X-Render-Pixel-Height"),
                        dpi: h("X-Render-Dpi"))
}

// Usage:
// let r = try await fetchRender(base: URL(string: "http://192.168.1.20:8025")!)
// print(r.pixelWidth, r.pixelHeight, r.dpi)   // 600 900 300
