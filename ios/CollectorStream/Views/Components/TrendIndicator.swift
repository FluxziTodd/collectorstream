import SwiftUI

/// Small up/down arrow with percentage for price trends
struct TrendIndicator: View {
    let trend: Double // Percentage change

    var body: some View {
        HStack(spacing: 2) {
            Image(systemName: trend >= 0 ? "arrow.up" : "arrow.down")
                .font(.system(size: 8, weight: .bold))
            Text("\(abs(Int(trend)))%")
                .font(.system(size: 9, weight: .semibold))
        }
        .foregroundColor(trend >= 0 ? Theme.Colors.success : Theme.Colors.danger)
    }
}

/// Trend indicator with label
struct LabeledTrendIndicator: View {
    let label: String
    let trend: Double

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(Theme.Colors.textMuted)
            TrendIndicator(trend: trend)
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        HStack(spacing: 16) {
            TrendIndicator(trend: 15.5)
            TrendIndicator(trend: -8.2)
            TrendIndicator(trend: 0.5)
        }

        HStack(spacing: 16) {
            LabeledTrendIndicator(label: "7D", trend: 12.5)
            LabeledTrendIndicator(label: "30D", trend: -5.3)
            LabeledTrendIndicator(label: "90D", trend: 8.7)
        }
    }
    .padding()
    .background(Theme.Colors.bgCard)
}
