import Foundation

// MARK: - Portfolio Stats
/// Statistics and metrics for the entire portfolio
struct PortfolioStats {
    let totalValue: Double
    let totalCards: Int
    let profitLoss: Double
    let profitLossPercent: Double
    let topGainer: Card?
    let topLoser: Card?
    let recommendationSummary: RecommendationSummary

    /// Average value per card
    var averageValue: Double {
        guard totalCards > 0 else { return 0 }
        return totalValue / Double(totalCards)
    }

    /// Total purchase price of all cards
    var totalCost: Double {
        totalValue - profitLoss
    }

    /// Is the portfolio profitable?
    var isProfitable: Bool {
        profitLoss > 0
    }

    /// Initialize with default values
    static var empty: PortfolioStats {
        PortfolioStats(
            totalValue: 0,
            totalCards: 0,
            profitLoss: 0,
            profitLossPercent: 0,
            topGainer: nil,
            topLoser: nil,
            recommendationSummary: RecommendationSummary(
                buyMore: 0,
                hold: 0,
                sell: 0,
                cutLoss: 0
            )
        )
    }
}

// MARK: - Portfolio Breakdown
/// Portfolio breakdown by category (sport, team, etc.)
struct PortfolioBreakdown {
    let category: String // e.g., "NFL", "NBA", "Cardinals"
    let cardCount: Int
    let totalValue: Double
    let percentage: Double // Percentage of total portfolio value

    /// Display-friendly description
    var displayName: String {
        "\(category) (\(cardCount) cards)"
    }
}

// MARK: - Recent Activity
/// Recent activity in the portfolio
struct PortfolioActivity: Identifiable {
    let id: String
    let type: ActivityType
    let cardName: String
    let value: Double?
    let change: Double?
    let timestamp: Date

    enum ActivityType {
        case cardAdded
        case valueUpdated
        case recommendationChanged
        case marketMover

        var icon: String {
            switch self {
            case .cardAdded: return "plus.circle.fill"
            case .valueUpdated: return "arrow.triangle.2.circlepath"
            case .recommendationChanged: return "brain.head.profile"
            case .marketMover: return "chart.line.uptrend.xyaxis"
            }
        }

        var displayName: String {
            switch self {
            case .cardAdded: return "Card Added"
            case .valueUpdated: return "Value Updated"
            case .recommendationChanged: return "Recommendation Changed"
            case .marketMover: return "Market Mover"
            }
        }
    }

    /// Display text for the activity
    var displayText: String {
        switch type {
        case .cardAdded:
            return "Added \(cardName)"
        case .valueUpdated:
            if let value = value {
                return "\(cardName) updated to $\(Int(value))"
            }
            return "\(cardName) value updated"
        case .recommendationChanged:
            return "\(cardName) recommendation changed"
        case .marketMover:
            if let change = change {
                let direction = change > 0 ? "up" : "down"
                return "\(cardName) moved \(direction) \(abs(Int(change)))%"
            }
            return "\(cardName) is a market mover"
        }
    }
}
