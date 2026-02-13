import SwiftUI

/// Enhanced card detail view with price charts and AI recommendations
struct EnhancedCardDetailView: View {
    let card: Card
    @EnvironmentObject var cardStore: CardStore
    @Environment(\.dismiss) var dismiss

    @StateObject private var viewModel: CardDetailViewModel
    @State private var showDeleteConfirmation = false
    @State private var showEditSheet = false
    @State private var isRefreshing = false

    init(card: Card) {
        self.card = card
        _viewModel = StateObject(wrappedValue: CardDetailViewModel(cardId: card.id))
    }

    var body: some View {
        ZStack {
            Theme.Colors.bgPrimary
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: Theme.Spacing.lg) {
                    // Card Images (existing)
                    CardImagesSection(card: card)

                    // NEW: Price Chart
                    PriceChartCard(
                        history: viewModel.filteredHistory,
                        selectedTimeframe: $viewModel.selectedTimeframe,
                        isLoading: viewModel.isLoadingChart,
                        stats: viewModel.chartStats
                    )

                    // NEW: AI Recommendation
                    if viewModel.isLoadingRecommendation {
                        RecommendationLoadingCard()
                    } else if let error = viewModel.recommendationError {
                        RecommendationErrorCard(error: error)
                    } else if let recommendation = viewModel.recommendation {
                        RecommendationCard(recommendation: recommendation)
                    }

                    // NEW: Market Metrics
                    MarketMetricsCard(
                        metrics: viewModel.recommendation?.metrics,
                        purchasePrice: card.purchasePrice,
                        currentValue: card.estimatedValue
                    )

                    // Card Info (existing)
                    CardInfoSection(card: card)

                    // Grading Info (existing)
                    if let grading = card.grading {
                        GradingSection(grading: grading)
                    }

                    // Value Section (existing)
                    ValueSection(card: card)

                    // Notes (existing)
                    if let notes = card.notes, !notes.isEmpty {
                        NotesSection(notes: notes)
                    }

                    // Actions
                    VStack(spacing: Theme.Spacing.md) {
                        // NEW: Refresh Market Value Button
                        PrimaryButton(
                            title: isRefreshing ? "Refreshing..." : "Refresh Market Value",
                            action: refreshMarketValue,
                            isLoading: isRefreshing
                        )
                        .disabled(isRefreshing)

                        SecondaryButton(title: "Edit Card", action: { showEditSheet = true })

                        Button(action: { showDeleteConfirmation = true }) {
                            Text("Delete Card")
                                .font(Theme.Typography.headline)
                                .foregroundColor(Theme.Colors.danger)
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                        }
                    }
                    .padding(.top, Theme.Spacing.lg)
                }
                .padding(Theme.Spacing.lg)
            }
        }
        .navigationTitle(card.playerName)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            // Load data when view appears
            await viewModel.loadData()
        }
        .confirmationDialog("Delete Card?", isPresented: $showDeleteConfirmation, titleVisibility: .visible) {
            Button("Delete", role: .destructive) {
                Task {
                    if await cardStore.deleteCard(card.id) {
                        dismiss()
                    }
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This action cannot be undone.")
        }
        .sheet(isPresented: $showEditSheet) {
            EditCardView(card: card)
        }
    }

    // MARK: - Actions

    private func refreshMarketValue() {
        Task {
            isRefreshing = true
            await viewModel.refreshMarketValue()

            // Reload cards in store to update the main view
            await cardStore.fetchCards()

            isRefreshing = false
        }
    }
}

// MARK: - Preview
#Preview {
    NavigationView {
        EnhancedCardDetailView(
            card: Card(
                id: "123",
                playerName: "Patrick Mahomes",
                team: "Kansas City Chiefs",
                year: "2017",
                set: "Prizm",
                cardNumber: "127",
                manufacturer: "Panini",
                sport: .football,
                condition: .nearMint,
                grading: Card.Grading(company: .psa, grade: "10", certNumber: "12345678"),
                frontImageUrl: nil,
                backImageUrl: nil,
                purchasePrice: 100,
                estimatedValue: 125,
                notes: "Rookie card in excellent condition",
                createdAt: Date(),
                updatedAt: Date()
            )
        )
    }
    .environmentObject(CardStore())
}
