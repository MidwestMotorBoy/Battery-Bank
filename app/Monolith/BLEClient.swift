import Foundation
import CoreBluetooth
import MonolithKit

/// CoreBluetooth central for the Monolith GATT (docs/app/ble-gatt-spec.md).
/// Connect → read Protocol Version → subscribe to Status, Ports, Temperatures, Command Result (spec §7).
/// The last pack is remembered and reconnected to automatically; a pending `connect` waits until
/// it's back in range.
@MainActor
final class BLEClient: NSObject {
    weak var store: PackStore?

    private var central: CBCentralManager!
    private var peripheral: CBPeripheral?
    private var seen: [UUID: CBPeripheral] = [:]
    private var characteristics: [CBUUID: CBCharacteristic] = [:]
    private var wantScan = false
    private var rediscoverTask: Task<Void, Never>?

    private var settingsWrite: CheckedContinuation<Void, Error>?
    private var pendingCommand: (opcode: UInt8, continuation: CheckedContinuation<CommandResponse, Error>)?

    /// These drop the link on purpose (spec §7); a disconnect while one is pending counts as success.
    private static let linkDroppingOpcodes = Set([CommandOpcode.clearBonds, .enterOTA, .resetMCU].map(\.rawValue))
    private static let commandTimeout: Duration = .seconds(2)
    private static let savedPackKey = "monolith.packID"
    private static let savedNameKey = "monolith.packName"

    override init() {
        super.init()
        central = CBCentralManager(delegate: self, queue: nil)
    }

    private var savedPackID: UUID? {
        get { UserDefaults.standard.string(forKey: Self.savedPackKey).flatMap(UUID.init) }
        set { UserDefaults.standard.set(newValue?.uuidString, forKey: Self.savedPackKey) }
    }

    // MARK: Control

    func startScan() {
        wantScan = true
        guard central.state == .poweredOn else { return }
        store?.setLink(.scanning)
        central.scanForPeripherals(withServices: [MonolithUUID.batteryService], options: nil)
    }

    func connect(id: UUID) {
        guard let p = seen[id] ?? central.retrievePeripherals(withIdentifiers: [id]).first else { return }
        wantScan = false
        central.stopScan()
        peripheral = p
        p.delegate = self
        store?.setLink(.connecting(p.name ?? MonolithUUID.localName))
        central.connect(p)
    }

    func disconnect() {
        wantScan = false
        if central.isScanning { central.stopScan() }
        if let p = peripheral { central.cancelPeripheralConnection(p) }
        peripheral = nil
        characteristics = [:]
    }

    /// Stop reconnecting to the remembered pack.
    func forget() {
        savedPackID = nil
        disconnect()
    }

    private func reconnectToSavedPack() -> Bool {
        guard let id = savedPackID, let p = central.retrievePeripherals(withIdentifiers: [id]).first else { return false }
        store?.setPackName(UserDefaults.standard.string(forKey: Self.savedNameKey) ?? MonolithUUID.localName)
        peripheral = p
        p.delegate = self
        store?.setLink(.connecting(p.name ?? MonolithUUID.localName))
        central.connect(p)
        return true
    }

    // MARK: Startup sequence

    private func didRead(_ version: ProtocolVersion, from p: CBPeripheral) {
        guard version.isSupported else {
            store?.setLink(.incompatible(version.protoMajor))
            return
        }
        savedPackID = p.identifier
        UserDefaults.standard.set(p.name, forKey: Self.savedNameKey)
        store?.setLink(.connected)
        for uuid in [MonolithUUID.status, MonolithUUID.ports, MonolithUUID.temperatures, MonolithUUID.commandResult] {
            if let c = characteristics[uuid] { p.setNotifyValue(true, for: c) }
        }
        for uuid in [MonolithUUID.status, MonolithUUID.ports, MonolithUUID.temperatures, MonolithUUID.settings, MonolithUUID.gaugeHealth, MonolithUUID.packLife] {
            if let c = characteristics[uuid] { p.readValue(for: c) }
        }
    }

