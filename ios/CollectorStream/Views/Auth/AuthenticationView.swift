import SwiftUI

struct AuthenticationView: View {
    @State private var showLogin = true

    var body: some View {
        ZStack {
            Theme.Colors.bgPrimary
                .ignoresSafeArea()

            VStack(spacing: 0) {
                TopAccentBar()

                ScrollView {
                    VStack(spacing: Theme.Spacing.xl) {
                        // Logo
                        VStack(spacing: Theme.Spacing.md) {
                            Image(systemName: "chart.line.uptrend.xyaxis")
                                .font(.system(size: 64))
                                .foregroundColor(Theme.Colors.accent)

                            LogoView(size: 40)

                            Text("Track Your Sports Card Collection")
                                .font(Theme.Typography.subheadline)
                                .foregroundColor(Theme.Colors.textSecondary)
                        }
                        .padding(.top, Theme.Spacing.xxl)

                        // Auth Form
                        if showLogin {
                            LoginView(showLogin: $showLogin)
                        } else {
                            RegisterView(showLogin: $showLogin)
                        }
                    }
                    .padding(.horizontal, Theme.Spacing.lg)
                    .padding(.bottom, Theme.Spacing.xxl)
                }
            }
        }
    }
}

// MARK: - Login View
struct LoginView: View {
    @Binding var showLogin: Bool
    @EnvironmentObject var authManager: AuthManager

    @State private var email = ""
    @State private var password = ""
    @State private var showForgotPassword = false

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            // Form
            VStack(spacing: Theme.Spacing.md) {
                ThemedTextField(
                    placeholder: "Email",
                    text: $email,
                    keyboardType: .emailAddress,
                    autocapitalization: .never
                )

                ThemedTextField(
                    placeholder: "Password",
                    text: $password,
                    isSecure: true
                )
            }

            // Error Message
            if let error = authManager.errorMessage {
                Text(error)
                    .font(Theme.Typography.footnote)
                    .foregroundColor(Theme.Colors.danger)
                    .multilineTextAlignment(.center)
            }

            // Forgot Password
            Button(action: { showForgotPassword = true }) {
                Text("Forgot Password?")
                    .font(Theme.Typography.subheadline)
                    .foregroundColor(Theme.Colors.accent)
            }

            // Login Button
            PrimaryButton(
                title: "Sign In",
                action: {
                    Task {
                        await authManager.login(email: email, password: password)
                    }
                },
                isLoading: authManager.isLoading,
                isDisabled: email.isEmpty || password.isEmpty
            )

            // Divider
            HStack {
                Rectangle()
                    .fill(Theme.Colors.border)
                    .frame(height: 1)

                Text("or")
                    .font(Theme.Typography.footnote)
                    .foregroundColor(Theme.Colors.textMuted)

                Rectangle()
                    .fill(Theme.Colors.border)
                    .frame(height: 1)
            }

            // Register Link
            Button(action: { showLogin = false }) {
                HStack(spacing: 4) {
                    Text("Don't have an account?")
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text("Sign Up")
                        .foregroundColor(Theme.Colors.accent)
                        .fontWeight(.semibold)
                }
                .font(Theme.Typography.subheadline)
            }
        }
        .sheet(isPresented: $showForgotPassword) {
            ForgotPasswordView()
        }
    }
}

// MARK: - Register View
struct RegisterView: View {
    @Binding var showLogin: Bool
    @EnvironmentObject var authManager: AuthManager

    @State private var email = ""
    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""

    private var passwordsMatch: Bool {
        password == confirmPassword
    }

    private var isValid: Bool {
        !email.isEmpty && !username.isEmpty && !password.isEmpty && passwordsMatch
    }

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            // Form
            VStack(spacing: Theme.Spacing.md) {
                ThemedTextField(
                    placeholder: "Username",
                    text: $username,
                    autocapitalization: .never
                )

                ThemedTextField(
                    placeholder: "Email",
                    text: $email,
                    keyboardType: .emailAddress,
                    autocapitalization: .never
                )

                ThemedTextField(
                    placeholder: "Password",
                    text: $password,
                    isSecure: true
                )

                ThemedTextField(
                    placeholder: "Confirm Password",
                    text: $confirmPassword,
                    isSecure: true
                )

                if !confirmPassword.isEmpty && !passwordsMatch {
                    Text("Passwords do not match")
                        .font(Theme.Typography.footnote)
                        .foregroundColor(Theme.Colors.danger)
                }
            }

            // Error Message
            if let error = authManager.errorMessage {
                Text(error)
                    .font(Theme.Typography.footnote)
                    .foregroundColor(Theme.Colors.danger)
                    .multilineTextAlignment(.center)
            }

            // Register Button
            PrimaryButton(
                title: "Create Account",
                action: {
                    Task {
                        await authManager.register(
                            email: email,
                            username: username,
                            password: password
                        )
                    }
                },
                isLoading: authManager.isLoading,
                isDisabled: !isValid
            )

            // Divider
            HStack {
                Rectangle()
                    .fill(Theme.Colors.border)
                    .frame(height: 1)

                Text("or")
                    .font(Theme.Typography.footnote)
                    .foregroundColor(Theme.Colors.textMuted)

                Rectangle()
                    .fill(Theme.Colors.border)
                    .frame(height: 1)
            }

            // Login Link
            Button(action: { showLogin = true }) {
                HStack(spacing: 4) {
                    Text("Already have an account?")
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text("Sign In")
                        .foregroundColor(Theme.Colors.accent)
                        .fontWeight(.semibold)
                }
                .font(Theme.Typography.subheadline)
            }
        }
    }
}

// MARK: - Forgot Password View
struct ForgotPasswordView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var authManager: AuthManager

    @State private var email = ""
    @State private var emailSent = false

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: Theme.Spacing.lg) {
                    if emailSent {
                        // Success State
                        VStack(spacing: Theme.Spacing.md) {
                            Image(systemName: "envelope.circle.fill")
                                .font(.system(size: 64))
                                .foregroundColor(Theme.Colors.success)

                            Text("Check Your Email")
                                .font(Theme.Typography.title2)
                                .foregroundColor(Theme.Colors.textPrimary)

                            Text("We've sent password reset instructions to \(email)")
                                .font(Theme.Typography.body)
                                .foregroundColor(Theme.Colors.textSecondary)
                                .multilineTextAlignment(.center)
                        }

                        PrimaryButton(title: "Back to Login", action: { dismiss() })
                    } else {
                        // Form State
                        VStack(spacing: Theme.Spacing.md) {
                            Text("Enter your email address and we'll send you instructions to reset your password.")
                                .font(Theme.Typography.body)
                                .foregroundColor(Theme.Colors.textSecondary)
                                .multilineTextAlignment(.center)

                            ThemedTextField(
                                placeholder: "Email",
                                text: $email,
                                keyboardType: .emailAddress,
                                autocapitalization: .never
                            )
                        }

                        if let error = authManager.errorMessage {
                            Text(error)
                                .font(Theme.Typography.footnote)
                                .foregroundColor(Theme.Colors.danger)
                        }

                        PrimaryButton(
                            title: "Send Reset Link",
                            action: {
                                Task {
                                    let success = await authManager.resetPassword(email: email)
                                    if success {
                                        emailSent = true
                                    }
                                }
                            },
                            isLoading: authManager.isLoading,
                            isDisabled: email.isEmpty
                        )
                    }
                }
                .padding(Theme.Spacing.lg)
            }
            .navigationTitle("Reset Password")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(Theme.Colors.accent)
                }
            }
        }
    }
}

#Preview {
    AuthenticationView()
        .environmentObject(AuthManager())
}
