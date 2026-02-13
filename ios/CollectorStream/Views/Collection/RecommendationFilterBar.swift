import SwiftUI

/// Filter options for recommendations
enum RecommendationFilter: String, CaseIterable, Identifiable {
    case all = "All"
    case buyMore = "Buy More"
    case hold = "Hold"
    case sell = "Sell"
    case needsAttention = "Needs Attention"

    var id: String { rawValue }

    /// Matches recommendation action
    func matches(_ action: RecommendationAction) -> Bool {
        switch self {
        case .all: return true
        case .buyMore: return action == .buyMore
        case .hold: return action == .hold
        case .sell: return action == .sell
        case .needsAttention: return action == .sell || action == .cutLoss
        }
    }

    /// Color for the filter pill
    var color: Color {
        switch self {
        case .all: return Theme.Colors.textPrimary
        case .buyMore: return Theme.Colors.success
        case .hold: return Theme.Colors.info
        case .sell: return Theme.Colors.warning
        case .needsAttention: return Theme.Colors.danger
        }
    }
}

/// Horizontal filter bar with recommendation pills
struct RecommendationFilterBar: View {
    @Binding var selected: RecommendationFilter
    let counts: [RecommendationFilter: Int]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(RecommendationFilter.allCases) { filter in
                    FilterPill(
                        filter: filter,
                        count: counts[filter] ?? 0,
                        isSelected: selected == filter
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selected = filter
                        }
                    }
                }
            }
            .padding(.horizontal, Theme.Spacing.md)
        }
        .frame(height: 40)
    }
}

// MARK: - Filter Pill
private struct FilterPill: View {
    let filter: RecommendationFilter
    let count: Int
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Text(filter.rawValue)
                    .font(Theme.Typography.caption)
                    .fontWeight(isSelected ? .semibold : .medium)

                if count > 0 {
                    Text("\(count)")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(isSelected ? .white : filter.color)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 2)
                        .background(
                            isSelected ? filter.color.opacity(0.3) : Theme.Colors.bgSecondary
                        )
                        .cornerRadius(8)
                }
            }
            .foregroundColor(isSelected ? .white : Theme.Colors.textSecondary)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                isSelected ? filter.color : Theme.Colors.bgCard
            )
            .cornerRadius(Theme.CornerRadius.small)
            .overlay(
                RoundedRectangle(cornerRadius: Theme.CornerRadius.small)
                    .stroke(isSelected ? filter.color : Theme.Colors.border, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        RecommendationFilterBar(
            selected: .constant(.all),
            counts: [
                .all: 24,
                .buyMore: 5,
                .hold: 12,
                .sell: 4,
                .needsAttention: 3
            ]
        )

        RecommendationFilterBar(
            selected: .constant(.buyMore),
            counts: [
                .all: 24,
                .buyMore: 5,
                .hold: 12,
                .sell: 4,
                .needsAttention: 3
            ]
        )
    }
    .background(Theme.Colors.bgPrimary)
}