    private func failPending(_ error: Error) {
        settingsWrite?.resume(throwing: error); settingsWrite = nil
        pendingCommand?.continuation.resume(throwing: error); pendingCommand = nil
    }

    private func log(_ line: String) { store?.appendDebug("BLE: " + line) }

    private var packName: String { peripheral?.name ?? MonolithUUID.localName }

    private func discover(_ p: CBPeripheral) {
        p.discoverServices([MonolithUUID.monolithService, MonolithUUID.batteryService])
    }

    /// The link is up but the Monolith service is gone (FakePack quit while the Mac kept its Continuity
    /// link, or firmware rebooting its GATT). Keep asking until it comes back.
    private func scheduleRediscovery(_ p: CBPeripheral) {
        rediscoverTask?.cancel()
        rediscoverTask = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(3))
            guard !Task.isCancelled, let self, p == self.peripheral, p.state == .connected else { return }
            self.discover(p)
        }
    }

    /// Called by the store's heartbeat watchdog: connected but no Status. Drop our connection and
    /// let the pending reconnect in didDisconnect bring it back with a fresh discovery.
    func recover() {
        guard let p = peripheral else { return }
        log("no Status for 15 s, reconnecting (state \(p.state.rawValue))")
        if p.state == .connected || p.state == .connecting {
            central.cancelPeripheralConnection(p)
        } else {
            central.connect(p)
        }
    }
}

// MARK: PackBackend

extension BLEClient: PackBackend {
    func write(_ settings: Settings) async throws {
        guard let p = peripheral, let c = characteristics[MonolithUUID.settings] else { throw PackError.notConnected }
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            settingsWrite?.resume(throwing: CancellationError())
            settingsWrite = cont
            p.writeValue(settings.encode(), for: c, type: .withResponse)   // iOS runs the pairing prompt if needed
        }
        p.readValue(for: c)
    }

    func send(_ command: Command) async throws -> CommandResponse {
        guard let p = peripheral, let c = characteristics[MonolithUUID.command] else { throw PackError.notConnected }
        let opcode = command.opcode.rawValue
        return try await withCheckedThrowingContinuation { (cont: CheckedContinuation<CommandResponse, Error>) in
            pendingCommand?.continuation.resume(throwing: CancellationError())
            pendingCommand = (opcode, cont)
            p.writeValue(command.encode(), for: c, type: .withResponse)
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: Self.commandTimeout)
                guard let self, let pending = self.pendingCommand, pending.opcode == opcode else { return }
                self.pendingCommand = nil
                pending.continuation.resume(throwing: PackError.noResult)
            }
        }
    }

    func setDebugLog(_ on: Bool) {
        guard let p = peripheral, let c = characteristics[MonolithUUID.debugLog] else { return }
        p.setNotifyValue(on, for: c)
    }
}

// MARK: CBCentralManagerDelegate (main queue)

