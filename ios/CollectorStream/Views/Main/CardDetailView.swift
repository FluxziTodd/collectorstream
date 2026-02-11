import SwiftUI

struct CardDetailView: View {
    let card: Card
    @EnvironmentObject var cardStore: CardStore
    @Environment(\.dismiss) var dismiss

    @State private var showDeleteConfirmation = false
    @State private var showEditSheet = false

    var body: some View {
        ZStack {
            Theme.Colors.bgPrimary
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: Theme.Spacing.lg) {
                    // Card Images
                    CardImagesSection(card: card)

                    // Card Info
                    CardInfoSection(card: card)

                    // Grading Info
                    if let grading = card.grading {
                        GradingSection(grading: grading)
                    }

                    // Value Section
                    ValueSection(card: card)

                    // Notes
                    if let notes = card.notes, !notes.isEmpty {
                        NotesSection(notes: notes)
                    }

                    // Actions
                    VStack(spacing: Theme.Spacing.md) {
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
}

// MARK: - Card Images Section
struct CardImagesSection: View {
    let card: Card
    @State private var selectedSide = 0

    var body: some View {
        VStack(spacing: Theme.Spacing.sm) {
            TabView(selection: $selectedSide) {
                CardImageView(url: card.frontImageUrl, label: "Front")
                    .tag(0)

                CardImageView(url: card.backImageUrl, label: "Back")
                    .tag(1)
            }
            .tabViewStyle(.page(indexDisplayMode: .never))
            .frame(height: 350)

            // Page Indicator
            HStack(spacing: Theme.Spacing.sm) {
                ForEach(0..<2, id: \.self) { index in
                    Circle()
                        .fill(selectedSide == index ? Theme.Colors.accent : Theme.Colors.textMuted)
                        .frame(width: 8, height: 8)
                }
            }
        }
    }
}

struct CardImageView: View {
    let url: String?
    let label: String

    var body: some View {
        ZStack {
            if let urlString = url, let url = URL(string: urlString) {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                    case .failure:
                        imagePlaceholder
                    case .empty:
                        ProgressView()
                    @unknown default:
                        imagePlaceholder
                    }
                }
            } else {
                imagePlaceholder
            }
        }
        .frame(maxWidth: .infinity)
        .background(Theme.Colors.bgCard)
        .cornerRadius(Theme.CornerRadius.medium)
        .overlay(
            VStack {
                Spacer()
                HStack {
                    Text(label)
                        .font(Theme.Typography.caption)
                        .foregroundColor(.white)
                        .padding(.horizontal, Theme.Spacing.sm)
                        .padding(.vertical, 4)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(Theme.CornerRadius.small)
                    Spacer()
                }
                .padding(Theme.Spacing.sm)
            }
        )
    }

    private var imagePlaceholder: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Image(systemName: "photo")
                .font(.system(size: 48))
                .foregroundColor(Theme.Colors.textMuted)
            Text("No \(label) Image")
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textMuted)
        }
    }
}

// MARK: - Card Info Section
struct CardInfoSection: View {
    let card: Card

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                InfoRow(label: "Player", value: card.playerName)

                if let team = card.team {
                    InfoRow(label: "Team", value: team)
                }

                if let year = card.year {
                    InfoRow(label: "Year", value: year)
                }

                if let set = card.set {
                    InfoRow(label: "Set", value: set)
                }

                if let cardNumber = card.cardNumber {
                    InfoRow(label: "Card #", value: cardNumber)
                }

                if let manufacturer = card.manufacturer {
                    InfoRow(label: "Manufacturer", value: manufacturer)
                }

                InfoRow(label: "Sport", value: card.sport.displayName)

                if let condition = card.condition {
                    InfoRow(label: "Condition", value: condition.rawValue)
                }
            }
        }
    }
}

struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(Theme.Typography.subheadline)
                .foregroundColor(Theme.Colors.textSecondary)
            Spacer()
            Text(value)
                .font(Theme.Typography.subheadline)
                .fontWeight(.medium)
                .foregroundColor(Theme.Colors.textPrimary)
        }
    }
}

// MARK: - Grading Section
struct GradingSection: View {
    let grading: Card.Grading

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                HStack {
                    Image(systemName: "checkmark.seal.fill")
                        .foregroundColor(Theme.Colors.accent)
                    Text("Graded Card")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                InfoRow(label: "Company", value: grading.company.rawValue)
                InfoRow(label: "Grade", value: grading.grade)

                if let cert = grading.certNumber {
                    InfoRow(label: "Cert #", value: cert)
                }
            }
        }
    }
}

