// ContentView.swift
import SwiftUI

struct ContentView: View {
    @State private var image: UIImage? = nil
    @State private var statusText: String = "Ready to render"
    @State private var isLoading: Bool = false
    
    // Change this to your Mac's LAN IP where the Java server is running
    let serverBaseURL = URL(string: "http://192.168.1.20:8025")!
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Sovereign Renderer")
                .font(.title)
                .bold()
            
            Text(statusText)
                .font(.caption)
                .foregroundColor(.gray)
            
            if let image = image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 400)
                    .border(Color.black, width: 1)
            } else {
                Rectangle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 400)
                    .overlay(Text("No Image").foregroundColor(.gray))
            }
            
            Button(action: {
                Task { await loadRender() }
            }) {
                if isLoading {
                    ProgressView()
                } else {
                    Text("Fetch 300 DPI Render")
                        .bold()
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
            }
            .disabled(isLoading)
        }
        .padding()
    }
    
    @MainActor
    func loadRender() async {
        isLoading = true
        statusText = "Connecting to \(serverBaseURL.absoluteString)..."
        do {
            let result = try await fetchRender(base: serverBaseURL)
            self.image = result.image
            self.statusText = "Success: \(result.pixelWidth)x\(result.pixelHeight) @ \(result.dpi) DPI"
        } catch {
            self.statusText = "Error: \(error.localizedDescription)"
        }
        isLoading = false
    }
}
