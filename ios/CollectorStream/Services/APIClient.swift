import Foundation

/// API client for CollectorStream backend
class APIClient {
    static let shared = APIClient()

    // MARK: - Configuration
    private let baseURL = "https://api.collectorstream.com/v1"
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        session = URLSession(configuration: config)
    }

    // MARK: - Auth Response
    struct AuthResponse: Codable {
        let token: String
        let user: AuthManager.User
    }

    // MARK: - Login
    func login(email: String, password: String) async throws -> AuthResponse {
        let endpoint = "\(baseURL)/auth/login"
        let body = ["email": email, "password": password]
        return try await post(endpoint, body: body)
    }

    // MARK: - Register
    func register(email: String, username: String, password: String) async throws -> AuthResponse {
        let endpoint = "\(baseURL)/auth/register"
        let body = ["email": email, "username": username, "password": password]
        return try await post(endpoint, body: body)
    }

    // MARK: - Validate Token
    func validateToken(_ token: String) async throws -> AuthManager.User {
        let endpoint = "\(baseURL)/auth/validate"
        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return try await execute(request)
    }

    // MARK: - Reset Password
    func resetPassword(email: String) async throws {
        let endpoint = "\(baseURL)/auth/reset-password"
        let body = ["email": email]
        let _: EmptyResponse = try await post(endpoint, body: body)
    }

    // MARK: - Change Password
    func changePassword(currentPassword: String, newPassword: String) async throws {
        let endpoint = "\(baseURL)/auth/change-password"
        let body = ["current_password": currentPassword, "new_password": newPassword]
        let _: EmptyResponse = try await post(endpoint, body: body, authenticated: true)
    }

    // MARK: - Cards API

    struct CardListResponse: Codable {
        let cards: [Card]
        let total: Int
        let page: Int
        let perPage: Int
    }

    func getCards(page: Int = 1, perPage: Int = 50) async throws -> CardListResponse {
        let endpoint = "\(baseURL)/cards?page=\(page)&per_page=\(perPage)"
        return try await get(endpoint, authenticated: true)
    }

    func addCard(_ card: CardUpload) async throws -> Card {
        let endpoint = "\(baseURL)/cards"
        return try await post(endpoint, body: card, authenticated: true)
    }

    func updateCard(_ card: Card) async throws -> Card {
        let endpoint = "\(baseURL)/cards/\(card.id)"
        return try await put(endpoint, body: card, authenticated: true)
    }

    func deleteCard(_ cardId: String) async throws {
        let endpoint = "\(baseURL)/cards/\(cardId)"
        let _: EmptyResponse = try await delete(endpoint, authenticated: true)
    }

    // MARK: - Image Upload

    struct ImageUploadResponse: Codable {
        let url: String
        let thumbnailUrl: String?
    }

    func uploadImage(_ imageData: Data, side: String) async throws -> ImageUploadResponse {
        let endpoint = "\(baseURL)/images/upload"
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        if let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"side\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(side)\r\n".data(using: .utf8)!)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"card.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        return try await execute(request)
    }

    // MARK: - Card Identification (Ximilar)

    struct CardIdentificationResponse: Codable {
        let playerName: String?
        let team: String?
        let year: String?
        let set: String?
        let cardNumber: String?
        let manufacturer: String?
        let sport: String?
        let estimatedValue: Double?
        let confidence: Double
        let grading: GradingInfo?
    }

    struct GradingInfo: Codable {
        let company: String?  // PSA, BGS, etc.
        let grade: String?
        let certNumber: String?
    }

    func identifyCard(frontImageData: Data, backImageData: Data? = nil) async throws -> CardIdentificationResponse {
        let endpoint = "\(baseURL)/cards/identify"
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        if let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add front image
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"front.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(frontImageData)
        body.append("\r\n".data(using: .utf8)!)

        // Add back image if provided
        if let backImageData = backImageData {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"back_image\"; filename=\"back.jpg\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
            body.append(backImageData)
            body.append("\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        return try await execute(request)
    }

    // MARK: - Private Helpers

    private struct EmptyResponse: Codable {}

    private func get<T: Codable>(_ endpoint: String, authenticated: Bool = false) async throws -> T {
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        if authenticated, let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return try await execute(request)
    }

    private func post<T: Codable, U: Encodable>(_ endpoint: String, body: U, authenticated: Bool = false) async throws -> T {
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)

        if authenticated, let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return try await execute(request)
    }

    private func put<T: Codable, U: Encodable>(_ endpoint: String, body: U, authenticated: Bool = false) async throws -> T {
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)

        if authenticated, let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return try await execute(request)
    }

    private func delete<T: Codable>(_ endpoint: String, authenticated: Bool = false) async throws -> T {
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        if authenticated, let token = KeychainService.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return try await execute(request)
    }

    private func execute<T: Codable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200...299:
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase

            // Custom date decoding to handle Python's datetime format (no timezone)
            decoder.dateDecodingStrategy = .custom { decoder in
                let container = try decoder.singleValueContainer()
                let dateString = try container.decode(String.self)

                let formatter = DateFormatter()
                formatter.locale = Locale(identifier: "en_US_POSIX")
                formatter.timeZone = TimeZone(secondsFromGMT: 0)

                // Try with fractional seconds (Python's default: 2026-02-10T20:41:08.372748)
                formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                if let date = formatter.date(from: dateString) {
                    return date
                }

                // Try with milliseconds (3 digits)
                formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS"
                if let date = formatter.date(from: dateString) {
                    return date
                }

                // Try without fractional seconds
                formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
                if let date = formatter.date(from: dateString) {
                    return date
                }

                // Try ISO8601 with timezone (if API format changes)
                let iso8601 = ISO8601DateFormatter()
                iso8601.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                if let date = iso8601.date(from: dateString) {
                    return date
                }

                throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string: \(dateString)")
            }

            return try decoder.decode(T.self, from: data)
        case 401:
            throw APIError.unauthorized
        case 403:
            throw APIError.forbidden
        case 404:
            throw APIError.notFound
        case 422:
            if let errorResponse = try? JSONDecoder().decode(ValidationError.self, from: data) {
                throw APIError.validation(errorResponse.message)
            }
            throw APIError.validation("Invalid request")
        case 500...599:
            throw APIError.serverError
        default:
            throw APIError.unknown(httpResponse.statusCode)
        }
    }
}

// MARK: - API Error
enum APIError: Error {
    case invalidURL
    case invalidResponse
    case unauthorized
    case forbidden
    case notFound
    case validation(String)
    case serverError
    case unknown(Int)

    var userMessage: String {
        switch self {
        case .invalidURL:
            return "Invalid request URL"
        case .invalidResponse:
            return "Invalid server response"
        case .unauthorized:
            return "Invalid email or password"
        case .forbidden:
            return "Access denied"
        case .notFound:
            return "Resource not found"
        case .validation(let message):
            return message
        case .serverError:
            return "Server error. Please try again later."
        case .unknown(let code):
            return "An error occurred (code: \(code))"
        }
    }
}

// MARK: - Validation Error
struct ValidationError: Codable {
    let message: String
    let errors: [String: [String]]?
}
