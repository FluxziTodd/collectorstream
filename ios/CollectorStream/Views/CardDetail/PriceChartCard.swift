import SwiftUI
import Charts

/// Price history chart card with timeframe selector
struct PriceChartCard: View {
    let history: [MarketDataPoint]
    @Binding var selectedTimeframe: TimeFrame
    let isLoading: Bool
    let stats: ChartStats?

    var body: some View {
        CardContainer {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                // Header
                HStack {
                    Image(systemName: "chart.xyaxis.line")
                        .foregroundColor(Theme.Colors.accent)
                    Text("Price History")
                        .font(Theme.Typography.headline)
                        .foregroundColor(Theme.Colors.textPrimary)
                    Spacer()
                }

                // Timeframe selector
                TimeframeSelector(selected: $selectedTimeframe)

                // Chart or loading/empty state
                if isLoading {
                    ChartLoadingView()
                } else if history.isEmpty {
                    EmptyChartView()
                } else {
                    PriceChart(data: history)
                        .frame(height: 200)
                }

                // Chart summary stats
                if let stats = stats, !history.isEmpty {
                    ChartSummaryRow(stats: stats)
                }
            }
            .padding(Theme.Spacing.md)
        }
    }
}

// MARK: - Price Chart
private struct PriceChart: View {
    let data: [MarketDataPoint]

    var body: some View {
        Chart(data) { point in
            // Line mark
            LineMark(
                x: .value("Date", point.checkedAt),
                y: .value("Price", point.marketPrice)
            )
            .foregroundStyle(Theme.Colors.accent)
            .lineStyle(StrokeStyle(lineWidth: 2))

            // Area fill with gradient
            AreaMark(
                x: .value("Date", point.checkedAt),
                y: .value("Price", point.marketPrice)
            )
            .foregroundStyle(
                LinearGradient(
                    colors: [
                        Theme.Colors.accent.opacity(0.3),
                        Theme.Colors.accent.opacity(0.0)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        }
        .chartXAxis {
            AxisMarks(values: .automatic) { value in
                AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                    .foregroundStyle(Theme.Colors.border)
                AxisValueLabel {
                    if let date = value.as(Date.self) {
                        Text(date, format: .dateTime.month().day())
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textMuted)
                    }
                }
            }
        }
        .chartYAxis {
            AxisMarks { value in
                AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                    .foregroundStyle(Theme.Colors.border)
                AxisValueLabel {
                    if let price = value.as(Double.self) {
                        Text("$\(Int(price))")
                            .font(Theme.Typography.caption)
                            .foregroundColor(Theme.Colors.textMuted)
                    }
                }
            }
        }
        .chartPlotStyle { plotArea in
            plotArea
                .background(Theme.Colors.bgPrimary)
        }
    }
}

// MARK: - Chart Summary Row
private struct ChartSummaryRow: View {
    let stats: ChartStats

    var body: some View {
        HStack(spacing: Theme.Spacing.lg) {
            StatItem(label: "Low", value: "$\(Int(stats.lowest))", color: Theme.Colors.danger)
            StatItem(label: "High", value: "$\(Int(stats.highest))", color: Theme.Colors.success)
            StatItem(label: "Avg", value: "$\(Int(stats.average))", color: Theme.Colors.info)
        }
        .padding(.top, Theme.Spacing.sm)
    }
}

private struct StatItem: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textSecondary)
            Text(value)
                .font(Theme.Typography.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
    }
}

// MARK: - Loading View
private struct ChartLoadingView: View {
    var body: some View {
        VStack(spacing: Theme.Spacing.md) {
            ProgressView()
                .tint(Theme.Colors.accent)
            Text("Loading price history...")
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textMuted)
        }
        .frame(height: 200)
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Empty Chart View
private struct EmptyChartView: View {
    var body: some View {
        VStack(spacing: Theme.Spacing.md) {
            Image(systemName: "chart.line.downtrend.xyaxis")
                .font(.system(size: 48))
                .foregroundColor(Theme.Colors.textMuted)
            Text("No price history available")
                .font(Theme.Typography.body)
                .foregroundColor(Theme.Colors.textSecondary)
            Text("Price data will appear here once market values are tracked")
                .font(Theme.Typography.caption)
                .foregroundColor(Theme.Colors.textMuted)
                .multilineTextAlignment(.center)
        }
        .frame(height: 200)
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Preview
#Preview {
    let sampleData = (1...30).map { day in
        MarketDataPoint(
            id: UUID().uuidString,
            marketPrice: Double.random(in: 80...120),
            sampleSize: 10,
            confidenceLevel: 0.85,
            priceRangeLow: 70,
            priceRangeHigh: 130,
            checkedAt: Calendar.current.date(byAdding: .day, value: -day, to: Date())!
        )
    }.reversed()

    let stats = ChartStats(lowest: 80, highest: 120, average: 100)

    return VStack {
        PriceChartCard(
            history: Array(sampleData),
            selectedTimeframe: .constant(.month),
            isLoading: false,
            stats: stats
        )
    }
    .padding()
    .background(Theme.Colors.bgPrimary)
}
