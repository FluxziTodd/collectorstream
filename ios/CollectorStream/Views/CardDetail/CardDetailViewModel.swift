import Foundation
import SwiftUI

/// View model for enhanced card detail view
/// Manages market history, recommendations, and UI state
@MainActor
class CardDetailViewModel: ObservableObject {
    let cardId: String

    // MARK: - Published State
    @Published var marketHistory: [MarketDataPoint] = []
    @Published var recommendation: Recommendation?
    @Published var selectedTimeframe: TimeFrame = .month
    @Published var isLoadingChart = false
    @Published var isLoadingRecommendation = false
    @Published var chartError: String?
    @Published var recommendationError: String?

    private let apiClient = APIClient.shared

    // MARK: - Initialization
    init(cardId: String) {
        self.cardId = cardId
    }

    // MARK: - Data Loading

    /// Load all data (market history + recommendation)
    func loadData() async {
        async let historyTask = loadMarketHistory()
        async let recommendationTask = loadRecommendation()

        // Wait for both to complete
        await historyTask
        await recommendationTask
    }

    /// Load market history from API
    func loadMarketHistory() async {
        isLoadingChart = true
        chartError = nil

        do {
            let history = try await apiClient.getMarketHistory(cardId, limit: 365)
            marketHistory = history.history.sorted(by: { $0.checkedAt < $1.checkedAt })
            print("📈 Loaded \(marketHistory.count) price points for card \(cardId)")
            isLoadingChart = false
        } catch let error as APIError {
            chartError = error.userMessage
            print("❌ Failed to load market history: \(error.userMessage)")
            isLoadingChart = false
        } catch {
            chartError = "Failed to load price history"
            print("❌ Failed to load market history: \(error.localizedDescription)")
            isLoadingChart = false
        }
    }

    /// Load AI recommendation from API
    func loadRecommendation() async {
        isLoadingRecommendation = true
        recommendationError = nil

        do {
            recommendation = try await apiClient.getCardRecommendation(cardId)
            print("🤖 Loaded recommendation: \(recommendation?.action.displayName ?? "nil")")
            isLoadingRecommendation = false
        } catch let error as APIError {
            recommendationError = error.userMessage
            print("❌ Failed to load recommendation: \(error.userMessage)")
            isLoadingRecommendation = false
        } catch {
            recommendationError = "Failed to load recommendation"
            print("❌ Failed to load recommendation: \(error.localizedDescription)")
            isLoadingRecommendation = false
        }
    }

    /// Refresh market value and reload data
    func refreshMarketValue() async {
        do {
            let response = try await apiClient.refreshMarketValue(cardId)
            print("💰 Refreshed market value: $\(response.marketPrice ?? 0)")

            // Reload data after refresh
            await loadMarketHistory()
            await loadRecommendation()
        } catch let error as APIError {
            print("❌ Failed to refresh market value: \(error.userMessage)")
        } catch {
            print("❌ Failed to refresh market value: \(error.localizedDescription)")
        }
    }

    // MARK: - Chart Data

    /// Get filtered market history for selected timeframe
    var filteredHistory: [MarketDataPoint] {
        let cutoffDate = Calendar.current.date(
            byAdding: .day,
            value: -selectedTimeframe.days,
            to: Date()
        ) ?? Date()

        return marketHistory.filter { $0.checkedAt >= cutoffDate }
    }

    /// Get chart statistics for current timeframe
    var chartStats: ChartStats? {
        guard !filteredHistory.isEmpty else { return nil }

        let prices = filteredHistory.map { $0.marketPrice }
        let low = prices.min() ?? 0
        let high = prices.max() ?? 0
        let average = prices.reduce(0, +) / Double(prices.count)

        return ChartStats(lowest: low, highest: high, average: average)
    }

    /// Check if there's enough data for meaningful chart
    var hasEnoughDataForChart: Bool {
        filteredHistory.count >= 2
    }
}

// MARK: - Chart Stats
struct ChartStats {
    let lowest: Double
    let highest: Double
    let average: Double

    var range: Double {
        highest - lowest
    }

    var rangePercent: Double {
        guard lowest > 0 else { return 0 }
        return (range / lowest) * 100
    }
}
