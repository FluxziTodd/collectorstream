import SwiftUI

@main
struct CollectorStreamApp: App {
    @StateObject private var authManager = AuthManager()
    @StateObject private var cardStore = CardStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
                .environmentObject(cardStore)
                .preferredColorScheme(.dark)
        }
    }
}
