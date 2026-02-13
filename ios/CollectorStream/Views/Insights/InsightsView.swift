import SwiftUI
import Charts

/// Market intelligence and insights view
struct InsightsView: View {
    @EnvironmentObject var cardStore: CardStore
    @StateObject private var viewModel = InsightsViewModel()

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary.ignoresSafeArea()

                if viewModel.isLoading {
                    LoadingOverlay(message: "Loading insights...")
                } else {
                    ScrollView {
                        VStack(spacing: Theme.Spacing.lg) {
                            // Action Signals Distribution
                            ActionSignalsDistributionCard(
                                summary: cardStore.portfolioStats.recommendationSummary
                            )

                            // Top Opportunities
                            if !viewModel.opportunities.isEmpty {
                                OpportunitiesSection(opportunities: viewModel.opportunities)
                            }

                            // Needs Attention
                            if !viewModel.needsAttention.isEmpty {
                                NeedsAttentionSection(alerts: viewModel.needsAttention)
                            }

                            // Market Movers
                            if !viewModel.topGainers.isEmpty || !viewModel.topLosers.isEmpty {
                                MarketMoversSection(
                                    gainers: viewModel.topGainers,
                                    losers: viewModel.topLosers
                                )
                            }

                            // Portfolio Breakdown
                            if !viewModel.sportBreakdown.isEmpty {
                                PortfolioBreakdownCard(breakdown: Array(viewModel.sportBreakdown.values))
                            }
                        }
                        .padding(Theme.Spacing.md)
                    }
                    .refreshable {
                        await viewModel.refresh(
                            cards: cardStore.cards,
                            recommendations: cardStore.recommendations
                        )
                    }
                }
            }
            .navigationTitle("Insights")
            .navigationBarTitleDisplayMode(.large)
        }
        .task {
            await viewModel.loadInsights(
                cards: cardStore.cards,
                recommendations: cardStore.recommendations
            )
        }
    }
}

// MARK: - Action Signals Distribution Card
private struct ActionSignalsDistributionCard: View {
    let summary: RecommendationSummary

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                Text("Action Signals Distribution")
                    .font(Theme.Typography.headline)
                    .foregroundColor(Theme.Colors.textPrimary)

                // Bar chart showing distribution
                HStack(alignment: .bottom, spacing: Theme.Spacing.sm) {
                    SignalBar(label: "BUY", count: summary.buyMore, color: Theme.Colors.success, total: summary.total)
                    SignalBar(label: "HOLD", count: summary.hold, color: Theme.Colors.info, total: summary.total)
                    SignalBar(label: "SELL", count: summary.sell, color: Theme.Colors.warning, total: summary.total)
                    SignalBar(label: "CUT", count: summary.cutLoss, color: Theme.Colors.danger, total: summary.total)
                }
                .frame(height: 120)
            }
            .padding(Theme.Spacing.md)
        }
    }
}

private struct SignalBar: View {
    let label: String
    let count: Int
    let color: Color
    let total: Int

    var body: some View {
        VStack(spacing: 4) {
            // Bar
            VStack {
                Spacer()
                RoundedRectangle(cornerRadius: 4)
                    .fill(color)
                    .frame(height: barHeight)
            }

            // Count
            Text("\(count)")
                .font(Theme.Typography.caption)
                .fontWeight(.semibold)
                .foregroundColor(Theme.Colors.textPrimary)

            // Label
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(Theme.Colors.textSecondary)
        }
    }

    private var barHeight: CGFloat {
        guard total > 0 else { return 0 }
        let percentage = CGFloat(count) / CGFloat(total)
        return max(percentage * 100, 8) // Minimum 8pt for visibility
    }
}

// MARK: - Opportunities Section
private struct OpportunitiesSection: View {
    let opportunities: [Recommendation]

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            HStack {
                Image(systemName: "lightbulb.fill")
                    .foregroundColor(Theme.Colors.success)
                Text("Top Opportunities")
                    .font(Theme.Typography.title3)
                    .foregroundColor(Theme.Colors.textPrimary)
                Spacer()
            }

            ForEach(opportunities.prefix(5)) { rec in
                NavigationLink(destination: Text("Card Detail")) { // TODO: Link to actual card
                    OpportunityRow(recommendation: rec)
                }
            }
        }
    }
}

private struct OpportunityRow: View {
    let recommendation: Recommendation

    var body: some View {
        CardContainer {
            HStack(spacing: Theme.Spacing.md) {
                // Icon
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(Theme.Colors.success)

                // Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(recommendation.playerName)
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)

                    Text(recommendation.reasoning)
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                        .lineLimit(2)
                }

                Spacer()

                // Confidence
                VStack(spacing: 2) {
                    Text("\(Int(recommendation.confidence * 100))%")
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.bold)
                        .foregroundColor(Theme.Colors.success)
                    Text("Conf.")
                        .font(.system(size: 8))
                        .foregroundColor(Theme.Colors.textMuted)
                }
            }
            .padding(Theme.Spacing.sm)
        }
    }
}

