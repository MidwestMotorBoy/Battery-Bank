import SwiftUI

/// The Monolith iPhone app. See docs/app/README.md.
/// Generate the Xcode project with `xcodegen` in `app/`.
@main
struct MonolithApp: App {
    @StateObject private var store = PackStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(store)
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        if store.hasPack {
            TabView {
                DashboardView().tabItem { Label("Pack", systemImage: "battery.75percent") }
                ChargingView().tabItem { Label("Charging", systemImage: "bolt.fill") }
                TemperaturesView().tabItem { Label("Temps", systemImage: "thermometer.medium") }
                NavigationStack { PackLifeView() }.tabItem { Label("Health", systemImage: "heart.text.square") }
                SettingsView().tabItem { Label("Settings", systemImage: "slider.horizontal.3") }
            }
        } else {
            ConnectView()
        }
    }
}
