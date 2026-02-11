import SwiftUI

/// View for browsing draft boards from CollectorStream
struct DraftBoardView: View {
    @State private var selectedSport: String = "wnba"
    @State private var selectedYear: Int = 2026
    @State private var isLoading = false

    let sports = [
        ("wnba", "WNBA"),
        ("nba", "NBA"),
        ("nfl", "NFL"),
        ("mlb", "MLB"),
        ("nhl", "NHL")
    ]

    let years = [2026, 2027, 2028, 2029, 2030]

    var body: some View {
        NavigationView {
            ZStack {
                Theme.Colors.bgPrimary
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Sport Selector
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: Theme.Spacing.sm) {
                            ForEach(sports, id: \.0) { sport in
                                SportButton(
                                    code: sport.0,
                                    name: sport.1,
                                    isSelected: selectedSport == sport.0
                                ) {
                                    selectedSport = sport.0
                                }
                            }
                        }
                        .padding(.horizontal, Theme.Spacing.md)
                        .padding(.vertical, Theme.Spacing.sm)
                    }

                    // Year Selector
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: Theme.Spacing.sm) {
                            ForEach(years, id: \.self) { year in
                                YearButton(
                                    year: year,
                                    isSelected: selectedYear == year
                                ) {
                                    selectedYear = year
                                }
                            }
                        }
                        .padding(.horizontal, Theme.Spacing.md)
                        .padding(.vertical, Theme.Spacing.sm)
                    }

                    Divider()
                        .background(Theme.Colors.border)

                    // Draft Board Content (WebView to collectorstream.com)
                    DraftBoardWebView(sport: selectedSport, year: selectedYear)
                }
            }
            .navigationTitle("Draft Boards")
        }
    }
}

struct SportButton: View {
    let code: String
    let name: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: sportIcon)
                    .font(.system(size: 24))
                Text(name)
                    .font(Theme.Typography.caption)
            }
            .foregroundColor(isSelected ? .white : Theme.Colors.textSecondary)
            .frame(width: 60, height: 60)
            .background(isSelected ? Theme.Colors.accent : Theme.Colors.bgCard)
            .cornerRadius(Theme.CornerRadius.medium)
            .overlay(
                RoundedRectangle(cornerRadius: Theme.CornerRadius.medium)
                    .stroke(isSelected ? Theme.Colors.accent : Theme.Colors.border, lineWidth: 1)
            )
        }
    }

    private var sportIcon: String {
        switch code {
        case "wnba", "nba": return "figure.basketball"
        case "nfl": return "figure.american.football"
        case "mlb": return "figure.baseball"
        case "nhl": return "figure.hockey"
        default: return "sportscourt"
        }
    }
}

struct YearButton: View {
    let year: Int
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(String(year))
                .font(Theme.Typography.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .white : Theme.Colors.textSecondary)
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.vertical, Theme.Spacing.sm)
                .background(isSelected ? Theme.Colors.accent : Theme.Colors.bgCard)
                .cornerRadius(Theme.CornerRadius.xl)
                .overlay(
                    RoundedRectangle(cornerRadius: Theme.CornerRadius.xl)
                        .stroke(isSelected ? Theme.Colors.accent : Theme.Colors.border, lineWidth: 1)
                )
        }
    }
}

// MARK: - Draft Board WebView
import WebKit

struct DraftBoardWebView: UIViewRepresentable {
    let sport: String
    let year: Int

    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView()
        webView.isOpaque = false
        webView.backgroundColor = UIColor(Theme.Colors.bgPrimary)
        webView.scrollView.backgroundColor = UIColor(Theme.Colors.bgPrimary)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        let urlString = buildURL()
        if let url = URL(string: urlString) {
            let request = URLRequest(url: url)
            webView.load(request)
        }
    }

    private func buildURL() -> String {
        // Build URL based on sport and year
        let baseURL = "https://collectorstream.com"

        switch sport {
        case "wnba":
            return "\(baseURL)/\(year)-board.html"
        case "nba":
            return "\(baseURL)/nba-\(year)-board.html"
        case "nfl":
            return "\(baseURL)/nfl-\(year)-board.html"
        case "mlb":
            return "\(baseURL)/mlb-\(year)-board.html"
        case "nhl":
            return "\(baseURL)/nhl-\(year)-board.html"
        default:
            return "\(baseURL)/\(year)-board.html"
        }
    }
}

#Preview {
    DraftBoardView()
        .preferredColorScheme(.dark)
}
