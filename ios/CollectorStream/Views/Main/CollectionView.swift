import SwiftUI

struct CollectionView: View {
    @EnvironmentObject var cardStore: CardStore
    @Binding var selectedTab: Int
    @State private var searchText = ""
    @State private var selectedSport: Card.Sport?
    @State private var sortOption: SortOption = .dateAdded
    @State private var showFilters = false

    enum SortOption: String, CaseIterable {
        case dateAdded = "Date Added"
        case playerName = "Player Name"
        case value = "Value"
        case year = "Year"
    }

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

        // Sort
        switch sortOption {
        case .dateAdded:
            cards.sort { $0.createdAt > $1.createdAt }
        case .playerName:
            cards.sort { $0.playerName < $1.playerName }
        case .value:
            cards.sort { ($0.estimatedValue ?? 0) > ($1.estimatedValue ?? 0) }
        case .year:
            cards.sort { ($0.year ?? "") > ($1.year ?? "") }
        }

        return cards
    }

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Stats Header
                    CollectionStats(totalCards: cardStore.totalCards, totalValue: cardStore.totalValue)
                        .padding(.horizontal, Theme.Spacing.md)
                        .padding(.top, Theme.Spacing.sm)

                    // Sport Filter Pills
                    SportFilterPills(selectedSport: $selectedSport)
                        .padding(.vertical, Theme.Spacing.sm)

                    // Cards Grid
                    if cardStore.isLoading && cardStore.cards.isEmpty {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: Theme.Colors.accent))
                        Spacer()
                    } else if filteredCards.isEmpty {
                        EmptyStateView(
                            icon: "rectangle.stack",
                            title: "No Cards Yet",
                            message: "Start building your collection by scanning your first card.",
                            actionTitle: "Scan Card",
                            action: { selectedTab = 1 }
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
                                    NavigationLink(destination: CardDetailView(card: card)) {
                                        CardGridItem(card: card)
                                    }
                                }
                            }
                            .padding(Theme.Spacing.md)
                        }
                    }
                }
            }
            .navigationTitle("Collection")
            .searchable(text: $searchText, prompt: "Search cards...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Picker("Sort By", selection: $sortOption) {
                            ForEach(SortOption.allCases, id: \.self) { option in
                                Text(option.rawValue).tag(option)
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.up.arrow.down.circle")
                            .foregroundColor(Theme.Colors.accent)
                    }
                }
            }
        }
        .task {
            await cardStore.fetchCards()
        }
    }
}

// MARK: - Collection Stats
struct CollectionStats: View {
    let totalCards: Int
    let totalValue: Double

    var body: some View {
        HStack(spacing: Theme.Spacing.md) {
            StatBox(title: "Total Cards", value: "\(totalCards)", icon: "rectangle.stack")
            StatBox(title: "Est. Value", value: "$\(Int(totalValue))", icon: "dollarsign.circle")
        }
    }
}

struct StatBox: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        CardContainer {
            HStack(spacing: Theme.Spacing.sm) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(Theme.Colors.accent)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text(value)
                        .font(Theme.Typography.title3)
                        .foregroundColor(Theme.Colors.textPrimary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

// MARK: - Sport Filter Pills
struct SportFilterPills: View {
    @Binding var selectedSport: Card.Sport?

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: Theme.Spacing.sm) {
                FilterPill(title: "All", isSelected: selectedSport == nil) {
                    selectedSport = nil
                }

                ForEach(Card.Sport.allCases, id: \.self) { sport in
                    FilterPill(title: sport.rawValue, isSelected: selectedSport == sport) {
                        selectedSport = sport
                    }
                }
            }
            .padding(.horizontal, Theme.Spacing.md)
        }
    }
}

struct FilterPill: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(Theme.Typography.footnote)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .white : Theme.Colors.textSecondary)
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.vertical, Theme.Spacing.sm)
                .background(isSelected ? Theme.Colors.accent : Theme.Colors.bgCard)
                .cornerRadius(Theme.CornerRadius.xl)
                .overlay(
                    RoundedRectangle(cornerRadius: Theme.CornerRadius.xl)
                        .stroke(isSelected ? Theme.Colors.accent : Theme.Colors.border, lineWidth: 1)
                )
        }
    }
}

// MARK: - Card Grid Item
struct CardGridItem: View {
    let card: Card

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                // Card Image
                ZStack {
                    if let imageUrl = card.frontImageUrl, let url = URL(string: imageUrl) {
                        AuthenticatedAsyncImage(url: url) { image in
                            image
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                        } placeholder: {
                            ProgressView()
                        }
                    } else {
                        cardPlaceholder
                    }
                }
                .frame(height: 140)
                .cornerRadius(Theme.CornerRadius.small)
                .clipped()

                // Card Info
                VStack(alignment: .leading, spacing: 2) {
                    Text(card.playerName)
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)
                        .lineLimit(1)

                    if let team = card.team {
                        Text(team)
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textSecondary)
                            .lineLimit(1)
                    }

                    HStack {
                        Text(card.sport.rawValue)
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.accent)

                        Spacer()

                        if let value = card.estimatedValue {
                            Text("$\(Int(value))")
                                .font(Theme.Typography.caption)
                                .fontWeight(.semibold)
                                .foregroundColor(Theme.Colors.success)
                        }
                    }
                }
            }
        }
    }

    private var cardPlaceholder: some View {
        ZStack {
            Theme.Colors.bgSecondary
            Image(systemName: "photo")
                .font(.system(size: 32))
                .foregroundColor(Theme.Colors.textMuted)
        }
    }
}

#Preview {
    CollectionView(selectedTab: .constant(0))
        .environmentObject(CardStore())
        .preferredColorScheme(.dark)
}
