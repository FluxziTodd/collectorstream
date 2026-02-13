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
                    // Header Card
                    VStack(spacing: Theme.Spacing.md) {
                        // Title & Description
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Mock Draft Boards")
                                .font(Theme.Typography.title2)
                                .fontWeight(.bold)
                                .foregroundColor(Theme.Colors.textPrimary)
                            Text("Track player stock movement and find undervalued cards")
                                .font(Theme.Typography.caption)
                                .foregroundColor(Theme.Colors.textSecondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, Theme.Spacing.md)
                        .padding(.top, Theme.Spacing.sm)

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
                        }
                    }
                    .padding(.bottom, Theme.Spacing.md)
                    .background(Theme.Colors.bgSecondary)

                    // Draft Board Content (WebView to collectorstream.com)
                    DraftBoardWebView(sport: selectedSport, year: selectedYear)
                }
            }
            .navigationBarHidden(true)
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
        let config = WKWebViewConfiguration()
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = UIColor(Theme.Colors.bgPrimary)
        webView.scrollView.backgroundColor = UIColor(Theme.Colors.bgPrimary)

        // Inject CSS for mobile-optimized table view
        let css = """
        /* Hide everything except the table */
        body > *:not(main) { display: none !important; }
        nav, header, footer, .hero, .features, .stats { display: none !important; }

        body {
            background: #0a0a0a !important;
            color: #ffffff !important;
            font-family: -apple-system, system-ui, sans-serif !important;
            margin: 0 !important;
            padding: 8px !important;
        }

        main {
            padding: 0 !important;
            max-width: 100% !important;
        }

        .picks-table-container {
            background: #151515 !important;
            border: 1px solid #1f1f1f !important;
            border-radius: 12px !important;
            overflow-x: auto !important;
            margin: 0 !important;
        }

        .picks-table {
            width: 100% !important;
            border-collapse: collapse !important;
            font-size: 12px !important;
        }

        .picks-table th {
            background: #111111 !important;
            color: #9ca3af !important;
            padding: 12px 8px !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border-bottom: 1px solid #1f1f1f !important;
            position: sticky !important;
            top: 0 !important;
            white-space: nowrap !important;
        }

        .picks-table td {
            padding: 12px 8px !important;
            border-bottom: 1px solid #1f1f1f !important;
            color: #ffffff !important;
        }

        .picks-table tr:last-child td {
            border-bottom: none !important;
        }

        /* Rank column */
        .picks-table td:first-child {
            color: #10b981 !important;
            font-weight: 600 !important;
            text-align: center !important;
            width: 40px !important;
        }

        /* Player cell */
        .player-cell {
            display: flex !important;
            flex-direction: column !important;
            gap: 2px !important;
        }

        .player-cell-name {
            font-weight: 600 !important;
            color: #ffffff !important;
            font-size: 13px !important;
        }

        .player-cell-pos {
            font-size: 11px !important;
            color: #9ca3af !important;
        }

        /* Sport badge */
        .sport-badge {
            display: inline-block !important;
            padding: 3px 8px !important;
            background: rgba(16, 185, 129, 0.1) !important;
            color: #10b981 !important;
            border-radius: 6px !important;
            font-size: 11px !important;
            font-weight: 600 !important;
        }

        /* Mock change */
        .mock-change {
            display: inline-flex !important;
            align-items: center !important;
            gap: 4px !important;
            font-size: 12px !important;
        }

        .mock-change.up {
            color: #10b981 !important;
        }

        .mock-change.down {
            color: #ef4444 !important;
        }

        .mock-change svg {
            width: 14px !important;
            height: 14px !important;
        }

        /* Price change */
        .price-change {
            font-weight: 600 !important;
            font-size: 12px !important;
        }

        .price-change.positive {
            color: #10b981 !important;
        }

        .price-change.negative {
            color: #ef4444 !important;
        }

        /* Signal badge */
        .signal-badge {
            display: inline-block !important;
            padding: 4px 10px !important;
            border-radius: 6px !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
        }

        .signal-strong-buy {
            background: rgba(16, 185, 129, 0.2) !important;
            color: #10b981 !important;
            border: 1px solid #10b981 !important;
        }

        .signal-buy {
            background: rgba(59, 130, 246, 0.2) !important;
            color: #3b82f6 !important;
            border: 1px solid #3b82f6 !important;
        }

        .signal-hold {
            background: rgba(245, 158, 11, 0.2) !important;
            color: #f59e0b !important;
            border: 1px solid #f59e0b !important;
        }

        .signal-sell {
            background: rgba(239, 68, 68, 0.2) !important;
            color: #ef4444 !important;
            border: 1px solid #ef4444 !important;
        }

        /* Mobile optimization */
        @media (max-width: 768px) {
            .picks-table th:nth-child(4),
            .picks-table td:nth-child(4) {
                display: none !important;
            }
        }
        """

        let script = WKUserScript(
            source: """
            var style = document.createElement('style');
            style.innerHTML = '\(css)';
            document.head.appendChild(style);
            """,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: true
        )
        config.userContentController.addUserScript(script)

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
