import SwiftUI

/// Small AI recommendation badge for card grid items
struct AIBadge: View {
    let action: RecommendationAction
    let confidence: Double

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: action.icon)
                .font(.system(size: 10, weight: .semibold))
            Text(action.shortText)
                .font(.system(size: 10, weight: .bold))
        }
        .foregroundColor(.white)
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(action.color)
        .cornerRadius(4)
        .shadow(color: .black.opacity(0.3), radius: 2, x: 0, y: 1)
    }
}

/// AI badge with confidence percentage
struct AIBadgeWithConfidence: View {
    let action: RecommendationAction
    let confidence: Double

    var body: some View {
        VStack(spacing: 2) {
            AIBadge(action: action, confidence: confidence)

            Text("\(Int(confidence * 100))%")
                .font(.system(size: 8, weight: .medium))
                .foregroundColor(action.color)
                .padding(.horizontal, 4)
                .padding(.vertical, 1)
                .background(action.color.opacity(0.15))
                .cornerRadius(2)
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        HStack(spacing: 12) {
            AIBadge(action: .buyMore, confidence: 0.85)
            AIBadge(action: .hold, confidence: 0.70)
            AIBadge(action: .sell, confidence: 0.80)
            AIBadge(action: .cutLoss, confidence: 0.90)
        }

        HStack(spacing: 12) {
            AIBadgeWithConfidence(action: .buyMore, confidence: 0.85)
            AIBadgeWithConfidence(action: .hold, confidence: 0.70)
            AIBadgeWithConfidence(action: .sell, confidence: 0.80)
            AIBadgeWithConfidence(action: .cutLoss, confidence: 0.90)
        }
    }
    .padding()
    .background(Theme.Colors.bgCard)
}
