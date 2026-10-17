import SwiftUI
import CoreBluetooth
import MonolithKit

/// Raw bytes, the pack's debug log and the maintenance commands (spec §4.6, §4.8).
struct DeveloperView: View {
    @EnvironmentObject private var store: PackStore
    @State private var result: String?
    @State private var confirm: Command?

    private static let records: [(String, CBUUID)] = [
        ("Protocol Version", MonolithUUID.protocolVersion), ("Status", MonolithUUID.status),
        ("Ports", MonolithUUID.ports), ("Temperatures", MonolithUUID.temperatures),
        ("Settings", MonolithUUID.settings), ("Gauge Health", MonolithUUID.gaugeHealth), ("Pack Life", MonolithUUID.packLife),
    ]

    var body: some View {
        List {
            Section("Pack") {
                LabeledContent("Name", value: store.packName)
                if let v = store.version {
                    LabeledContent("Firmware", value: v.firmwareString)
                    LabeledContent("Protocol", value: "\(v.protoMajor).\(v.protoMinor)")
                    LabeledContent("Hardware rev", value: "\(v.hwRev)")
                }
                if let s = store.status { LabeledContent("Uptime", value: Duration.seconds(s.uptimeS).formatted(.units(allowed: [.days, .hours, .minutes, .seconds], width: .narrow, maximumUnitCount: 2))) }
            }

            Section {
                Button("Identify (blink LED)") { run(.identify) }
                Button("Allow another phone to pair") { run(.openPairing) }
                Button("Re-test sensors") { run(.clearSensorFaults) }
                Button("Restart pack controller") { confirm = .resetMCU }
                Button("Enter firmware update mode") { confirm = .enterOTA }
                Button("Ship mode (power off for storage)", role: .destructive) { confirm = .shipMode }
                Button("Forget all paired phones", role: .destructive) { confirm = .clearBonds }
            } header: {
                Text("Commands")
            } footer: {
                if let result { Text(result) }
            }
            .disabled(!store.isLive)

            Section("Raw values") {
                ForEach(Self.records, id: \.1) { name, uuid in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(name).font(.caption).foregroundStyle(.secondary)
                        Text(store.raw[uuid].map(Fmt.hex) ?? "—").font(.caption.monospaced()).textSelection(.enabled)
                    }
                }
            }

            Section("Debug log") {
                if store.debugLines.isEmpty {
                    Text("Nothing yet.").foregroundStyle(.secondary)
                }
                ForEach(Array(store.debugLines.suffix(100).reversed().enumerated()), id: \.offset) { _, line in
                    Text(line).font(.caption.monospaced())
                }
            }

            Section {
                Button(store.isDemo ? "Leave demo" : "Forget this pack", role: .destructive) { store.forget() }
            }
        }
        .navigationTitle("Developer")
        // The debug log is only subscribed while this screen is visible (keep the radio quiet).
        .onAppear { store.setDebugLog(true) }
        .onDisappear { store.setDebugLog(false) }
        .confirmationDialog(confirmTitle, isPresented: Binding(get: { confirm != nil }, set: { if !$0 { confirm = nil } }), titleVisibility: .visible) {
            if let c = confirm {
                Button("Continue", role: .destructive) { run(c) }
            }
        } message: {
            Text(confirmMessage)
        }
    }

    private var confirmTitle: String {
        switch confirm?.opcode {
        case .resetMCU: "Restart the pack controller?"
        case .enterOTA: "Enter firmware update mode?"
        case .shipMode: "Put the pack in ship mode?"
        case .clearBonds: "Forget all paired phones?"
        default: ""
        }
    }

    private var confirmMessage: String {
        switch confirm?.opcode {
        case .resetMCU: "Ports and the gauge keep running. The app reconnects on its own."
        case .enterOTA: "The pack reboots into update mode and disconnects. Needs at least 20% charge and under 20 W output."
        case .shipMode: "Outputs turn off until a charger is plugged in or the button is pressed. Unplug all cables first."
        case .clearBonds: "Every phone, including this one, will have to pair again. Plug a cable into the pack to open pairing."
        default: ""
        }
    }

    private func run(_ command: Command) {
        Task {
            do {
                let r = try await store.run(command)
                result = "\(command.opcode): OK" + (r.detail != 0 ? " (\(r.detail))" : "")
            } catch {
                result = "\(command.opcode): \(error.localizedDescription)"
            }
        }
    }
}
