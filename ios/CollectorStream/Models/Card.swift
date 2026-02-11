import Foundation

/// Represents a sports card in the collection
struct Card: Codable, Identifiable, Equatable {
    let id: String
    var playerName: String
    var team: String?
    var year: String?
    var set: String?
    var cardNumber: String?
    var manufacturer: String?
    var sport: Sport
    var condition: Condition?
    var grading: Grading?
    var frontImageUrl: String?
    var backImageUrl: String?
    var purchasePrice: Double?
    var estimatedValue: Double?
    var notes: String?
    var createdAt: Date
    var updatedAt: Date

    // MARK: - Sport Enum
    enum Sport: String, Codable, CaseIterable {
        case baseball = "MLB"
        case basketball = "NBA"
        case football = "NFL"
        case hockey = "NHL"
        case wnba = "WNBA"
        case soccer = "Soccer"
        case other = "Other"

        var displayName: String {
            switch self {
            case .baseball: return "Baseball"
            case .basketball: return "Basketball"
            case .football: return "Football"
            case .hockey: return "Hockey"
            case .wnba: return "WNBA"
            case .soccer: return "Soccer"
            case .other: return "Other"
            }
        }

        var icon: String {
            switch self {
            case .baseball: return "figure.baseball"
            case .basketball, .wnba: return "figure.basketball"
            case .football: return "figure.american.football"
            case .hockey: return "figure.hockey"
            case .soccer: return "figure.soccer"
            case .other: return "sportscourt"
            }
        }
    }

    // MARK: - Condition Enum
    enum Condition: String, Codable, CaseIterable {
        case mint = "Mint"
        case nearMint = "Near Mint"
        case excellent = "Excellent"
        case veryGood = "Very Good"
        case good = "Good"
        case fair = "Fair"
        case poor = "Poor"

        var abbreviation: String {
            switch self {
            case .mint: return "M"
            case .nearMint: return "NM"
            case .excellent: return "EX"
            case .veryGood: return "VG"
            case .good: return "G"
            case .fair: return "F"
            case .poor: return "P"
            }
        }
    }

    // MARK: - Grading
    struct Grading: Codable, Equatable {
        var company: GradingCompany
        var grade: String
        var certNumber: String?

        enum GradingCompany: String, Codable, CaseIterable {
            case psa = "PSA"
            case bgs = "BGS"
            case sgc = "SGC"
            case cgc = "CGC"
            case hga = "HGA"
            case other = "Other"
        }
    }
}

// MARK: - Card Upload (for creating new cards)
struct CardUpload: Codable {
    var playerName: String
    var team: String?
    var year: String?
    var set: String?
    var cardNumber: String?
    var manufacturer: String?
    var sport: Card.Sport
    var condition: Card.Condition?
    var gradingCompany: String?
    var gradingGrade: String?
    var gradingCertNumber: String?
    var frontImageUrl: String?
    var backImageUrl: String?
    var estimatedValue: Double?
    var purchasePrice: Double?
    var notes: String?
}

// MARK: - Card Store
@MainActor
class CardStore: ObservableObject {
    @Published var cards: [Card] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let apiClient = APIClient.shared

    // MARK: - Fetch Cards
    func fetchCards() async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiClient.getCards()
            cards = response.cards
            print("📥 Fetched \(cards.count) cards")
            if let firstCard = cards.first {
                print("   First card: \(firstCard.playerName)")
                print("   frontImageUrl: \(firstCard.frontImageUrl ?? "nil")")
                print("   backImageUrl: \(firstCard.backImageUrl ?? "nil")")
                print("   estimatedValue: \(firstCard.estimatedValue ?? 0)")
                print("   sport: \(firstCard.sport.rawValue)")
            }
            print("💰 Total collection value: $\(totalValue)")
            isLoading = false
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
        } catch {
            errorMessage = "Failed to load cards"
            isLoading = false
        }
    }

    // MARK: - Add Card
    func addCard(_ card: CardUpload) async -> Card? {
        isLoading = true
        errorMessage = nil

        do {
            print("🔄 CardStore: Calling API to add card...")
            let newCard = try await apiClient.addCard(card)
            print("✅ CardStore: Card added successfully")
            cards.insert(newCard, at: 0)
            isLoading = false
            return newCard
        } catch let error as APIError {
            print("❌ CardStore: APIError - \(error)")
            print("   User message: \(error.userMessage)")
            errorMessage = error.userMessage
            isLoading = false
            return nil
        } catch {
            print("❌ CardStore: Generic error - \(error.localizedDescription)")
            print("   Full error: \(error)")
            errorMessage = "Failed to add card"
            isLoading = false
            return nil
        }
    }

    // MARK: - Update Card
    func updateCard(_ card: Card) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            let updatedCard = try await apiClient.updateCard(card)
            if let index = cards.firstIndex(where: { $0.id == card.id }) {
                cards[index] = updatedCard
            }
            isLoading = false
            return true
        } catch let error as APIError {
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            errorMessage = "Failed to update card"
            isLoading = false
            return false
        }
    }

    // MARK: - Delete Card
    func deleteCard(_ cardId: String) async -> Bool {
        isLoading = true
        errorMessage = nil

        do {
            print("🗑️ CardStore: Deleting card \(cardId)...")
            try await apiClient.deleteCard(cardId)
            cards.removeAll { $0.id == cardId }
            print("✅ CardStore: Card deleted successfully")
            isLoading = false
            return true
        } catch let error as APIError {
            print("❌ CardStore: Delete failed - \(error)")
            print("   User message: \(error.userMessage)")
            errorMessage = error.userMessage
            isLoading = false
            return false
        } catch {
            print("❌ CardStore: Delete failed - \(error.localizedDescription)")
            errorMessage = "Failed to delete card"
            isLoading = false
            return false
        }
    }

    // MARK: - Statistics
    var totalCards: Int { cards.count }

    var totalValue: Double {
        cards.compactMap(\.estimatedValue).reduce(0, +)
    }

    var cardsBySport: [Card.Sport: [Card]] {
        Dictionary(grouping: cards, by: \.sport)
    }
}
