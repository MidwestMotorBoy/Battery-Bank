import SwiftUI

/// Scan → pick a pack. Shown until a Protocol Version has been read.
struct ConnectView: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    switch store.link {
                    case .unavailable(let why):
                        Label(why, systemImage: "antenna.radiowaves.left.and.right.slash")
                    case .connecting(let name):
                        HStack { ProgressView(); Text("Connecting to \(name)…").padding(.leading, 6) }
                    case .incompatible(let major):
                        Label("This pack speaks protocol \(major).x. Update the app to use it.", systemImage: "exclamationmark.triangle")
                    case .scanning where store.discovered.isEmpty:
                        HStack { ProgressView(); Text("Looking for packs…").padding(.leading, 6) }
                    default:
                        EmptyView()
                    }
                    ForEach(store.discovered) { pack in
                        Button { store.connect(pack) } label: {
                            HStack {
                                Image(systemName: "battery.100percent").foregroundStyle(.green)
                                Text(pack.name)
                                Spacer()
                                SignalBars(rssi: pack.rssi)
                            }
                        }
                    }
                } footer: {
                    Text("Plug a cable into the pack before pairing a new phone: it only accepts pairing for 2 minutes after a cable is attached.")
                }

                Section {
                    Button("Use demo pack", systemImage: "play.circle") { store.startDemo() }
                } footer: {
                    Text("A simulated pack running inside the app. Bluetooth doesn't work in the iOS Simulator, so the demo is used there.")
                }
            }
            .navigationTitle("Monolith")
            .toolbar {
                Button("Scan", systemImage: "arrow.clockwise") { store.startScan() }
                    .disabled(store.link == .scanning)
            }
            .onAppear { if store.link == .idle { store.startScan() } }
        }
    }
}

struct SignalBars: View {
    let rssi: Int
    private var bars: Int { rssi > -60 ? 3 : rssi > -75 ? 2 : 1 }
    var body: some View {
        HStack(alignment: .bottom, spacing: 2) {
            ForEach(1...3, id: \.self) { i in
                RoundedRectangle(cornerRadius: 1)
                    .frame(width: 4, height: CGFloat(4 * i + 2))
                    .opacity(i <= bars ? 1 : 0.25)
            }
        }
        .foregroundStyle(.secondary)
        .accessibilityLabel("Signal \(bars) of 3")
    }
}
