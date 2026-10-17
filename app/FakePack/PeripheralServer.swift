import Foundation
import CoreBluetooth
import Combine
import MonolithKit

/// Advertises the Monolith GATT (docs/app/ble-gatt-spec.md) from the Mac's
/// Bluetooth radio and serves it from a `PackModel`.
@MainActor
final class PeripheralServer: NSObject, ObservableObject {
    @Published private(set) var stateText = "Starting…"
    @Published private(set) var advertising = false
    @Published private(set) var subscribers: [String: Int] = [:]   // characteristic name → count

    private let model: PackModel
    private var manager: CBPeripheralManager!
    private var timer: AnyCancellable?

    // Characteristics we notify on.
    private var batteryLevel: CBMutableCharacteristic!
    private var status: CBMutableCharacteristic!
    private var ports: CBMutableCharacteristic!
    private var temperatures: CBMutableCharacteristic!
    private var commandResult: CBMutableCharacteristic!
    private var debugLog: CBMutableCharacteristic!

    private var lastStatus = Data(), lastPorts = Data(), lastTemps = Data()
    private var lastStatusSent = Date.distantPast, lastTempsSent = Date.distantPast
    private var pending: [(CBMutableCharacteristic, Data)] = []

    init(model: PackModel) {
        self.model = model
        super.init()
        manager = CBPeripheralManager(delegate: self, queue: nil)
        timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect().sink { [weak self] _ in
            guard let self else { return }
            self.model.tick()
            self.pushUpdates(force: false)
        }
    }

    // MARK: GATT table

    private func buildServices() {
        func ch(_ uuid: CBUUID, _ props: CBCharacteristicProperties, _ perms: CBAttributePermissions, value: Data? = nil) -> CBMutableCharacteristic {
            CBMutableCharacteristic(type: uuid, properties: props, value: value, permissions: perms)
        }
        // Battery Service
        batteryLevel = ch(MonolithUUID.batteryLevel, [.read, .notify], .readable)
        let battery = CBMutableService(type: MonolithUUID.batteryService, primary: true)
        battery.characteristics = [batteryLevel]

        // Device Information (static values are cached by CoreBluetooth when `value` is set)
        let dis = CBMutableService(type: MonolithUUID.deviceInfoService, primary: true)
        dis.characteristics = [
            ch(MonolithUUID.manufacturerName, .read, .readable, value: Data(MonolithUUID.manufacturerNameValue.utf8)),
            ch(MonolithUUID.modelNumber, .read, .readable, value: Data("FAKEPACK-MAC".utf8)),
            ch(MonolithUUID.firmwareRevision, .read, .readable, value: Data(model.version.firmwareString.utf8)),
            ch(MonolithUUID.hardwareRevision, .read, .readable, value: Data("fakepack".utf8)),
            ch(MonolithUUID.serialNumber, .read, .readable, value: Data("FP-0001".utf8)),
        ]

        // Monolith service. Settings/Command require an encrypted (bonded) link, as the spec says.
        let protoVersion = ch(MonolithUUID.protocolVersion, .read, .readable, value: model.version.encode())
        status = ch(MonolithUUID.status, [.read, .notify], .readable)
        ports = ch(MonolithUUID.ports, [.read, .notify], .readable)
        temperatures = ch(MonolithUUID.temperatures, [.read, .notify], .readable)
        let settings = ch(MonolithUUID.settings, [.read, .write], [.readable, .writeEncryptionRequired])
        let command = ch(MonolithUUID.command, [.write], .writeEncryptionRequired)
        commandResult = ch(MonolithUUID.commandResult, [.notify], .readable)
        let gaugeHealth = ch(MonolithUUID.gaugeHealth, .read, .readable)
        let packLife = ch(MonolithUUID.packLife, .read, .readable)
        debugLog = ch(MonolithUUID.debugLog, [.notify], .readable)
        let monolith = CBMutableService(type: MonolithUUID.monolithService, primary: true)
        monolith.characteristics = [protoVersion, status, ports, temperatures, settings, command, commandResult, gaugeHealth, packLife, debugLog]

        manager.add(battery)
        manager.add(dis)
        manager.add(monolith)
    }

    func startAdvertising() {
        guard manager.state == .poweredOn else { return }
        manager.startAdvertising([
            CBAdvertisementDataLocalNameKey: MonolithUUID.localName,
            CBAdvertisementDataServiceUUIDsKey: [MonolithUUID.batteryService, MonolithUUID.monolithService],
        ])
    }

    func stopAdvertising() { manager.stopAdvertising(); advertising = false }

    // MARK: Notifications

    /// Spec §4.2–4.4: Status ≤ 1/s and ≥ every 10 s; Ports on change; Temperatures ≤ every 5 s attached / 60 s idle.
    func pushUpdates(force: Bool) {
        let now = Date()
        let s = model.statusRecord().encode()
        if force || (s != lastStatus && now.timeIntervalSince(lastStatusSent) >= 1) || now.timeIntervalSince(lastStatusSent) >= 10 {
            lastStatus = s; lastStatusSent = now
            send(status, s)
            send(batteryLevel, Data([s[0]]))
        }
        let p = model.portsRecord().encode()
        if force || p != lastPorts {
            lastPorts = p
            send(ports, p)
        }
        let t = model.temperaturesRecord().encode()
        let tempsPeriod: TimeInterval = model.powerState == .idle ? 60 : 5
        let faultChanged = t.suffix(2) != lastTemps.suffix(2)
        if force || faultChanged || (t != lastTemps && now.timeIntervalSince(lastTempsSent) >= tempsPeriod) {
            lastTemps = t; lastTempsSent = now
            send(temperatures, t)
        }
    }

