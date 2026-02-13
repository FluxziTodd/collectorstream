import Foundation
import SwiftUI

/// View model for insights view
/// Categorizes recommendations and identifies opportunities/alerts
@MainActor
class InsightsViewModel: ObservableObject {
    @Published var opportunities: [Recommendation] = []
    @Published var needsAttention: [Recommendation] = []
    @Published var topGainers: [Card] = []
    @Published var topLosers: [Card] = []
    @Published var sportBreakdown: [String: PortfolioBreakdown] = [:]
    @Published var isLoading = false

    // MARK: - Load Insights

    /// Load insights from cards and recommendations
    func loadInsights(cards: [Card], recommendations: [String: Recommendation]) async {
        isLoading = true

        // Categorize recommendations
        categorizeRecommendations(Array(recommendations.values))

        // Identify top movers
        identifyTopMovers(cards)

        // Calculate sport breakdown
        calculateSportBreakdown(cards)

        isLoading = false
    }

    /// Refresh insights
    func refresh(cards: [Card], recommendations: [String: Recommendation]) async {
        await loadInsights(cards: cards, recommendations: recommendations)
    }

    // MARK: - Categorization

    private func categorizeRecommendations(_ recommendations: [Recommendation]) {
        // High-confidence BUY recommendations (>70% confidence)
        opportunities = recommendations
            .filter { $0.action == .buyMore && $0.confidence >= 0.7 }
            .sorted { $0.confidence > $1.confidence }
            .prefix(10)
            .map { $0 }

        // SELL and CUT_LOSS recommendations (sorted by confidence)
        needsAttention = recommendations
            .filter { $0.action == .sell || $0.action == .cutLoss }
            .sorted { $0.confidence > $1.confidence }
            .prefix(10)
            .map { $0 }
    }

    private func identifyTopMovers(_ cards: [Card]) {
        let cardsWithROI = cards.compactMap { card -> (Card, Double)? in
            guard let purchase = card.purchasePrice,
                  let value = card.estimatedValue,
                  purchase > 0 else { return nil }
            let roi = ((value - purchase) / purchase) * 100
            return (card, roi)
        }

        // Top 5 gainers
        topGainers = cardsWithROI
            .filter { $0.1 > 0 } // Only positive gains
            .sorted { $0.1 > $1.1 }
            .prefix(5)
            .map { $0.0 }

        // Top 5 losers
        topLosers = cardsWithROI
            .filter { $0.1 < 0 } // Only losses
            .sorted { $0.1 < $1.1 }
            .prefix(5)
            .map { $0.0 }
    }

    private func calculateSportBreakdown(_ cards: [Card]) {
        var breakdown: [String: PortfolioBreakdown] = [:]
        let totalValue = cards.compactMap(\.estimatedValue).reduce(0, +)

        for sport in Card.Sport.allCases {
            let sportCards = cards.filter { $0.sport == sport }
            guard !sportCards.isEmpty else { continue }

            let sportValue = sportCards.compactMap(\.estimatedValue).reduce(0, +)
            let percentage = totalValue > 0 ? (sportValue / totalValue) * 100 : 0

            breakdown[sport.rawValue] = PortfolioBreakdown(
                category: sport.rawValue,
                cardCount: sportCards.count,
                totalValue: sportValue,
                percentage: percentage
            )
        }

        sportBreakdown = breakdown
    }

    // MARK: - Recommendation Summary

    var recommendationSummary: RecommendationSummary {
        let buyMore = opportunities.count
        let hold = 0 // Not tracked separately in insights
        let sell = needsAttention.filter { $0.action == .sell }.count
        let cutLoss = needsAttention.filter { $0.action == .cutLoss }.count

        return RecommendationSummary(
            buyMore: buyMore,
            hold: hold,
            sell: sell,
            cutLoss: cutLoss
        )
    }
}
