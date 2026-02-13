import SwiftUI

/// Horizontal pill selector for chart timeframes
struct TimeframeSelector: View {
    @Binding var selected: TimeFrame

    var body: some View {
        HStack(spacing: 8) {
            ForEach(TimeFrame.allCases, id: \.self) { timeframe in
                TimeframePill(
                    timeframe: timeframe,
                    isSelected: selected == timeframe
                ) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selected = timeframe
                    }
                }
            }
        }
    }
}

// MARK: - Timeframe Pill
private struct TimeframePill: View {
    let timeframe: TimeFrame
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(timeframe.rawValue)
                .font(Theme.Typography.caption)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .white : Theme.Colors.textSecondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Theme.Colors.accent : Theme.Colors.bgSecondary)
                .cornerRadius(Theme.CornerRadius.small)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: Theme.Spacing.lg) {
        TimeframeSelector(selected: .constant(.week))
        TimeframeSelector(selected: .constant(.month))
        TimeframeSelector(selected: .constant(.year))
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
