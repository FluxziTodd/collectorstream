import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 2

    var body: some View {
        TabView(selection: $selectedTab) {
            CollectionView(selectedTab: $selectedTab)
                .tabItem {
                    Label("Collection", systemImage: "square.grid.2x2")
                }
                .tag(0)

            ScanCardView(selectedTab: $selectedTab)
                .tabItem {
                    Label("Scan", systemImage: "camera.viewfinder")
                }
                .tag(1)

            DraftBoardView()
                .tabItem {
                    Label("Draft Board", systemImage: "list.number")
                }
                .tag(2)

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.circle")
                }
                .tag(3)
        }
        .tint(Theme.Colors.accent)
    }
}

#Preview {
    MainTabView()
        .environmentObject(AuthManager())
        .environmentObject(CardStore())
        .preferredColorScheme(.dark)
}
