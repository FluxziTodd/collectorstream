import SwiftUI

// MARK: - Primary Button
struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var isLoading: Bool = false
    var isDisabled: Bool = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: Theme.Spacing.sm) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                }
                Text(title)
                    .font(Theme.Typography.headline)
                    .foregroundColor(.white)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 50)
            .background(Theme.Gradients.accent)
            .cornerRadius(Theme.CornerRadius.medium)
        }
        .disabled(isDisabled || isLoading)
        .opacity(isDisabled ? 0.5 : 1.0)
    }
}

// MARK: - Secondary Button
struct SecondaryButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(Theme.Typography.headline)
                .foregroundColor(Theme.Colors.accent)
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Theme.Colors.bgCard)
                .overlay(
                    RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                        .stroke(Theme.Colors.accent, lineWidth: 1)
                )
                .cornerRadius(Theme.CornerRadius.medium)
        }
    }
}

// MARK: - Text Field
struct ThemedTextField: View {
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboardType: UIKeyboardType = .default
    var autocapitalization: TextInputAutocapitalization = .sentences

    var body: some View {
        Group {
            if isSecure {
                SecureField(placeholder, text: $text)
            } else {
                TextField(placeholder, text: $text)
                    .keyboardType(keyboardType)
                    .textInputAutocapitalization(autocapitalization)
            }
        }
        .font(Theme.Typography.body)
        .foregroundColor(Theme.Colors.textPrimary)
        .padding()
        .background(Theme.Colors.bgCard)
        .overlay(
            RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                .stroke(Theme.Colors.border, lineWidth: 1)
        )
        .cornerRadius(Theme.CornerRadius.medium)
    }
}

// MARK: - Card Container
struct CardContainer<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(Theme.Spacing.md)
            .background(Theme.Colors.bgCard)
            .cornerRadius(Theme.CornerRadius.medium)
            .overlay(
                RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                    .stroke(Theme.Colors.border, lineWidth: 1)
            )
    }
}

// MARK: - Logo View
struct LogoView: View {
    var size: CGFloat = 32

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: size))
                .foregroundColor(Theme.Colors.accent)

            Text("Collector")
                .font(.system(size: size * 0.75, weight: .bold))
                .foregroundColor(Theme.Colors.textPrimary)
            +
            Text("Stream")
                .font(.system(size: size * 0.75, weight: .bold))
                .foregroundColor(Theme.Colors.accent)
        }
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    var message: String = "Loading..."

    var body: some View {
        ZStack {
            Theme.Colors.bgPrimary.opacity(0.8)
                .ignoresSafeArea()

            VStack(spacing: Theme.Spacing.md) {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: Theme.Colors.accent))
                    .scaleEffect(1.5)

                Text(message)
                    .font(Theme.Typography.subheadline)
                    .foregroundColor(Theme.Colors.textSecondary)
            }
            .padding(Theme.Spacing.xl)
            .background(Theme.Colors.bgCard)
            .cornerRadius(Theme.CornerRadius.large)
        }
    }
}

// MARK: - Empty State View
struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Image(systemName: icon)
                .font(.system(size: 64))
                .foregroundColor(Theme.Colors.textMuted)

            VStack(spacing: Theme.Spacing.sm) {
                Text(title)
                    .font(Theme.Typography.title3)
                    .foregroundColor(Theme.Colors.textPrimary)

                Text(message)
                    .font(Theme.Typography.body)
                    .foregroundColor(Theme.Colors.textSecondary)
                    .multilineTextAlignment(.center)
            }

            if let actionTitle = actionTitle, let action = action {
                PrimaryButton(title: actionTitle, action: action)
                    .frame(width: 200)
            }
        }
        .padding(Theme.Spacing.xl)
    }
}

// MARK: - Top Accent Bar
struct TopAccentBar: View {
    var body: some View {
        Theme.Gradients.topBar
            .frame(height: 3)
            .ignoresSafeArea(edges: .horizontal)
    }
}
