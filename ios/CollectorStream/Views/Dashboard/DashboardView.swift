import SwiftUI

/// Main dashboard view - new home screen
struct DashboardView: View {
    @EnvironmentObject var cardStore: CardStore
    @Binding var selectedTab: Int
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary.ignoresSafeArea()

                if viewModel.isLoading {
                    LoadingOverlay(message: "Loading dashboard...")
                } else {
                    ScrollView {
                        VStack(spacing: Theme.Spacing.lg) {
                            // Portfolio Value Card
                            PortfolioValueCard(stats: viewModel.stats)

                            // Quick Stats Grid
                            QuickStatsGrid(stats: viewModel.stats, cardStore: cardStore)

                            // Action Signals Card
                            ActionSignalsCard(
                                summary: viewModel.stats.recommendationSummary,
                                onTap: { selectedTab = 3 } // Navigate to Insights
                            )

                            // Top Movers Section
                            if !viewModel.topGainers.isEmpty || !viewModel.topLosers.isEmpty {
                                TopMoversSection(
                                    gainers: viewModel.topGainers,
                                    losers: viewModel.topLosers
                                )
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
            .navigationTitle("Dashboard")
            .navigationBarTitleDisplayMode(.large)
        }
        .task {
            await viewModel.loadDashboard(
                cards: cardStore.cards,
                recommendations: cardStore.recommendations
            )
        }
    }
}

// MARK: - Portfolio Value Card
private struct PortfolioValueCard: View {
    let stats: PortfolioStats

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                Text("Total Portfolio Value")
                    .font(Theme.Typography.subheadline)
                    .foregroundColor(Theme.Colors.textSecondary)

                HStack(alignment: .firstTextBaseline) {
                    Text("$\(Int(stats.totalValue))")
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(Theme.Colors.textPrimary)

                    Spacer()

                    // Profit/Loss
                    VStack(alignment: .trailing, spacing: 2) {
                        HStack(spacing: 4) {
                            Image(systemName: stats.profitLoss >= 0 ? "arrow.up" : "arrow.down")
                                .font(.system(size: 12, weight: .bold))
                            Text("$\(abs(Int(stats.profitLoss)))")
                                .font(Theme.Typography.title3)
                                .fontWeight(.semibold)
                        }
                        .foregroundColor(stats.profitLoss >= 0 ? Theme.Colors.success : Theme.Colors.danger)

                        Text("\(stats.profitLoss >= 0 ? "+" : "")\(String(format: "%.1f", stats.profitLossPercent))%")
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }
                }
            }
            .padding(Theme.Spacing.md)
        }
    }
}

// MARK: - Quick Stats Grid
private struct QuickStatsGrid: View {
    let stats: PortfolioStats
    let cardStore: CardStore

    var body: some View {
        LazyVGrid(
            columns: [
                GridItem(.flexible(), spacing: Theme.Spacing.md),
                GridItem(.flexible(), spacing: Theme.Spacing.md)
            ],
            spacing: Theme.Spacing.md
        ) {
            QuickStatCard(
                icon: "rectangle.stack.fill",
                label: "Total Cards",
                value: "\(stats.totalCards)",
                color: Theme.Colors.accent
            )

            QuickStatCard(
                icon: "chart.line.uptrend.xyaxis",
                label: "Top Gainer",
                value: stats.topGainer?.playerName ?? "N/A",
                color: Theme.Colors.success
            )

            QuickStatCard(
                icon: "dollarsign.circle.fill",
                label: "Avg. Value",
                value: "$\(Int(stats.averageValue))",
                color: Theme.Colors.info
            )

            QuickStatCard(
                icon: "chart.bar.fill",
                label: "Holdings",
                value: "\(uniquePlayerCount) Players",
                color: Theme.Colors.warning
            )
        }
    }

    private var uniquePlayerCount: Int {
        Set(cardStore.cards.map { $0.playerName }).count
    }
}

// MARK: - Action Signals Card
private struct ActionSignalsCard: View {
    let summary: RecommendationSummary
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            CardContainer {
                VStack(spacing: Theme.Spacing.md) {
                    HStack {
                        Image(systemName: "brain.head.profile")
                            .foregroundColor(Theme.Colors.accent)
                        Text("AI Action Signals")
                            .font(Theme.Typography.headline)
                            .foregroundColor(Theme.Colors.textPrimary)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(Theme.Colors.textMuted)
                    }

                    HStack(spacing: 8) {
                        ActionSignalPill(action: "BUY", count: summary.buyMore, color: Theme.Colors.success)
                        ActionSignalPill(action: "HOLD", count: summary.hold, color: Theme.Colors.info)
                        ActionSignalPill(action: "SELL", count: summary.sell, color: Theme.Colors.warning)
                        ActionSignalPill(action: "CUT", count: summary.cutLoss, color: Theme.Colors.danger)
                    }
                }
                .padding(Theme.Spacing.md)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Top Movers Section
private struct TopMoversSection: View {
    let gainers: [Card]
    let losers: [Card]
    @State private var selectedSegment = 0

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            HStack {
                Text("Top Movers")
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

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: Theme.Spacing.md) {
                    ForEach(selectedSegment == 0 ? gainers : losers) { card in
                        NavigationLink(destination: EnhancedCardDetailView(card: card)) {
                            MoverCardItem(card: card, isGainer: selectedSegment == 0)
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Mover Card Item
private struct MoverCardItem: View {
    let card: Card
    let isGainer: Bool

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                // Card image
                if let urlString = card.frontImageUrl, let url = URL(string: urlString) {
                    AsyncImage(url: url) { image in
                        image.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        Color.gray.opacity(0.2)
                    }
                    .frame(width: 120, height: 168)
                    .cornerRadius(Theme.CornerRadius.small)
                } else {
                    Color.gray.opacity(0.2)
                        .frame(width: 120, height: 168)
                        .cornerRadius(Theme.CornerRadius.small)
                }

                // Player name
                Text(card.playerName)
                    .font(Theme.Typography.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(Theme.Colors.textPrimary)
                    .lineLimit(1)
                    .frame(width: 120)

                // Value and change
                HStack {
                    if let value = card.estimatedValue {
                        Text("$\(Int(value))")
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                    }
                    Spacer()
                    if let purchase = card.purchasePrice, let value = card.estimatedValue, purchase > 0 {
                        let change = ((value - purchase) / purchase) * 100
                        HStack(spacing: 2) {
                            Image(systemName: change >= 0 ? "arrow.up" : "arrow.down")
                                .font(.system(size: 8, weight: .bold))
                            Text("\(abs(Int(change)))%")
                                .font(.system(size: 10, weight: .semibold))
                        }
                        .foregroundColor(isGainer ? Theme.Colors.success : Theme.Colors.danger)
                    }
                }
                .frame(width: 120)
            }
            .padding(Theme.Spacing.sm)
        }
        .frame(width: 136)
    }
}

// MARK: - Preview
#Preview {
    DashboardView(selectedTab: .constant(0))
        .environmentObject(CardStore())
}
