import Foundation

// MARK: - Recommendations API Extension
extension APIClient {
    /// Get AI recommendation for a specific card
    /// - Parameter cardId: The ID of the card
    /// - Returns: Recommendation with action, confidence, and reasoning
    /// - Throws: API error if request fails
    func getCardRecommendation(_ cardId: String) async throws -> Recommendation {
        let endpoint = "\(baseURL)/cards/\(cardId)/recommendation"

        let request = try createRequest(
            endpoint: endpoint,
            method: "GET",
            body: nil as String?,
            authenticated: true
        )

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }

        guard httpResponse.statusCode == 200 else {
            if let errorData = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorData.detail)
            }
            throw APIError.serverError("Failed to fetch recommendation (Status: \(httpResponse.statusCode))")
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom(dateDecoder)

        return try decoder.decode(Recommendation.self, from: data)
    }

    /// Get portfolio-wide recommendations for all cards
    /// - Returns: Portfolio recommendations response with summary and individual recommendations
    /// - Throws: API error if request fails
    func getPortfolioRecommendations() async throws -> PortfolioRecommendationsResponse {
        let endpoint = "\(baseURL)/cards/portfolio/recommendations"

        let request = try createRequest(
            endpoint: endpoint,
            method: "GET",
            body: nil as String?,
            authenticated: true
        )

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }

        guard httpResponse.statusCode == 200 else {
            if let errorData = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorData.detail)
            }
            throw APIError.serverError("Failed to fetch portfolio recommendations (Status: \(httpResponse.statusCode))")
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom(dateDecoder)

        return try decoder.decode(PortfolioRecommendationsResponse.self, from: data)
    }
}
