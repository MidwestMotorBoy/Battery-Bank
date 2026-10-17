import SwiftUI
import MonolithKit

/// Stored settings (spec §4.5) plus the two expiring charge commands (§4.6).
/// Edits a draft of the record the pack sent; Save writes the whole record back.
struct SettingsView: View {
    @EnvironmentObject private var store: PackStore
    @State private var draft: Settings?
    @State private var saving = false
    @State private var message: String?

    private var dirty: Bool { draft != nil && draft != store.settings }
    private var flags: StatusFlags { store.status?.flags ?? [] }

    var body: some View {
        NavigationStack {
            Form {
                if let binding = Binding($draft) {
                    Section {
                        Picker("Charge limit", selection: binding.maxSOCPct) {
                            ForEach(Settings.maxSOCChoices, id: \.self) { Text("\($0)%").tag($0) }
                        }
                        Toggle("Fast charge", isOn: binding.fastCharge)
                    } header: {
                        Text("Charging")
                    } footer: {
                        Text("Stopping below 100% makes the cells last longer. Fast charge uses 1C between 20 and 80% when the charger and temperatures allow.")
                    }
                    Section {
                        Stepper("USB-C 2 minimum: \(binding.wrappedValue.usb2MinW) W", value: binding.usb2MinW, in: Settings.usb2MinWRange, step: 5)
                        Picker("Balancing charge", selection: binding.autoFullChargeDays) {
                            Text("Never").tag(UInt8(0))
                            ForEach([7, 14, 30, 60, 90] as [UInt8], id: \.self) { Text("Every \($0) days").tag($0) }
                            if ![0, 7, 14, 30, 60, 90].contains(binding.wrappedValue.autoFullChargeDays) {
                                Text("Every \(binding.wrappedValue.autoFullChargeDays) days").tag(binding.wrappedValue.autoFullChargeDays)
                            }
                        }
                        Picker("LED", selection: binding.ledMode) {
                            Text("Off").tag(UInt8(0)); Text("Normal").tag(UInt8(1)); Text("Dim").tag(UInt8(2))
                        }
                    } header: {
                        Text("Pack")
                    } footer: {
                        Text("USB-C 2 keeps at least this much power when both ports are in use.")
                    }
                    Section {
                        Button(saving ? "Saving…" : "Save to pack") { save() }
                            .disabled(!dirty || saving || !store.isLive)
                        if dirty { Button("Discard changes", role: .destructive) { draft = store.settings } }
                    } footer: {
                        if let message { Text(message) }
                    }
                } else {
                    Text("The pack's settings couldn't be read, so they can't be changed.")
                        .foregroundStyle(.secondary)
                }

                Section {
                    Toggle("Trip mode (48 h)", isOn: Binding(
                        get: { flags.contains(.tripMode) },
                        set: { on in run(.tripMode(on), done: on ? "Trip mode on: charges to 100% for 48 hours." : "Trip mode off.") }
                    ))
                    Button(flags.contains(.fullOncePending) ? "Full charge armed" : "Charge to 100% once") {
                        run(.chargeTo100Once, done: "The next charge goes to 100%, then the limit applies again.")
                    }
                    .disabled(flags.contains(.fullOncePending))
                } header: {
                    Text("Before a trip")
                } footer: {
                    Text("These expire on their own and don't change your charge limit.")
                }
                .disabled(!store.isLive)

                Section {
                    NavigationLink { DeveloperView() } label: { Label("Developer", systemImage: "hammer") }
                } footer: {
                    Text("Firmware info, raw values, the debug log and maintenance commands.")
                }
            }
            .staleWhenOffline()
            .navigationTitle("Settings")
            .packToolbar()
            .onAppear { if draft == nil { draft = store.settings } }
            .onChange(of: store.settings) { old, new in
                // Follow the pack unless the user has unsaved edits.
                if draft == nil || draft == old { draft = new }
            }
        }
    }

    private func save() {
        guard let draft else { return }
        saving = true
        Task {
            defer { saving = false }
            do { try await store.save(draft); message = "Saved." }
            catch { message = error.localizedDescription }
        }
    }

    private func run(_ command: Command, done: String) {
        Task {
            do { try await store.run(command); message = done }
            catch { message = error.localizedDescription }
        }
    }
}
