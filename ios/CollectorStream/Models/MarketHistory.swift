import Foundation

// MARK: - Market Data Point
/// Single price point in market history
struct MarketDataPoint: Codable, Identifiable {
    let id: String
    let marketPrice: Double
    let sampleSize: Int
    let confidenceLevel: Double
    let priceRangeLow: Double?
    let priceRangeHigh: Double?
    let checkedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case marketPrice
        case sampleSize = "sample_size"
        case confidenceLevel = "confidence_level"
        case priceRangeLow = "price_range_low"
        case priceRangeHigh = "price_range_high"
        case checkedAt = "checked_at"
    }
}

// MARK: - Market History
/// Collection of market price data points for a card
struct MarketHistory: Codable {
    let cardId: String
    let history: [MarketDataPoint]
    let total: Int

    enum CodingKeys: String, CodingKey {
        case cardId = "card_id"
        case history
        case total
    }

    /// Get data points for a specific timeframe
    func data(for timeframe: TimeFrame) -> [MarketDataPoint] {
        let cutoffDate = Calendar.current.date(
            byAdding: .day,
            value: -timeframe.days,
            to: Date()
        ) ?? Date()

        return history.filter { $0.checkedAt >= cutoffDate }
    }

    /// Get the lowest price in the history
    var lowestPrice: Double? {
        history.map { $0.marketPrice }.min()
    }

    /// Get the highest price in the history
    var highestPrice: Double? {
        history.map { $0.marketPrice }.max()
    }

    /// Get the average price in the history
    var averagePrice: Double? {
        guard !history.isEmpty else { return nil }
        let total = history.reduce(0.0) { $0 + $1.marketPrice }
        return total / Double(history.count)
    }

    /// Get the most recent price
    var latestPrice: Double? {
        history.max(by: { $0.checkedAt < $1.checkedAt })?.marketPrice
    }
}

// MARK: - Market History Response
/// API response for market history endpoint
struct MarketHistoryResponse: Codable {
    let cardId: String
    let history: [MarketDataPoint]
    let total: Int

    enum CodingKeys: String, CodingKey {
        case cardId = "card_id"
        case history
        case total
    }

    /// Convert response to MarketHistory model
    func toMarketHistory() -> MarketHistory {
        MarketHistory(cardId: cardId, history: history, total: total)
    }
}

// MARK: - Time Frame
/// Chart timeframe options
enum TimeFrame: String, CaseIterable {
    case week = "1W"
    case month = "1M"
    case threeMonths = "3M"
    case sixMonths = "6M"
    case year = "1Y"

    /// Number of days for the timeframe
    var days: Int {
        switch self {
        case .week: return 7
        case .month: return 30
        case .threeMonths: return 90
        case .sixMonths: return 180
        case .year: return 365
        }
    }

    /// Display name for the timeframe
    var displayName: String {
        switch self {
        case .week: return "1 Week"
        case .month: return "1 Month"
        case .threeMonths: return "3 Months"
        case .sixMonths: return "6 Months"
        case .year: return "1 Year"
        }
    }
}

// MARK: - Market Value Response
/// Response from market value refresh endpoint
struct MarketValueResponse: Codable {
    let cardId: String
    let marketPrice: Double?
    let sampleSize: Int
    let confidenceLevel: Double
    let priceRangeLow: Double?
    let priceRangeHigh: Double?
    let source: String
    let checkedAt: String

    enum CodingKeys: String, CodingKey {
        case cardId
        case marketPrice
        case sampleSize
        case confidenceLevel
        case priceRangeLow
        case priceRangeHigh
        case source
        case checkedAt
    }
}
