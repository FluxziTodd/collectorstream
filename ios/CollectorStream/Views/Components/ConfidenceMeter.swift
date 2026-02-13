import SwiftUI

/// Horizontal progress bar showing AI confidence level
struct ConfidenceMeter: View {
    let confidence: Double // 0.0 to 1.0

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                // Background
                RoundedRectangle(cornerRadius: 4)
                    .fill(Theme.Colors.bgSecondary)
                    .frame(height: 8)

                // Fill
                RoundedRectangle(cornerRadius: 4)
                    .fill(confidenceColor)
                    .frame(
                        width: geometry.size.width * CGFloat(min(max(confidence, 0), 1)),
                        height: 8
                    )
                    .animation(.easeInOut(duration: 0.3), value: confidence)
            }
        }
        .frame(height: 8)
    }

    /// Color based on confidence level
    private var confidenceColor: Color {
        if confidence >= 0.8 { return Theme.Colors.success }
        if confidence >= 0.6 { return Theme.Colors.info }
        if confidence >= 0.4 { return Theme.Colors.warning }
        return Theme.Colors.danger
    }
}

/// Confidence meter with label
struct LabeledConfidenceMeter: View {
    let confidence: Double
    let label: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(Theme.Typography.caption)
                    .foregroundColor(Theme.Colors.textSecondary)
                Spacer()
                Text("\(Int(confidence * 100))%")
                    .font(Theme.Typography.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(Theme.Colors.textPrimary)
            }

            ConfidenceMeter(confidence: confidence)
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: Theme.Spacing.lg) {
        LabeledConfidenceMeter(confidence: 0.95, label: "High Confidence")
        LabeledConfidenceMeter(confidence: 0.75, label: "Medium-High Confidence")
        LabeledConfidenceMeter(confidence: 0.55, label: "Medium Confidence")
        LabeledConfidenceMeter(confidence: 0.35, label: "Low Confidence")
    }
    .padding()
    .background(Theme.Colors.bgCard)
}
