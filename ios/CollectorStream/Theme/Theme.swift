import SwiftUI

/// CollectorStream Design System
/// Matching the web portal's dark theme with emerald accent
struct Theme {
    // MARK: - Colors
    struct Colors {
        static let bgPrimary = Color(hex: "0a0a0a")
        static let bgSecondary = Color(hex: "111111")
        static let bgCard = Color(hex: "151515")
        static let border = Color(hex: "1f1f1f")
        static let borderHover = Color(hex: "2a2a2a")
        static let accent = Color(hex: "10b981")      // Emerald green
        static let accentDark = Color(hex: "059669")
        static let textPrimary = Color.white
        static let textSecondary = Color(hex: "9ca3af")
        static let textMuted = Color(hex: "6b7280")
        static let success = Color(hex: "10b981")
        static let warning = Color(hex: "f59e0b")
        static let danger = Color(hex: "ef4444")
        static let info = Color(hex: "3b82f6")
    }

    // MARK: - Typography
    struct Typography {
        static let largeTitle = Font.system(size: 34, weight: .bold, design: .default)
        static let title = Font.system(size: 28, weight: .bold, design: .default)
        static let title2 = Font.system(size: 22, weight: .semibold, design: .default)
        static let title3 = Font.system(size: 20, weight: .semibold, design: .default)
        static let headline = Font.system(size: 17, weight: .semibold, design: .default)
        static let body = Font.system(size: 17, weight: .regular, design: .default)
        static let callout = Font.system(size: 16, weight: .regular, design: .default)
        static let subheadline = Font.system(size: 15, weight: .regular, design: .default)
        static let footnote = Font.system(size: 13, weight: .regular, design: .default)
        static let caption = Font.system(size: 12, weight: .regular, design: .default)
    }

    // MARK: - Spacing
    struct Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
        static let xxl: CGFloat = 48
    }

    // MARK: - Corner Radius
    struct CornerRadius {
        static let small: CGFloat = 8
        static let medium: CGFloat = 12
        static let large: CGFloat = 16
        static let xl: CGFloat = 24
    }
}

// MARK: - Color Extension for Hex
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Gradient
extension Theme {
    struct Gradients {
        static let accent = LinearGradient(
            colors: [Colors.accent, Colors.accentDark],
            startPoint: .leading,
            endPoint: .trailing
        )

        static let topBar = LinearGradient(
            colors: [Colors.accent, Colors.accentDark],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
}
