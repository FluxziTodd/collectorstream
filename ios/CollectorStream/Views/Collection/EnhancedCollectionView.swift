import SwiftUI

/// Enhanced collection view with AI badges, filters, and advanced sorting
struct EnhancedCollectionView: View {
    @EnvironmentObject var cardStore: CardStore
    @Binding var selectedTab: Int

    @StateObject private var viewModel = CollectionViewModel()
    @State private var searchText = ""
    @State private var selectedSport: Card.Sport?
    @State private var selectedFilter: RecommendationFilter = .all
    @State private var sortOption: CollectionSortOption = .dateAdded
    @State private var showSortMenu = false
    @State private var isRefreshing = false

    var filteredCards: [Card] {
        var cards = cardStore.cards

        // Filter by sport
        if let sport = selectedSport {
            cards = cards.filter { $0.sport == sport }
        }

        // Filter by search
        if !searchText.isEmpty {
            cards = cards.filter {
                $0.playerName.localizedCaseInsensitiveContains(searchText) ||
                ($0.team?.localizedCaseInsensitiveContains(searchText) ?? false) ||
                ($0.set?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
        }

        // Filter by recommendation
        cards = viewModel.filterCards(cards, by: selectedFilter)

        // Sort
        cards = viewModel.sortCards(cards, by: sortOption)

        return cards
    }

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Stats Header
                    CollectionStats(
                        totalCards: cardStore.totalCards,
                        totalValue: cardStore.totalValue
                    )
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.sm)

                    // Recommendation Filter Bar (NEW)
                    RecommendationFilterBar(
                        selected: $selectedFilter,
                        counts: viewModel.recommendationCounts(for: cardStore.cards)
                    )
                    .padding(.vertical, Theme.Spacing.sm)

                    // Sport Filter Pills
                    SportFilterPills(selectedSport: $selectedSport)
                        .padding(.bottom, Theme.Spacing.sm)

                    // Cards Grid
                    if cardStore.isLoading && cardStore.cards.isEmpty {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: Theme.Colors.accent))
                        Spacer()
                    } else if filteredCards.isEmpty {
                        EmptyStateView(
                            icon: "rectangle.stack",
                            title: selectedFilter == .all ? "No Cards Yet" : "No Cards Match Filter",
                            message: selectedFilter == .all
                                ? "Start building your collection by scanning your first card."
                                : "Try changing the filter to see more cards.",
                            actionTitle: selectedFilter == .all ? "Scan Card" : "Show All",
                            action: {
                                if selectedFilter == .all {
                                    selectedTab = 2 // Scan tab
                                } else {
                                    selectedFilter = .all
                                }
                            }
                        )
                    } else {
                        ScrollView {
                            LazyVGrid(
                                columns: [
                                    GridItem(.flexible(), spacing: Theme.Spacing.md),
                                    GridItem(.flexible(), spacing: Theme.Spacing.md)
                                ],
                                spacing: Theme.Spacing.md
                            ) {
                                ForEach(filteredCards) { card in
                                    NavigationLink(destination: EnhancedCardDetailView(card: card)) {
                                        EnhancedCardGridItem(
                                            card: card,
                                            recommendation: viewModel.recommendation(for: card.id)
                                        )
                                    }
                                }
                            }
                            .padding(Theme.Spacing.md)
                        }
                        .refreshable {
                            await refreshData()
                        }
                    }
                }
            }
            .navigationTitle("Collection")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Picker("Sort By", selection: $sortOption) {
                            ForEach(CollectionSortOption.allCases) { option in
                                Label(option.rawValue, systemImage: option.icon)
                                    .tag(option)
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.up.arrow.down.circle")
                            .foregroundColor(Theme.Colors.accent)
                    }
                }

                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { isRefreshing = true; Task { await refreshData() } }) {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .foregroundColor(Theme.Colors.accent)
                    }
                    .disabled(isRefreshing)
                }
            }
            .searchable(text: $searchText, prompt: "Search cards...")
            .task {
                // Load recommendations when view appears
                await viewModel.loadRecommendations()
            }
        }
    }

    // MARK: - Actions

    private func refreshData() async {
        isRefreshing = true

        // Refresh cards and recommendations concurrently
        async let cardsTask = cardStore.fetchCards()
        async let recommendationsTask = viewModel.loadRecommendations()

        await cardsTask
        await recommendationsTask

        isRefreshing = false
    }
}

// MARK: - Preview
#Preview {
    EnhancedCollectionView(selectedTab: .constant(1))
        .environmentObject(CardStore())
}
