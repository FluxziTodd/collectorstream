import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var showSplash = true
    @State private var opacity = 0.0

    var body: some View {
        Group {
            if showSplash {
                // Splash screen
                ZStack {
                    Color.black
                        .ignoresSafeArea()

                    // Logo matching portal design
                    HStack(spacing: 12) {
                        Image(systemName: "bolt.fill")
                            .font(.system(size: 40, weight: .bold))
                            .foregroundColor(Theme.Colors.accent)

                        HStack(spacing: 4) {
                            Text("Collector")
                                .font(.system(size: 36, weight: .bold))
                                .foregroundColor(.white)
                            Text("Stream")
                                .font(.system(size: 36, weight: .bold))
                                .foregroundColor(Theme.Colors.accent)
                        }
                    }
                    .opacity(opacity)
                }
                .onAppear {
                    // Fade in animation
                    withAnimation(.easeIn(duration: 0.8)) {
                        opacity = 1.0
                    }

                    // Transition to main app after 2 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                        withAnimation(.easeOut(duration: 0.5)) {
                            showSplash = false
                        }
                    }
                }
            } else {
                // Main app content
                Group {
                    if authManager.isAuthenticated {
                        MainTabView()
                    } else {
                        AuthenticationView()
                    }
                }
                .animation(.easeInOut, value: authManager.isAuthenticated)
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthManager())
        .environmentObject(CardStore())
}
