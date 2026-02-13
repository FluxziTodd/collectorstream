import Foundation

// MARK: - Market History API Extension
extension APIClient {
    /// Get market price history for a card
    /// - Parameters:
    ///   - cardId: The ID of the card
    ///   - limit: Maximum number of history records to return (default 365)
    /// - Returns: Market history with price data points
    /// - Throws: API error if request fails
    func getMarketHistory(_ cardId: String, limit: Int = 365) async throws -> MarketHistory {
        let endpoint = "\(baseURL)/cards/\(cardId)/market-history?limit=\(limit)"

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
            throw APIError.serverError("Failed to fetch market history (Status: \(httpResponse.statusCode))")
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom(dateDecoder)

        // Try to decode as MarketHistoryResponse first, then convert to MarketHistory
        if let response = try? decoder.decode(MarketHistoryResponse.self, from: data) {
            return response.toMarketHistory()
        }

        // Fallback to direct MarketHistory decoding
        return try decoder.decode(MarketHistory.self, from: data)
    }

    /// Refresh market value for a card
    /// - Parameter cardId: The ID of the card
    /// - Returns: Updated market value information
    /// - Throws: API error if request fails
    func refreshMarketValue(_ cardId: String) async throws -> MarketValueResponse {
        let endpoint = "\(baseURL)/cards/\(cardId)/market-value"

        let request = try createRequest(
            endpoint: endpoint,
            method: "POST",
            body: nil as String?, // Empty body for POST
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
            throw APIError.serverError("Failed to refresh market value (Status: \(httpResponse.statusCode))")
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom(dateDecoder)

        return try decoder.decode(MarketValueResponse.self, from: data)
    }

    /// Refresh market values for multiple cards
    /// - Parameter cardIds: Array of card IDs to refresh
    /// - Returns: Dictionary mapping card IDs to their market value responses
    func refreshMarketValues(_ cardIds: [String]) async throws -> [String: MarketValueResponse] {
        var results: [String: MarketValueResponse] = [:]

        // Refresh cards concurrently
        await withTaskGroup(of: (String, MarketValueResponse?).self) { group in
            for cardId in cardIds {
                group.addTask {
                    do {
                        let response = try await self.refreshMarketValue(cardId)
                        return (cardId, response)
                    } catch {
                        print("Failed to refresh market value for card \(cardId): \(error)")
                        return (cardId, nil)
                    }
                }
            }

            for await (cardId, response) in group {
                if let response = response {
                    results[cardId] = response
                }
            }
        }

        return results
    }
}