    func sendDebug(_ line: String) {
        send(debugLog, Data(line.utf8.prefix(48)))
    }

    private func send(_ c: CBMutableCharacteristic, _ data: Data) {
        guard manager.state == .poweredOn, (c.subscribedCentrals?.isEmpty == false) else { return }
        if !manager.updateValue(data, for: c, onSubscribedCentrals: nil) {
            pending.append((c, data))   // retried in peripheralManagerIsReady
        }
    }

    private func refreshSubscribers() {
        subscribers = [
            "Battery Level": batteryLevel.subscribedCentrals?.count ?? 0,
            "Status": status.subscribedCentrals?.count ?? 0,
            "Ports": ports.subscribedCentrals?.count ?? 0,
            "Temperatures": temperatures.subscribedCentrals?.count ?? 0,
            "Command Result": commandResult.subscribedCentrals?.count ?? 0,
            "Debug Log": debugLog.subscribedCentrals?.count ?? 0,
        ].filter { $0.value > 0 }
    }
}

extension PeripheralServer: CBPeripheralManagerDelegate {
    nonisolated func peripheralManagerDidUpdateState(_ peripheral: CBPeripheralManager) {
        Task { @MainActor in
            switch peripheral.state {
            case .poweredOn:
                stateText = "Bluetooth on"
                buildServices()
                startAdvertising()
            case .unauthorized: stateText = "Bluetooth permission denied (System Settings > Privacy > Bluetooth)"
            case .poweredOff: stateText = "Bluetooth is off"
            case .unsupported: stateText = "No BLE radio"
            default: stateText = "Bluetooth state \(peripheral.state.rawValue)"
            }
        }
    }

    nonisolated func peripheralManagerDidStartAdvertising(_ peripheral: CBPeripheralManager, error: Error?) {
        Task { @MainActor in
            advertising = error == nil
            if let error { model.logLine("Advertising failed: \(error.localizedDescription)") }
            else { model.logLine("Advertising as \(MonolithUUID.localName)") }
        }
    }

    nonisolated func peripheralManager(_ peripheral: CBPeripheralManager, didReceiveRead request: CBATTRequest) {
        Task { @MainActor in
            let data: Data?
            switch request.characteristic.uuid {
            case MonolithUUID.batteryLevel: data = Data([UInt8(model.socPct.rounded())])
            case MonolithUUID.status: data = model.statusRecord().encode()
            case MonolithUUID.ports: data = model.portsRecord().encode()
            case MonolithUUID.temperatures: data = model.temperaturesRecord().encode()
            case MonolithUUID.settings: data = model.settings.encode()
            case MonolithUUID.gaugeHealth: data = model.gaugeHealthRecord().encode()
            case MonolithUUID.packLife: data = model.packLifeRecord().encode()
            default: data = nil
            }
            guard let data else { peripheral.respond(to: request, withResult: .readNotPermitted); return }
            if request.offset > data.count { peripheral.respond(to: request, withResult: .invalidOffset); return }
            request.value = data.subdata(in: request.offset..<data.count)
            peripheral.respond(to: request, withResult: .success)
        }
    }

    nonisolated func peripheralManager(_ peripheral: CBPeripheralManager, didReceiveWrite requests: [CBATTRequest]) {
        Task { @MainActor in
            for request in requests {
                guard let value = request.value else { peripheral.respond(to: request, withResult: .invalidAttributeValueLength); continue }
                switch request.characteristic.uuid {
                case MonolithUUID.settings:
                    if let why = model.apply(settingsData: value) {
                        model.logLine("Settings write rejected: \(why) \(value.map { String(format: "%02X", $0) }.joined(separator: " "))")
                        // 0x80 = application error "value out of range" (spec §4.5)
                        peripheral.respond(to: request, withResult: CBATTError.Code(rawValue: 0x80) ?? .unlikelyError)
                    } else {
                        peripheral.respond(to: request, withResult: .success)
                    }
                case MonolithUUID.command:
                    guard let cmd = Command(data: value) else {
                        model.logLine("Unknown command \(value.map { String(format: "%02X", $0) }.joined(separator: " "))")
                        peripheral.respond(to: request, withResult: .success)
                        send(commandResult, CommandResponse(opcode: value.first ?? 0, result: .unknownOpcode).encode())
                        continue
                    }
                    peripheral.respond(to: request, withResult: .success)
                    let response = model.apply(command: cmd)
                    send(commandResult, response.encode())
                    pushUpdates(force: true)
                default:
                    peripheral.respond(to: request, withResult: .writeNotPermitted)
                }
            }
        }
    }

    nonisolated func peripheralManager(_ peripheral: CBPeripheralManager, central: CBCentral, didSubscribeTo characteristic: CBCharacteristic) {
        Task { @MainActor in
            model.logLine("Subscribed: \(characteristic.uuid) (MTU \(central.maximumUpdateValueLength))")
            refreshSubscribers()
            pushUpdates(force: true)
        }
    }

    nonisolated func peripheralManager(_ peripheral: CBPeripheralManager, central: CBCentral, didUnsubscribeFrom characteristic: CBCharacteristic) {
        Task { @MainActor in
            model.logLine("Unsubscribed: \(characteristic.uuid)")
            refreshSubscribers()
        }
    }

    nonisolated func peripheralManagerIsReady(toUpdateSubscribers peripheral: CBPeripheralManager) {
        Task { @MainActor in
            let queue = pending; pending.removeAll()
            for (c, d) in queue { send(c, d) }
        }
    }
}
