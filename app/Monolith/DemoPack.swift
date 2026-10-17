import Foundation
import MonolithKit

/// FakePack's simulated pack (`FakePack/PackModel.swift`), run inside the app for the iOS Simulator
/// and for trying the app without hardware. Records are encoded and fed through `PackStore.receive`
/// exactly as notifications from the radio would be.
@MainActor
final class DemoPack: PackBackend {
    private let model = PackModel()
    private weak var store: PackStore?
    private var timer: Timer?
    private var debugOn = false
    private var loggedCount = 0

    init(store: PackStore) {
        self.store = store
        // A 60 W charger on USB1 and a phone on USB2: pass-through, so most of the UI has something to show.
        model.socPct = 62
        model.usb1.state = .known(.sinking)
        model.usb1.flags = [.priority, .pdContract]
        model.usb1.contractMV = 20_000; model.usb1.contractMA = 3_000; model.usb1.powerDW = -600
        model.usb2.state = .known(.sourcing)
        model.usb2.flags = [.pdContract]
        model.usb2.contractMV = 9_000; model.usb2.contractMA = 2_000; model.usb2.powerDW = 150

        store.receive(MonolithUUID.protocolVersion, model.version.encode())
        store.receive(MonolithUUID.settings, model.settings.encode())
        publish()
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tick() }
        }
    }

    private func tick() {
        model.tick()
        publish()
    }

    private func publish() {
        guard let store else { return }
        store.receive(MonolithUUID.status, model.statusRecord().encode())
        store.receive(MonolithUUID.ports, model.portsRecord().encode())
        store.receive(MonolithUUID.temperatures, model.temperaturesRecord().encode())
        store.receive(MonolithUUID.gaugeHealth, model.gaugeHealthRecord().encode())
        if model.uptimeS % 60 == 0 { store.receive(MonolithUUID.packLife, model.packLifeRecord().encode()) }
        if debugOn {
            for line in model.log.dropFirst(loggedCount) { store.receive(MonolithUUID.debugLog, Data(line.utf8.prefix(48))) }
        }
        loggedCount = model.log.count
    }

    func write(_ settings: Settings) async throws {
        if model.apply(settingsData: settings.encode()) != nil { throw PackError.outOfRange }
        store?.receive(MonolithUUID.settings, model.settings.encode())
        publish()
    }

    func send(_ command: Command) async throws -> CommandResponse {
        let response = model.apply(command: command)
        publish()
        return response
    }

    func setDebugLog(_ on: Bool) { debugOn = on }

    func disconnect() {
        timer?.invalidate()
        timer = nil
    }
}
