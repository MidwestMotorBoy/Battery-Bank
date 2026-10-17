import SwiftUI

/// FakePack: the Monolith pack, simulated on the Mac's Bluetooth radio.
/// See docs/app/README.md. Generate the Xcode project with `xcodegen` in `app/`.
@main
@MainActor
struct FakePackApp: App {
    @NSApplicationDelegateAdaptor private var appDelegate: AppDelegate
    @StateObject private var model: PackModel
    @StateObject private var server: PeripheralServer

    init() {
        let m = PackModel()
        _model = StateObject(wrappedValue: m)
        _server = StateObject(wrappedValue: PeripheralServer(model: m))
    }

    var body: some Scene {
        WindowGroup("FakePack") {
            ContentView()
                .environmentObject(model)
                .environmentObject(server)
        }
    }
}

/// Closing the window quits, so the fake pack never keeps advertising unseen.
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}
