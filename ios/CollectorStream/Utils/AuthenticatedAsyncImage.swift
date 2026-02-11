import SwiftUI

/// AsyncImage that includes authentication token in requests
struct AuthenticatedAsyncImage<Content: View, Placeholder: View>: View {
    let url: URL
    let content: (Image) -> Content
    let placeholder: () -> Placeholder

    @State private var loadedImage: UIImage?
    @State private var isLoading = true
    @State private var loadError: Error?

    var body: some View {
        Group {
            if let image = loadedImage {
                content(Image(uiImage: image))
            } else if isLoading {
                placeholder()
            } else {
                placeholder()
            }
        }
        .task {
            await loadImage()
        }
    }

    private func loadImage() async {
        isLoading = true
        loadError = nil

        var request = URLRequest(url: url)

        // Add authentication token if available
        if let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("🖼️ Invalid response for image: \(url.absoluteString)")
                isLoading = false
                return
            }

            if httpResponse.statusCode == 200 {
                if let image = UIImage(data: data) {
                    loadedImage = image
                    print("✅ Loaded image: \(url.lastPathComponent)")
                } else {
                    print("❌ Failed to decode image data: \(url.lastPathComponent)")
                }
            } else {
                print("❌ Image load failed with status \(httpResponse.statusCode): \(url.lastPathComponent)")
            }

            isLoading = false
        } catch {
            // Ignore cancellation errors (happens when switching tabs)
            if (error as NSError).code == NSURLErrorCancelled {
                // Silent - this is normal when navigating away
                return
            }

            print("❌ Error loading image: \(error.localizedDescription)")
            print("   URL: \(url.absoluteString)")
            loadError = error
            isLoading = false
        }
    }
}

// Convenience initializer matching AsyncImage
extension AuthenticatedAsyncImage where Content == Image, Placeholder == Color {
    init(url: URL) {
        self.url = url
        self.content = { $0 }
        self.placeholder = { Color.gray }
    }
}
