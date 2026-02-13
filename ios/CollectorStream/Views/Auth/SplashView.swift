import SwiftUI

/// Splash screen with logo that shows on app launch
struct SplashView: View {
    @State private var isActive = false
    @State private var opacity = 0.0

    var body: some View {
        if isActive {
            ContentView()
        } else {
            ZStack {
                // Black background
                Color.black
                    .ignoresSafeArea()

                // CollectorStream Logo
                VStack(spacing: 8) {
                    // Logo SVG (graduation cap icon from portal)
                    Image(systemName: "graduationcap.fill")
                        .font(.system(size: 80))
                        .foregroundColor(Theme.Colors.accent)

                    // App name
                    HStack(spacing: 0) {
                        Text("Collector")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(.white)
                        Text("Stream")
                            .font(.system(size: 32, weight: .bold))
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

                // Transition to login after 2 seconds
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    withAnimation(.easeOut(duration: 0.5)) {
                        isActive = true
                    }
                }
            }
        }
    }
}

#Preview {
    SplashView()
}