// MARK: - Value Section
struct ValueSection: View {
    let card: Card

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                HStack {
                    Image(systemName: "dollarsign.circle.fill")
                        .foregroundColor(Theme.Colors.success)
                    Text("Value")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                if let purchasePrice = card.purchasePrice {
                    InfoRow(label: "Purchase Price", value: "$\(Int(purchasePrice))")
                }

                if let estimatedValue = card.estimatedValue {
                    HStack {
                        Text("Estimated Value")
                            .font(Theme.Typography.subheadline)
                            .foregroundColor(Theme.Colors.textSecondary)
                        Spacer()
                        Text("$\(Int(estimatedValue))")
                            .font(Theme.Typography.title3)
                            .fontWeight(.bold)
                            .foregroundColor(Theme.Colors.success)
                    }
                }

                if let purchase = card.purchasePrice, let estimated = card.estimatedValue {
                    let gain = estimated - purchase
                    let percentage = (gain / purchase) * 100
                    HStack {
                        Text("Gain/Loss")
                            .font(Theme.Typography.subheadline)
                            .foregroundColor(Theme.Colors.textSecondary)
                        Spacer()
                        Text("\(gain >= 0 ? "+" : "")$\(Int(gain)) (\(Int(percentage))%)")
                            .font(Theme.Typography.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(gain >= 0 ? Theme.Colors.success : Theme.Colors.danger)
                    }
                }
            }
        }
    }
}

// MARK: - Notes Section
struct NotesSection: View {
    let notes: String

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                HStack {
                    Image(systemName: "note.text")
                        .foregroundColor(Theme.Colors.accent)
                    Text("Notes")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                Text(notes)
                    .font(Theme.Typography.body)
                    .foregroundColor(Theme.Colors.textSecondary)
            }
        }
    }
}

// MARK: - Edit Card View
struct EditCardView: View {
    let card: Card
    @EnvironmentObject var cardStore: CardStore
    @Environment(\.dismiss) var dismiss

    @State private var playerName: String
    @State private var team: String
    @State private var year: String
    @State private var set: String
    @State private var cardNumber: String
    @State private var sport: Card.Sport
    @State private var condition: Card.Condition?
    @State private var purchasePrice: String
    @State private var notes: String
    @State private var isSaving = false

    init(card: Card) {
        self.card = card
        _playerName = State(initialValue: card.playerName)
        _team = State(initialValue: card.team ?? "")
        _year = State(initialValue: card.year ?? "")
        _set = State(initialValue: card.set ?? "")
        _cardNumber = State(initialValue: card.cardNumber ?? "")
        _sport = State(initialValue: card.sport)
        _condition = State(initialValue: card.condition)
        _purchasePrice = State(initialValue: card.purchasePrice.map { String($0) } ?? "")
        _notes = State(initialValue: card.notes ?? "")
    }

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: Theme.Spacing.md) {
                        ThemedTextField(placeholder: "Player Name", text: $playerName)
                        ThemedTextField(placeholder: "Team", text: $team)
                        ThemedTextField(placeholder: "Year", text: $year)
                        ThemedTextField(placeholder: "Set", text: $set)
                        ThemedTextField(placeholder: "Card #", text: $cardNumber)

                        Picker("Sport", selection: $sport) {
                            ForEach(Card.Sport.allCases, id: \.self) { sport in
                                Text(sport.displayName).tag(sport)
                            }
                        }
                        .pickerStyle(.menu)

                        ThemedTextField(placeholder: "Purchase Price", text: $purchasePrice, keyboardType: .decimalPad)

                        VStack(alignment: .leading) {
                            Text("Notes")
                                .font(Theme.Typography.caption)
                                .foregroundColor(Theme.Colors.textSecondary)
                            TextEditor(text: $notes)
                                .frame(height: 100)
                                .padding(Theme.Spacing.sm)
                                .background(Theme.Colors.bgCard)
                                .cornerRadius(Theme.CornerRadius.medium)
                        }
                    }
                    .padding(Theme.Spacing.lg)
                }
            }
            .navigationTitle("Edit Card")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(Theme.Colors.accent)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        Task { await saveChanges() }
                    }
                    .foregroundColor(Theme.Colors.accent)
                    .disabled(isSaving)
                }
            }
        }
    }

    private func saveChanges() async {
        isSaving = true

        var updatedCard = card
        updatedCard.playerName = playerName
        updatedCard.team = team.isEmpty ? nil : team
        updatedCard.year = year.isEmpty ? nil : year
        updatedCard.set = set.isEmpty ? nil : set
        updatedCard.cardNumber = cardNumber.isEmpty ? nil : cardNumber
        updatedCard.sport = sport
        updatedCard.condition = condition
        updatedCard.purchasePrice = Double(purchasePrice)
        updatedCard.notes = notes.isEmpty ? nil : notes

        if await cardStore.updateCard(updatedCard) {
            dismiss()
        }

        isSaving = false
    }
}

#Preview {
    NavigationView {
        CardDetailView(card: Card(
            id: "1",
            playerName: "Michael Jordan",
            team: "Chicago Bulls",
            year: "1986",
            set: "Fleer",
            cardNumber: "57",
            manufacturer: "Fleer",
            sport: .basketball,
            condition: .nearMint,
            grading: Card.Grading(company: .psa, grade: "10", certNumber: "12345678"),
            frontImageUrl: nil,
            backImageUrl: nil,
            purchasePrice: 50000,
            estimatedValue: 75000,
            notes: "Iconic rookie card",
            createdAt: Date(),
            updatedAt: Date()
        ))
        .environmentObject(CardStore())
    }
    .preferredColorScheme(.dark)
}
