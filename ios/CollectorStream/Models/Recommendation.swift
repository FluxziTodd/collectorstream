import Foundation
import SwiftUI

// MARK: - Recommendation Model
/// AI-powered recommendation for a card with buy/sell/hold signals
struct Recommendation: Codable, Identifiable {
    var id: String { cardId }

    let cardId: String
    let playerName: String
    let year: String?
    let set: String?
    let action: RecommendationAction
    let confidence: Double // 0.0 to 1.0
    let category: String // e.g., "QUICK_FLIP", "LONG_HOLD", "MOMENTUM", "CUT_LOSS"
    let reasoning: String
    let metrics: TrendMetrics

    enum CodingKeys: String, CodingKey {
        case cardId
        case playerName
        case year
        case set
        case action
        case confidence
        case category
        case reasoning
        case metrics
    }
}

// MARK: - Recommendation Action
enum RecommendationAction: String, Codable, CaseIterable {
    case buyMore = "BUY_MORE"
    case hold = "HOLD"
    case sell = "SELL"
    case cutLoss = "CUT_LOSS"

    /// Display name for the action
    var displayName: String {
        switch self {
        case .buyMore: return "Buy More"
        case .hold: return "Hold"
        case .sell: return "Sell"
        case .cutLoss: return "Cut Loss"
        }
    }

    /// Color for the action badge
    var color: Color {
        switch self {
        case .buyMore: return Theme.Colors.success
        case .hold: return Theme.Colors.info
        case .sell: return Theme.Colors.warning
        case .cutLoss: return Theme.Colors.danger
        }
    }

    /// SF Symbol icon name
    var icon: String {
        switch self {
        case .buyMore: return "arrow.up.circle.fill"
        case .hold: return "hand.raised.fill"
        case .sell: return "arrow.down.circle.fill"
        case .cutLoss: return "xmark.circle.fill"
        }
    }

    /// Short badge text for compact displays
    var shortText: String {
        switch self {
        case .buyMore: return "BUY"
        case .hold: return "HOLD"
        case .sell: return "SELL"
        case .cutLoss: return "CUT"
        }
    }
}

// MARK: - Portfolio Recommendations Response
/// Response from portfolio recommendations endpoint
struct PortfolioRecommendationsResponse: Codable {
    let recommendations: [Recommendation]
    let summary: RecommendationSummary
    let total: Int
}

// MARK: - Recommendation Summary
/// Summary counts of different recommendation actions
struct RecommendationSummary: Codable {
    let buyMore: Int
    let hold: Int
    let sell: Int
    let cutLoss: Int

    var total: Int {
        buyMore + hold + sell + cutLoss
    }

    /// Get count for a specific action
    func count(for action: RecommendationAction) -> Int {
        switch action {
        case .buyMore: return buyMore
        case .hold: return hold
        case .sell: return sell
        case .cutLoss: return cutLoss
        }
    }
}