extension BLEClient: CBCentralManagerDelegate {
    nonisolated func centralManagerDidUpdateState(_ central: CBCentralManager) {
        MainActor.assumeIsolated {
            if store?.isDemo == true { return }
            switch central.state {
            case .poweredOn:
                if !reconnectToSavedPack() && wantScan { startScan() }
            case .poweredOff: store?.setLink(.unavailable("Bluetooth is off."))
            case .unauthorized: store?.setLink(.unavailable("Bluetooth permission is off for Monolith (Settings › Monolith)."))
            case .unsupported: store?.setLink(.unavailable("Bluetooth isn't available on this device."))
            default: break
            }
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                                    advertisementData: [String: Any], rssi RSSI: NSNumber) {
        MainActor.assumeIsolated {
            // Spec §2: scan for 0x180F, then match the local name or the Monolith service UUID.
            let name = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? peripheral.name
            let services = (advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? [])
                + (advertisementData[CBAdvertisementDataOverflowServiceUUIDsKey] as? [CBUUID] ?? [])
            guard name == MonolithUUID.localName || name == "Mono" || services.contains(MonolithUUID.monolithService) else { return }
            seen[peripheral.identifier] = peripheral
            store?.found(DiscoveredPack(id: peripheral.identifier, name: name ?? MonolithUUID.localName, rssi: RSSI.intValue))
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        MainActor.assumeIsolated {
            log("connected")
            characteristics = [:]
            discover(peripheral)
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        MainActor.assumeIsolated {
            guard peripheral == self.peripheral else { return }
            log("connect failed: \(error?.localizedDescription ?? "unknown"), retrying")
            central.connect(peripheral)
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        MainActor.assumeIsolated {
            if let pending = pendingCommand, Self.linkDroppingOpcodes.contains(pending.opcode) {
                pendingCommand = nil
                pending.continuation.resume(returning: CommandResponse(opcode: pending.opcode, result: .ok))
            }
            failPending(PackError.notConnected)
            characteristics = [:]
            rediscoverTask?.cancel()
            guard peripheral == self.peripheral else { return }
            log("disconnected" + (error.map { ": \($0.localizedDescription)" } ?? "") + ", waiting to reconnect")
            // Keep the last values on screen (greyed) and wait for the pack to come back.
            store?.setLink(.connecting(peripheral.name ?? MonolithUUID.localName))
            central.connect(peripheral)
        }
    }
}

// MARK: CBPeripheralDelegate

extension BLEClient: CBPeripheralDelegate {
    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        MainActor.assumeIsolated {
            let services = peripheral.services ?? []
            guard services.contains(where: { $0.uuid == MonolithUUID.monolithService }) else {
                log("Monolith service not present yet, retrying")
                scheduleRediscovery(peripheral)
                return
            }
            for s in services { peripheral.discoverCharacteristics(nil, for: s) }
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didModifyServices invalidatedServices: [CBService]) {
        MainActor.assumeIsolated {
            guard peripheral == self.peripheral else { return }
            log("services changed: " + invalidatedServices.map(\.uuid.uuidString).joined(separator: ", "))
            for s in invalidatedServices { for c in s.characteristics ?? [] { characteristics[c.uuid] = nil } }
            if invalidatedServices.contains(where: { $0.uuid == MonolithUUID.monolithService }) {
                failPending(PackError.notConnected)
                store?.setLink(.connecting(packName))
            }
            discover(peripheral)
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        MainActor.assumeIsolated {
            for c in service.characteristics ?? [] { characteristics[c.uuid] = c }
            if service.uuid == MonolithUUID.monolithService, let v = characteristics[MonolithUUID.protocolVersion] {
                peripheral.readValue(for: v)
            }
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        MainActor.assumeIsolated {
            guard error == nil, let data = characteristic.value else { return }
            let uuid = characteristic.uuid
            if uuid == MonolithUUID.commandResult {
                guard let response = CommandResponse(data: data) else { return }
                if let pending = pendingCommand, pending.opcode == response.opcode {
                    pendingCommand = nil
                    pending.continuation.resume(returning: response)
                }
                return
            }
            store?.receive(uuid, data)
            if uuid == MonolithUUID.protocolVersion, let v = ProtocolVersion(data: data) { didRead(v, from: peripheral) }
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        MainActor.assumeIsolated {
            let mapped: Error? = error.map { e in
                let ns = e as NSError
                if ns.domain == CBATTErrorDomain && ns.code == 0x80 { return PackError.outOfRange }
                return PackError.attError(e.localizedDescription)
            }
            switch characteristic.uuid {
            case MonolithUUID.settings:
                if let mapped { settingsWrite?.resume(throwing: mapped) } else { settingsWrite?.resume() }
                settingsWrite = nil
            case MonolithUUID.command:
                if let mapped, let pending = pendingCommand {
                    pendingCommand = nil
                    pending.continuation.resume(throwing: mapped)
                }
            default: break
            }
        }
    }
}
