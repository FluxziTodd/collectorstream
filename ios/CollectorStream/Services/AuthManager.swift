import Foundation
import Combine

/// Authentication manager for CollectorStream API
@MainActor
class AuthManager: ObservableObject {
    // MARK: - Published Properties
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Private Properties
    private let apiClient = APIClient.shared
    private let keychain = KeychainService.shared
    private var cancellables = Set<AnyCancellable>()

    // MARK: - User Model
    struct User: Codable, Identifiable {
        let id: String
        let email: String
        let username: String
        let createdAt: Date?
    }

    // MARK: - Initialization
    init() {
        checkStoredCredentials()
    }

    // MARK: - Check Stored Credentials
    private func checkStoredCredentials() {
        if let token = keychain.getToken() {
            Task {
                await validateToken(token)
            }
        }
    }

    // MARK: - Login
    func login(email: String, password: String) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiClient.login(email: email, password: password)
            keychain.saveToken(response.token)
            currentUser = response.user
            isAuthenticated = true
            isLoading = false
            return true
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            errorMessage = "An unexpected error occurred"
            isLoading = false
            return false
        }
    }

    // MARK: - Register
    func register(email: String, username: String, password: String) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiClient.register(
                email: email,
                username: username,
                password: password
            )
            keychain.saveToken(response.token)
            currentUser = response.user
            isAuthenticated = true
            isLoading = false
            return true
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            errorMessage = "An unexpected error occurred"
            isLoading = false
            return false
        }
    }

    // MARK: - Logout
    func logout() {
        keychain.deleteToken()
        currentUser = nil
        isAuthenticated = false
    }

    // MARK: - Reset Password
    func resetPassword(email: String) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            try await apiClient.resetPassword(email: email)
            isLoading = false
            return true
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            errorMessage = "An unexpected error occurred"
            isLoading = false
            return false
        }
    }

    // MARK: - Change Password
    func changePassword(currentPassword: String, newPassword: String) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            try await apiClient.changePassword(
                currentPassword: currentPassword,
                newPassword: newPassword
            )
            isLoading = false
            return true
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            errorMessage = "An unexpected error occurred"
            isLoading = false
            return false
        }
    }

    // MARK: - Validate Token
    private func validateToken(_ token: String) async {
        do {
            let user = try await apiClient.validateToken(token)
            currentUser = user
            isAuthenticated = true
        } catch {
            // Token is invalid, clear it
            keychain.deleteToken()
            isAuthenticated = false
        }
    }
}
