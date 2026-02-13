import SwiftUI

/// Small stat card for dashboard grid
struct QuickStatCard: View {
    let icon: String
    let label: String
    let value: String
    let color: Color

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.sm) {
                // Icon
                Image(systemName: icon)
                    .font(.system(size: 28))
                    .foregroundColor(color)

                // Value
                Text(value)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(Theme.Colors.textPrimary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.5)

                // Label
                Text(label)
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .padding(Theme.Spacing.md)
            .frame(maxWidth: .infinity)
        }
    }
}

// MARK: - Preview
#Preview {
    LazyVGrid(
        columns: [
            GridItem(.flexible(), spacing: 12),
            GridItem(.flexible(), spacing: 12)
        ],
        spacing: 12
    ) {
        QuickStatCard(
            icon: "rectangle.stack.fill",
            label: "Total Cards",
            value: "24",
            color: Theme.Colors.accent
        )

        QuickStatCard(
            icon: "chart.line.uptrend.xyaxis",
            label: "Top Gainer",
            value: "Mahomes",
            color: Theme.Colors.success
        )

        QuickStatCard(
            icon: "dollarsign.circle.fill",
            label: "Avg. Value",
            value: "$145",
            color: Theme.Colors.info
        )

        QuickStatCard(
            icon: "chart.bar.fill",
            label: "Holdings",
            value: "12 Players",
            color: Theme.Colors.warning
        )
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