// MARK: - Needs Attention Section
private struct NeedsAttentionSection: View {
    let alerts: [Recommendation]

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(Theme.Colors.danger)
                Text("Needs Attention")
                    .font(Theme.Typography.title3)
                    .foregroundColor(Theme.Colors.textPrimary)
                Spacer()
            }

            ForEach(alerts.prefix(5)) { rec in
                NavigationLink(destination: Text("Card Detail")) { // TODO: Link to actual card
                    AlertRow(recommendation: rec)
                }
            }
        }
    }
}

private struct AlertRow: View {
    let recommendation: Recommendation

    var body: some View {
        CardContainer {
            HStack(spacing: Theme.Spacing.md) {
                // Icon
                Image(systemName: recommendation.action.icon)
                    .font(.system(size: 24))
                    .foregroundColor(recommendation.action.color)

                // Info
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(recommendation.playerName)
                            .font(Theme.Typography.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(Theme.Colors.textPrimary)

                        Text(recommendation.action.displayName.uppercased())
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(recommendation.action.color)
                            .cornerRadius(4)
                    }

                    Text(recommendation.reasoning)
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                        .lineLimit(2)
                }

                Spacer()
            }
            .padding(Theme.Spacing.sm)
        }
    }
}

// MARK: - Market Movers Section
private struct MarketMoversSection: View {
    let gainers: [Card]
    let losers: [Card]
    @State private var selectedSegment = 0

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            HStack {
                Text("Market Movers")
                    .font(Theme.Typography.title3)
                    .foregroundColor(Theme.Colors.textPrimary)
                Spacer()
                Picker("", selection: $selectedSegment) {
                    Text("Gainers").tag(0)
                    Text("Losers").tag(1)
                }
                .pickerStyle(.segmented)
                .frame(width: 180)
            }

            ForEach(selectedSegment == 0 ? gainers : losers) { card in
                NavigationLink(destination: EnhancedCardDetailView(card: card)) {
                    MoverRow(card: card, isGainer: selectedSegment == 0)
                }
            }
        }
    }
}

private struct MoverRow: View {
    let card: Card
    let isGainer: Bool

    var body: some View {
        CardContainer {
            HStack(spacing: Theme.Spacing.md) {
                // Card thumbnail
                if let urlString = card.frontImageUrl, let url = URL(string: urlString) {
                    AsyncImage(url: url) { image in
                        image.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        Color.gray.opacity(0.2)
                    }
                    .frame(width: 60, height: 84)
                    .cornerRadius(Theme.CornerRadius.small)
                } else {
                    Color.gray.opacity(0.2)
                        .frame(width: 60, height: 84)
                        .cornerRadius(Theme.CornerRadius.small)
                }

                // Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(card.playerName)
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)

                    if let team = card.team {
                        Text(team)
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }
                }

                Spacer()

                // ROI
                if let purchase = card.purchasePrice, let value = card.estimatedValue, purchase > 0 {
                    let roi = ((value - purchase) / purchase) * 100
                    VStack(alignment: .trailing, spacing: 2) {
                        HStack(spacing: 2) {
                            Image(systemName: roi >= 0 ? "arrow.up" : "arrow.down")
                                .font(.system(size: 10, weight: .bold))
                            Text("\(abs(Int(roi)))%")
                                .font(Theme.Typography.subheadline)
                                .fontWeight(.semibold)
                        }
                        .foregroundColor(isGainer ? Theme.Colors.success : Theme.Colors.danger)

                        Text("$\(Int(value))")
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }
                }
            }
            .padding(Theme.Spacing.sm)
        }
    }
}

// MARK: - Portfolio Breakdown Card
private struct PortfolioBreakdownCard: View {
    let breakdown: [PortfolioBreakdown]

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                Text("Portfolio Breakdown by Sport")
                    .font(Theme.Typography.headline)
                    .foregroundColor(Theme.Colors.textPrimary)

                ForEach(breakdown.sorted(by: { $0.totalValue > $1.totalValue }), id: \.category) { item in
                    BreakdownRow(breakdown: item)
                }
            }
            .padding(Theme.Spacing.md)
        }
    }
}

private struct BreakdownRow: View {
    let breakdown: PortfolioBreakdown

    var body: some View {
        VStack(spacing: 4) {
            HStack {
                Text(breakdown.category)
                    .font(Theme.Typography.subheadline)
                    .foregroundColor(Theme.Colors.textPrimary)
                Spacer()
                Text("$\(Int(breakdown.totalValue))")
                    .font(Theme.Typography.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(Theme.Colors.accent)
                Text("(\(breakdown.cardCount))")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textMuted)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(Theme.Colors.bgSecondary)
                        .frame(height: 4)

                    RoundedRectangle(cornerRadius: 2)
                        .fill(Theme.Colors.accent)
                        .frame(width: geometry.size.width * CGFloat(breakdown.percentage / 100), height: 4)
                }
            }
            .frame(height: 4)
        }
    }
}

// MARK: - Preview
#Preview {
    InsightsView()
        .environmentObject(CardStore())
}
