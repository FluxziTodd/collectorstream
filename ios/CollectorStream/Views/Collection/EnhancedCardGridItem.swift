import SwiftUI

/// Enhanced card grid item with AI recommendation badge
struct EnhancedCardGridItem: View {
    let card: Card
    let recommendation: Recommendation?

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                // Card image with AI badge overlay
                ZStack(alignment: .topTrailing) {
                    // Card image
                    CardImageView(url: card.frontImageUrl)
                        .frame(height: 168) // 5:7 ratio for 120px width
                        .cornerRadius(Theme.CornerRadius.small)

                    // AI recommendation badge
                    if let rec = recommendation {
                        AIBadge(action: rec.action, confidence: rec.confidence)
                            .padding(6)
                    }
                }

                // Card info
                VStack(alignment: .leading, spacing: 4) {
                    // Player name
                    Text(card.playerName)
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)
                        .lineLimit(1)

                    // Team
                    if let team = card.team {
                        Text(team)
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                            .lineLimit(1)
                    }

                    // Sport and value row
                    HStack(spacing: 4) {
                        // Sport badge
                        Text(card.sport.rawValue)
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.accent)

                        Spacer()

                        // Value with trend
                        if let value = card.estimatedValue {
                            HStack(spacing: 4) {
                                // Trend indicator if recommendation available
                                if let rec = recommendation {
                                    TrendIndicator(trend: rec.metrics.trend7d)
                                }

                                Text("$\(Int(value))")
                                    .font(Theme.Typography.caption)
                                    .fontWeight(.semibold)
                                    .foregroundColor(Theme.Colors.success)
                            }
                        }
                    }

                    // Profit/Loss indicator (if purchase price available)
                    if let purchase = card.purchasePrice,
                       let value = card.estimatedValue,
                       purchase > 0 {
                        let profit = value - purchase
                        let profitPercent = (profit / purchase) * 100

                        HStack(spacing: 2) {
                            Image(systemName: profit >= 0 ? "arrow.up" : "arrow.down")
                                .font(.system(size: 8, weight: .bold))
                            Text("\(abs(Int(profitPercent)))%")
                                .font(.system(size: 9, weight: .semibold))
                        }
                        .foregroundColor(profit >= 0 ? Theme.Colors.success : Theme.Colors.danger)
                    }
                }
                .padding(.horizontal, 4)
            }
        }
    }
}

// MARK: - Card Image View
private struct CardImageView: View {
    let url: String?

    var body: some View {
        if let urlString = url, let url = URL(string: urlString) {
            AsyncImage(url: url) { phase in
                switch phase {
                case .empty:
                    ProgressView()
                        .tint(Theme.Colors.accent)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Theme.Colors.bgSecondary)
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                case .failure:
                    PlaceholderImage()
                @unknown default:
                    PlaceholderImage()
                }
            }
        } else {
            PlaceholderImage()
        }
    }
}

private struct PlaceholderImage: View {
    var body: some View {
        ZStack {
            Theme.Colors.bgSecondary
            Image(systemName: "photo")
                .font(.system(size: 32))
                .foregroundColor(Theme.Colors.textMuted)
        }
    }
}

// MARK: - Preview
#Preview {
    let sampleCard = Card(
        id: "123",
        playerName: "Patrick Mahomes",
        team: "Kansas City Chiefs",
        year: "2017",
        set: "Prizm",
        cardNumber: "127",
        manufacturer: "Panini",
        sport: .football,
        condition: .nearMint,
        grading: nil,
        frontImageUrl: nil,
        backImageUrl: nil,
        purchasePrice: 100,
        estimatedValue: 125,
        notes: nil,
        createdAt: Date(),
        updatedAt: Date()
    )

    let sampleMetrics = TrendMetrics(
        trend7d: 5.2,
        trend30d: 12.5,
        trend90d: 8.3,
        volatility: 15.0,
        momentum: .accelerating,
        sampleSize: 45
    )

    let sampleRecommendation = Recommendation(
        cardId: "123",
        playerName: "Patrick Mahomes",
        year: "2017",
        set: "Prizm",
        action: .buyMore,
        confidence: 0.85,
        category: "MOMENTUM",
        reasoning: "Strong momentum",
        metrics: sampleMetrics
    )

    return LazyVGrid(
        columns: [
            GridItem(.flexible(), spacing: 16),
            GridItem(.flexible(), spacing: 16)
        ],
        spacing: 16
    ) {
        EnhancedCardGridItem(card: sampleCard, recommendation: sampleRecommendation)
        EnhancedCardGridItem(card: sampleCard, recommendation: nil)
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
