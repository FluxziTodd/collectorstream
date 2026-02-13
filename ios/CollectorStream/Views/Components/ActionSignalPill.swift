import SwiftUI

/// Colored pill showing action signal with count
struct ActionSignalPill: View {
    let action: String
    let count: Int
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Text(action)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.white)

            Text("\(count)")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(color)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.white.opacity(0.3))
                .cornerRadius(8)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color)
        .cornerRadius(Theme.CornerRadius.small)
    }
}

// MARK: - Preview
#Preview {
    HStack(spacing: 8) {
        ActionSignalPill(action: "BUY", count: 5, color: Theme.Colors.success)
        ActionSignalPill(action: "HOLD", count: 12, color: Theme.Colors.info)
        ActionSignalPill(action: "SELL", count: 4, color: Theme.Colors.warning)
        ActionSignalPill(action: "CUT", count: 2, color: Theme.Colors.danger)
    }
    .padding()
    .background(Theme.Colors.bgCard)
}
