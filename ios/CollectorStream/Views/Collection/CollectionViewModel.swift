import Foundation
import SwiftUI

/// View model for enhanced collection view
/// Manages recommendations, filtering, and sorting
@MainActor
class CollectionViewModel: ObservableObject {
    @Published var recommendations: [String: Recommendation] = [:] // Key = cardId
    @Published var isLoadingRecommendations = false
    @Published var recommendationError: String?

    private let apiClient = APIClient.shared

    // MARK: - Load Recommendations

    /// Load recommendations for all cards
    func loadRecommendations() async {
        isLoadingRecommendations = true
        recommendationError = nil

        do {
            let response = try await apiClient.getPortfolioRecommendations()
            recommendations = Dictionary(
                uniqueKeysWithValues: response.recommendations.map { ($0.cardId, $0) }
            )
            print("📊 Loaded \(recommendations.count) recommendations for collection")
            isLoadingRecommendations = false
        } catch let error as APIError {
            recommendationError = error.userMessage
            print("❌ Failed to load recommendations: \(error.userMessage)")
            isLoadingRecommendations = false
        } catch {
            recommendationError = "Failed to load recommendations"
            print("❌ Failed to load recommendations: \(error.localizedDescription)")
            isLoadingRecommendations = false
        }
    }

    /// Get recommendation for a specific card
    func recommendation(for cardId: String) -> Recommendation? {
        recommendations[cardId]
    }

    // MARK: - Filter Counts

    /// Calculate recommendation counts for filter bar
    func recommendationCounts(for cards: [Card]) -> [RecommendationFilter: Int] {
        var counts: [RecommendationFilter: Int] = [:]

        // All cards count
        counts[.all] = cards.count

        // Count by action
        var buyMoreCount = 0
        var holdCount = 0
        var sellCount = 0
        var needsAttentionCount = 0

        for card in cards {
            if let rec = recommendations[card.id] {
                switch rec.action {
                case .buyMore: buyMoreCount += 1
                case .hold: holdCount += 1
                case .sell:
                    sellCount += 1
                    needsAttentionCount += 1
                case .cutLoss:
                    needsAttentionCount += 1
                }
            }
        }

        counts[.buyMore] = buyMoreCount
        counts[.hold] = holdCount
        counts[.sell] = sellCount
        counts[.needsAttention] = needsAttentionCount

        return counts
    }

    // MARK: - Filtering

    /// Filter cards by recommendation
    func filterCards(_ cards: [Card], by filter: RecommendationFilter) -> [Card] {
        guard filter != .all else { return cards }

        return cards.filter { card in
            guard let rec = recommendations[card.id] else { return false }
            return filter.matches(rec.action)
        }
    }

    // MARK: - Sorting

    /// Sort cards by the selected option
    func sortCards(_ cards: [Card], by sortOption: CollectionSortOption) -> [Card] {
        switch sortOption {
        case .dateAdded:
            return cards.sorted { $0.createdAt > $1.createdAt }

        case .playerName:
            return cards.sorted { $0.playerName < $1.playerName }

        case .valueHigh:
            return cards.sorted {
                ($0.estimatedValue ?? 0) > ($1.estimatedValue ?? 0)
            }

        case .valueLow:
            return cards.sorted {
                ($0.estimatedValue ?? 0) < ($1.estimatedValue ?? 0)
            }

        case .profitPercent:
            return cards.sorted { card1, card2 in
                let roi1 = calculateROI(card1)
                let roi2 = calculateROI(card2)
                return roi1 > roi2
            }

        case .aiSignal:
            return cards.sorted { card1, card2 in
                let confidence1 = recommendations[card1.id]?.confidence ?? 0
                let confidence2 = recommendations[card2.id]?.confidence ?? 0
                return confidence1 > confidence2
            }
        }
    }

    // MARK: - Helpers

    private func calculateROI(_ card: Card) -> Double {
        guard let purchase = card.purchasePrice,
              let value = card.estimatedValue,
              purchase > 0 else { return 0 }
        return ((value - purchase) / purchase) * 100
    }
}

// MARK: - Sort Options

enum CollectionSortOption: String, CaseIterable, Identifiable {
    case dateAdded = "Date Added"
    case playerName = "Player Name"
    case valueHigh = "Value: High to Low"
    case valueLow = "Value: Low to High"
    case profitPercent = "Profit %"
    case aiSignal = "AI Signal"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .dateAdded: return "calendar"
        case .playerName: return "textformat.abc"
        case .valueHigh, .valueLow: return "dollarsign.circle"
        case .profitPercent: return "chart.line.uptrend.xyaxis"
        case .aiSignal: return "brain.head.profile"
        }
    }
}
