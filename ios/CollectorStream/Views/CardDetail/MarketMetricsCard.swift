import SwiftUI

/// Market metrics card showing trends, volatility, and momentum
struct MarketMetricsCard: View {
    let metrics: TrendMetrics?
    let purchasePrice: Double?
    let currentValue: Double?

    var body: some View {
        CardContainer {
            VStack(spacing: Theme.Spacing.md) {
                // Header
                HStack {
                    Image(systemName: "chart.bar.fill")
                        .foregroundColor(Theme.Colors.info)
                    Text("Market Metrics")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                if let metrics = metrics {
                    // Trend indicators
                    HStack(spacing: Theme.Spacing.lg) {
                        TrendColumn(label: "7D Trend", value: metrics.trend7d)
                        TrendColumn(label: "30D Trend", value: metrics.trend30d)
                        TrendColumn(label: "90D Trend", value: metrics.trend90d)
                    }

                    Divider()
                        .background(Theme.Colors.border)

                    // Volatility and momentum
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Volatility")
                                .font(Theme.Typography.caption)
                                .foregroundColor(Theme.Colors.textSecondary)
                            Text(formatPercent(metrics.volatility))
                                .font(Theme.Typography.subheadline)
                                .fontWeight(.semibold)
                                .foregroundColor(Theme.Colors.textPrimary)
                        }

                        Spacer()

                        VStack(alignment: .trailing, spacing: 4) {
                            Text("Momentum")
                                .font(Theme.Typography.caption)
                                .foregroundColor(Theme.Colors.textSecondary)
                            MomentumBadge(momentum: metrics.momentum)
                        }
                    }

                    // ROI display if purchase price available
                    if let purchase = purchasePrice, let current = currentValue {
                        Divider()
                            .background(Theme.Colors.border)

                        ROIDisplay(purchasePrice: purchase, currentValue: current)
                    }
                } else {
                    // Loading state
                    VStack(spacing: Theme.Spacing.sm) {
                        ProgressView()
                            .tint(Theme.Colors.accent)
                        Text("Loading metrics...")
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textMuted)
                    }
                    .frame(height: 80)
                }
            }
            .padding(Theme.Spacing.md)
        }
    }

    private func formatPercent(_ value: Double) -> String {
        let formatted = String(format: "%.1f", abs(value))
        return value >= 0 ? "+\(formatted)%" : "-\(formatted)%"
    }
}

// MARK: - Trend Column
private struct TrendColumn: View {
    let label: String
    let value: Double

    var body: some View {
        VStack(spacing: 4) {
            Text(label)
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textSecondary)

            HStack(spacing: 2) {
                Image(systemName: value >= 0 ? "arrow.up" : "arrow.down")
                    .font(.system(size: 10, weight: .bold))
                Text(formatValue(value))
                    .font(Theme.Typography.subheadline)
                    .fontWeight(.semibold)
            }
            .foregroundColor(value >= 0 ? Theme.Colors.success : Theme.Colors.danger)
        }
    }

    private func formatValue(_ val: Double) -> String {
        String(format: "%.1f%%", abs(val))
    }
}

// MARK: - Momentum Badge
struct MomentumBadge: View {
    let momentum: Momentum

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: momentum.icon)
                .font(.system(size: 10))
            Text(momentum.displayName)
                .font(Theme.Typography.caption)
                .fontWeight(.medium)
        }
        .foregroundColor(color)
        .padding(.horizontal, Theme.Spacing.sm)
        .padding(.vertical, 4)
        .background(color.opacity(0.15))
        .cornerRadius(Theme.CornerRadius.small)
    }

    private var color: Color {
        switch momentum {
        case .accelerating: return Theme.Colors.success
        case .steady: return Theme.Colors.info
        case .decelerating: return Theme.Colors.danger
        }
    }
}

// MARK: - ROI Display
struct ROIDisplay: View {
    let purchasePrice: Double
    let currentValue: Double

    var body: some View {
        VStack(spacing: Theme.Spacing.sm) {
            HStack {
                Text("Return on Investment")
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                Spacer()
            }

            HStack(spacing: Theme.Spacing.lg) {
                // Purchase price
                VStack(spacing: 2) {
                    Text("Purchase")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text("$\(Int(purchasePrice))")
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)
                }

                Image(systemName: "arrow.right")
                    .foregroundColor(Theme.Colors.textMuted)

                // Current value
                VStack(spacing: 2) {
                    Text("Current")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text("$\(Int(currentValue))")
                        .font(Theme.Typography.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(Theme.Colors.textPrimary)
                }

                Spacer()

                // ROI percentage
                VStack(spacing: 2) {
                    Text("ROI")
                        .font(Theme.Typography.caption)
                        .foregroundColor(Theme.Colors.textSecondary)
                    Text(roiText)
                        .font(Theme.Typography.title3)
                        .fontWeight(.bold)
                        .foregroundColor(roiColor)
                }
            }
        }
    }

    private var roi: Double {
        guard purchasePrice > 0 else { return 0 }
        return ((currentValue - purchasePrice) / purchasePrice) * 100
    }

    private var roiText: String {
        let formatted = String(format: "%.1f%%", abs(roi))
        return roi >= 0 ? "+\(formatted)" : "-\(formatted)"
    }

    private var roiColor: Color {
        roi >= 0 ? Theme.Colors.success : Theme.Colors.danger
    }
}

// MARK: - Preview
#Preview {
    let sampleMetrics = TrendMetrics(
        trend7d: 5.2,
        trend30d: 12.5,
        trend90d: -3.1,
        volatility: 15.0,
        momentum: .accelerating,
        sampleSize: 45
    )

    return VStack(spacing: Theme.Spacing.lg) {
        MarketMetricsCard(
            metrics: sampleMetrics,
            purchasePrice: 100,
            currentValue: 125
        )

        MarketMetricsCard(
            metrics: nil,
            purchasePrice: nil,
            currentValue: nil
        )
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
