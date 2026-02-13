import SwiftUI

/// AI recommendation card with action badge, confidence, and reasoning
struct RecommendationCard: View {
    let recommendation: Recommendation

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                // Header
                HStack {
                    Image(systemName: "brain.head.profile")
                        .foregroundColor(Theme.Colors.accent)
                    Text("AI Recommendation")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                // Action badge (large)
                HStack(spacing: Theme.Spacing.md) {
                    Image(systemName: recommendation.action.icon)
                        .font(.system(size: 32))
                        .foregroundColor(recommendation.action.color)

                    VStack(alignment: .leading, spacing: 4) {
                        Text(recommendation.action.displayName)
                            .font(Theme.Typography.title2)
                            .fontWeight(.bold)
                            .foregroundColor(Theme.Colors.textPrimary)

                        Text("\(Int(recommendation.confidence * 100))% Confidence")
                            .font(Theme.Typography.subheadline)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }

                    Spacer()
                }

                // Confidence meter
                ConfidenceMeter(confidence: recommendation.confidence)

                // Reasoning
                Text(recommendation.reasoning)
                    .font(Theme.Typography.body)
                    .foregroundColor(Theme.Colors.textSecondary)
                    .padding(.top, Theme.Spacing.sm)
                    .fixedSize(horizontal: false, vertical: true)

                // Category badge
                HStack {
                    CategoryBadge(category: recommendation.category, action: recommendation.action)
                    Spacer()
                }
                .padding(.top, Theme.Spacing.xs)
            }
            .padding(Theme.Spacing.md)
        }
    }
}

// MARK: - Category Badge
private struct CategoryBadge: View {
    let category: String
    let action: RecommendationAction

    var body: some View {
        Text(category.replacingOccurrences(of: "_", with: " "))
            .font(Theme.Typography.caption)
            .fontWeight(.medium)
            .foregroundColor(action.color)
            .padding(.horizontal, Theme.Spacing.sm)
            .padding(.vertical, 4)
            .background(action.color.opacity(0.15))
            .cornerRadius(Theme.CornerRadius.small)
    }
}

// MARK: - Loading State
struct RecommendationLoadingCard: View {
    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                HStack {
                    Image(systemName: "brain.head.profile")
                        .foregroundColor(Theme.Colors.accent)
                    Text("AI Recommendation")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                VStack(spacing: Theme.Spacing.md) {
                    ProgressView()
                        .tint(Theme.Colors.accent)
                    Text("Analyzing market trends...")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textMuted)
                }
                .frame(height: 80)
            }
            .padding(Theme.Spacing.md)
        }
    }
}

// MARK: - Error State
struct RecommendationErrorCard: View {
    let error: String

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                HStack {
                    Image(systemName: "brain.head.profile")
                        .foregroundColor(Theme.Colors.accent)
                    Text("AI Recommendation")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                VStack(spacing: Theme.Spacing.sm) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 32))
                        .foregroundColor(Theme.Colors.warning)
                    Text(error)
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textMuted)
                        .multilineTextAlignment(.center)
                }
                .frame(height: 80)
            }
            .padding(Theme.Spacing.md)
        }
    }
}

// MARK: - Preview
#Preview {
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
        reasoning: "Strong momentum building (+12.5% trend) with room to run. Add to winning position before full breakout. Market showing accelerating growth with consistent volume.",
        metrics: sampleMetrics
    )

    return VStack(spacing: Theme.Spacing.lg) {
        RecommendationCard(recommendation: sampleRecommendation)
        RecommendationLoadingCard()
        RecommendationErrorCard(error: "Unable to load recommendation. Please try again.")
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
