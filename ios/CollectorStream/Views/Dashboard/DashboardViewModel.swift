import Foundation
import SwiftUI

/// View model for dashboard
/// Calculates portfolio stats and manages dashboard state
@MainActor
class DashboardViewModel: ObservableObject {
    @Published var stats: PortfolioStats = .empty
    @Published var topGainers: [Card] = []
    @Published var topLosers: [Card] = []
    @Published var isLoading = false

    private let apiClient = APIClient.shared

    // MARK: - Load Dashboard

    /// Load dashboard data
    func loadDashboard(cards: [Card], recommendations: [String: Recommendation]) async {
        isLoading = true

        // Calculate stats from cards
        stats = calculateStats(from: cards, recommendations: recommendations)

        // Identify top movers
        let cardsWithROI = cards.compactMap { card -> (Card, Double)? in
            guard let purchase = card.purchasePrice,
                  let value = card.estimatedValue,
                  purchase > 0 else { return nil }
            let roi = ((value - purchase) / purchase) * 100
            return (card, roi)
        }

        // Top 5 gainers
        topGainers = cardsWithROI
            .sorted { $0.1 > $1.1 }
            .prefix(5)
            .map { $0.0 }

        // Top 5 losers
        topLosers = cardsWithROI
            .sorted { $0.1 < $1.1 }
            .prefix(5)
            .map { $0.0 }

        isLoading = false
    }

    /// Refresh dashboard
    func refresh(cards: [Card], recommendations: [String: Recommendation]) async {
        await loadDashboard(cards: cards, recommendations: recommendations)
    }

    // MARK: - Stats Calculation

    private func calculateStats(from cards: [Card], recommendations: [String: Recommendation]) -> PortfolioStats {
        let totalVal = cards.compactMap(\.estimatedValue).reduce(0, +)
        let totalPurchase = cards.compactMap(\.purchasePrice).reduce(0, +)
        let profitLoss = totalVal - totalPurchase
        let profitLossPercent = totalPurchase > 0 ? (profitLoss / totalPurchase) * 100 : 0

        // Find top gainer and loser
        let cardsWithROI = cards.compactMap { card -> (Card, Double)? in
            guard let purchase = card.purchasePrice,
                  let value = card.estimatedValue,
                  purchase > 0 else { return nil }
            let roi = ((value - purchase) / purchase) * 100
            return (card, roi)
        }

        let topGainer = cardsWithROI.max(by: { $0.1 < $1.1 })?.0
        let topLoser = cardsWithROI.min(by: { $0.1 < $1.1 })?.0

        // Calculate recommendation summary
        var buyMoreCount = 0
        var holdCount = 0
        var sellCount = 0
        var cutLossCount = 0

        for (_, recommendation) in recommendations {
            switch recommendation.action {
            case .buyMore: buyMoreCount += 1
            case .hold: holdCount += 1
            case .sell: sellCount += 1
            case .cutLoss: cutLossCount += 1
            }
        }

        let summary = RecommendationSummary(
            buyMore: buyMoreCount,
            hold: holdCount,
            sell: sellCount,
            cutLoss: cutLossCount
        )

        return PortfolioStats(
            totalValue: totalVal,
            totalCards: cards.count,
            profitLoss: profitLoss,
            profitLossPercent: profitLossPercent,
            topGainer: topGainer,
            topLoser: topLoser,
            recommendationSummary: summary
        )
    }
}
