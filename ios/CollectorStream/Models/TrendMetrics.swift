import Foundation

// MARK: - Trend Metrics
/// Market analysis metrics including trends, volatility, and momentum
struct TrendMetrics: Codable {
    let trend7d: Double   // 7-day trend percentage
    let trend30d: Double  // 30-day trend percentage
    let trend90d: Double  // 90-day trend percentage
    let volatility: Double // Price volatility (coefficient of variation)
    let momentum: Momentum // Price momentum direction
    let sampleSize: Int   // Number of data points used

    enum CodingKeys: String, CodingKey {
        case trend7d = "trend_7d"
        case trend30d = "trend_30d"
        case trend90d = "trend_90d"
        case volatility
        case momentum
        case sampleSize = "sample_size"
    }

    /// Get trend for a specific timeframe
    func trend(for timeframe: TimeFrame) -> Double {
        switch timeframe {
        case .week: return trend7d
        case .month: return trend30d
        case .threeMonths: return trend90d
        case .sixMonths: return trend90d // Fallback to 90d if 180d not available
        case .year: return trend90d // Fallback to 90d if 365d not available
        }
    }

    /// Get the overall trend direction
    var overallTrend: TrendDirection {
        // Weighted average: 30d has most weight
        let weighted = (trend7d * 0.2) + (trend30d * 0.5) + (trend90d * 0.3)
        if weighted > 5 { return .bullish }
        if weighted < -5 { return .bearish }
        return .neutral
    }
}

// MARK: - Momentum
enum Momentum: String, Codable {
    case accelerating = "ACCELERATING"
    case steady = "STEADY"
    case decelerating = "DECELERATING"

    var displayName: String {
        switch self {
        case .accelerating: return "Accelerating"
        case .steady: return "Steady"
        case .decelerating: return "Decelerating"
        }
    }

    var icon: String {
        switch self {
        case .accelerating: return "arrow.up.right"
        case .steady: return "arrow.right"
        case .decelerating: return "arrow.down.right"
        }
    }
}

// MARK: - Trend Direction
enum TrendDirection {
    case bullish
    case neutral
    case bearish

    var displayName: String {
        switch self {
        case .bullish: return "Bullish"
        case .neutral: return "Neutral"
        case .bearish: return "Bearish"
        }
    }

    var icon: String {
        switch self {
        case .bullish: return "arrow.up"
        case .neutral: return "minus"
        case .bearish: return "arrow.down"
        }
    }
}
