import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var cardStore: CardStore

    @State private var showChangePassword = false
    @State private var showLogoutConfirmation = false

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: Theme.Spacing.lg) {
                        // Profile Header
                        ProfileHeader(user: authManager.currentUser)

                        // Collection Stats
                        CollectionStatsCard(cardStore: cardStore)

                        // Settings Menu
                        SettingsMenu(
                            showChangePassword: $showChangePassword,
                            showLogoutConfirmation: $showLogoutConfirmation
                        )

                        // App Info
                        AppInfoSection()
                    }
                    .padding(Theme.Spacing.lg)
                }
            }
            .navigationTitle("Profile")
            .sheet(isPresented: $showChangePassword) {
                ChangePasswordView()
            }
            .confirmationDialog("Logout?", isPresented: $showLogoutConfirmation, titleVisibility: .visible) {
                Button("Logout", role: .destructive) {
                    authManager.logout()
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to logout?")
            }
        }
    }
}

// MARK: - Profile Header
struct ProfileHeader: View {
    let user: AuthManager.User?

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                // Avatar
                ZStack {
                    Circle()
                        .fill(Theme.Colors.accent.opacity(0.2))
                        .frame(width: 80, height: 80)

                    Text(initials)
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(Theme.Colors.accent)
                }

                // User Info
                VStack(spacing: 4) {
                    Text(user?.username ?? "User")
                        .font(Theme.Typography.title3)
                        .foregroundColor(Theme.Colors.textPrimary)

                    Text(user?.email ?? "")
                        .font(Theme.Typography.subheadline)
                        .foregroundColor(Theme.Colors.textSecondary)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, Theme.Spacing.md)
        }
    }

    private var initials: String {
        guard let username = user?.username else { return "U" }
        return String(username.prefix(2)).uppercased()
    }
}

// MARK: - Collection Stats Card
struct CollectionStatsCard: View {
    @ObservedObject var cardStore: CardStore

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                HStack {
                    Image(systemName: "rectangle.stack.fill")
                        .foregroundColor(Theme.Colors.accent)
                    Text("Collection Overview")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                HStack(spacing: Theme.Spacing.xl) {
                    StatItem(value: "\(cardStore.totalCards)", label: "Cards")
                    StatItem(value: "$\(Int(cardStore.totalValue))", label: "Est. Value")
                    StatItem(value: "\(cardStore.cardsBySport.count)", label: "Sports")
                }
            }
        }
    }
}

struct StatItem: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(Theme.Typography.title2)
                .fontWeight(.bold)
                .foregroundColor(Theme.Colors.accent)

            Text(label)
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textSecondary)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Settings Menu
struct SettingsMenu: View {
    @Binding var showChangePassword: Bool
    @Binding var showLogoutConfirmation: Bool

    var body: some View {
        CardContainer {
            VStack(spacing: 0) {
                SettingsRow(icon: "key.fill", title: "Change Password", showDivider: true) {
                    showChangePassword = true
                }

                SettingsRow(icon: "bell.fill", title: "Notifications", showDivider: true) {
                    // TODO: Notifications settings
                }

                SettingsRow(icon: "questionmark.circle.fill", title: "Help & Support", showDivider: true) {
                    // TODO: Help
                }

                SettingsRow(icon: "arrow.right.square.fill", title: "Logout", showDivider: false, isDestructive: true) {
                    showLogoutConfirmation = true
                }
            }
        }
    }
}

struct SettingsRow: View {
    let icon: String
    let title: String
    var showDivider: Bool = true
    var isDestructive: Bool = false
    let action: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Button(action: action) {
                HStack(spacing: Theme.Spacing.md) {
                    Image(systemName: icon)
                        .font(.system(size: 20))
                        .foregroundColor(isDestructive ? Theme.Colors.danger : Theme.Colors.accent)
                        .frame(width: 24)

                    Text(title)
                        .font(Theme.Typography.body)
                        .foregroundColor(isDestructive ? Theme.Colors.danger : Theme.Colors.textPrimary)

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 14))
                        .foregroundColor(Theme.Colors.textMuted)
                }
                .padding(.vertical, Theme.Spacing.md)
            }

            if showDivider {
                Divider()
                    .background(Theme.Colors.border)
            }
        }
    }
}

// MARK: - App Info Section
struct AppInfoSection: View {
    var body: some View {
        VStack(spacing: Theme.Spacing.sm) {
            LogoView(size: 24)

            Text("Version 1.0.0")
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textMuted)

            Link("collectorstream.com", destination: URL(string: "https://collectorstream.com")!)
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.accent)
        }
        .padding(.top, Theme.Spacing.lg)
    }
}

// MARK: - Change Password View
struct ChangePasswordView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var authManager: AuthManager

    @State private var currentPassword = ""
    @State private var newPassword = ""
    @State private var confirmPassword = ""
    @State private var showSuccess = false

    private var isValid: Bool {
        !currentPassword.isEmpty && !newPassword.isEmpty && newPassword == confirmPassword && newPassword.count >= 8
    }

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: Theme.Spacing.lg) {
                    VStack(spacing: Theme.Spacing.md) {
                        ThemedTextField(
                            placeholder: "Current Password",
                            text: $currentPassword,
                            isSecure: true
                        )

                        ThemedTextField(
                            placeholder: "New Password",
                            text: $newPassword,
                            isSecure: true
                        )

                        ThemedTextField(
                            placeholder: "Confirm New Password",
                            text: $confirmPassword,
                            isSecure: true
                        )

                        if !confirmPassword.isEmpty && newPassword != confirmPassword {
                            Text("Passwords do not match")
                                .font(Theme.Typography.footnote)
                                .foregroundColor(Theme.Colors.danger)
                        }

                        if !newPassword.isEmpty && newPassword.count < 8 {
                            Text("Password must be at least 8 characters")
                                .font(Theme.Typography.footnote)
                                .foregroundColor(Theme.Colors.warning)
                        }
                    }

                    if let error = authManager.errorMessage {
                        Text(error)
                            .font(Theme.Typography.footnote)
                            .foregroundColor(Theme.Colors.danger)
                    }

                    PrimaryButton(
                        title: "Change Password",
                        action: {
                            Task {
                                let success = await authManager.changePassword(
                                    currentPassword: currentPassword,
                                    newPassword: newPassword
                                )
                                if success {
                                    showSuccess = true
                                }
                            }
                        },
                        isLoading: authManager.isLoading,
                        isDisabled: !isValid
                    )

                    Spacer()
                }
                .padding(Theme.Spacing.lg)
            }
            .navigationTitle("Change Password")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(Theme.Colors.accent)
                }
            }
            .alert("Password Changed", isPresented: $showSuccess) {
                Button("OK") { dismiss() }
            } message: {
                Text("Your password has been changed successfully.")
            }
        }
    }
}

#Preview {
    ProfileView()
        .environmentObject(AuthManager())
        .environmentObject(CardStore())
        .preferredColorScheme(.dark)
}
