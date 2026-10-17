import Foundation
import CoreBluetooth
import MonolithKit

/// Where the bytes come from: the real pack over CoreBluetooth, or the in-process demo pack.
/// Both deliver raw characteristic values through `PackStore.receive`, so the demo exercises
/// the same decode path as the radio.
@MainActor
protocol PackBackend: AnyObject {
    /// Whole-record write (spec §4.5).
    func write(_ settings: Settings) async throws
    /// Resolves with the Command Result notification, or throws if none arrives (spec §4.6).
    func send(_ command: Command) async throws -> CommandResponse
    func setDebugLog(_ on: Bool)
    func disconnect()
}

enum LinkState: Equatable {
    case idle
    case unavailable(String)          // Bluetooth off, unauthorized, unsupported
    case scanning
    case connecting(String)           // includes "waiting for the bonded pack to come back in range"
    case connected
    case incompatible(UInt8)          // protocol major the app doesn't know
    case demo
}

struct DiscoveredPack: Identifiable, Equatable {
    let id: UUID
    var name: String
    var rssi: Int
}

enum PackError: LocalizedError {
    case notConnected
    case unparsedSettings
    case outOfRange
    case attError(String)
    case noResult
    case refused(Decoded<CommandResult>, UInt16)

    var errorDescription: String? {
        switch self {
        case .notConnected: "Not connected to a pack."
        case .unparsedSettings: "The pack's settings couldn't be read, so they weren't changed."
        case .outOfRange: "The pack rejected a value as out of range. Nothing was changed."
        case .attError(let s): s
        case .noResult: "The pack didn't confirm the command. It may not have run."
        case .refused(let r, let d): "Refused: \(r.label)" + (d != 0 ? " (detail \(d))" : "")
        }
    }
}

@MainActor
final class PackStore: ObservableObject {
    @Published private(set) var link: LinkState = .idle
    @Published private(set) var discovered: [DiscoveredPack] = []
    @Published private(set) var packName = MonolithUUID.localName

    @Published private(set) var version: ProtocolVersion?
    @Published private(set) var status: Status?
    @Published private(set) var ports: Ports?
    @Published private(set) var temperatures: Temperatures?
    @Published private(set) var settings: Settings?
    @Published private(set) var gauge: GaugeHealth?
    @Published private(set) var life: PackLife?
    @Published private(set) var lastUpdate: Date?
    @Published private(set) var raw: [CBUUID: Data] = [:]
    @Published private(set) var debugLines: [String] = []
    /// Connected, but no Status for longer than the spec's 10 s heartbeat allows (§4.2): the pack
    /// or its radio has hung without the link dropping. Treated like being out of range.
    @Published private(set) var silent = false

    private static let heartbeatTimeout: TimeInterval = 15
    private var lastStatusAt: Date?
    private var watchdog: Timer?

    let ble = BLEClient()
    private var demo: DemoPack?

    init() {
        ble.store = self
        watchdog = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.checkHeartbeat() }
        }
        #if targetEnvironment(simulator)
        startDemo()   // no Bluetooth in the Simulator
        #endif
    }

    /// Live values are flowing; otherwise the UI greys the last known values.
    var isLive: Bool { (link == .connected && !silent) || link == .demo }
    var hasPack: Bool { version != nil }
    var isDemo: Bool { demo != nil }
    private var backend: PackBackend? { demo ?? (link == .connected ? ble : nil) }

    // MARK: Actions

    func startScan() {
        demo = nil
        discovered = []
        ble.startScan()
    }

    func connect(_ pack: DiscoveredPack) {
        packName = pack.name
        ble.connect(id: pack.id)
    }

    func startDemo() {
        ble.disconnect()
        clear()
        packName = "Demo pack"
        demo = DemoPack(store: self)
        link = .demo
    }

    /// Forgets the pack (stops auto-reconnect) and returns to the connect screen.
    func forget() {
        demo?.disconnect()
        demo = nil
        ble.forget()
        clear()
        link = .idle
    }

    func save(_ new: Settings) async throws {
        guard let backend else { throw PackError.notConnected }
        guard settings != nil else { throw PackError.unparsedSettings }
        guard new.isValid else { throw PackError.outOfRange }
        try await backend.write(new)
    }

    @discardableResult
    func run(_ command: Command) async throws -> CommandResponse {
        guard let backend else { throw PackError.notConnected }
        let response = try await backend.send(command)
        guard response.result == .known(.ok) else { throw PackError.refused(response.result, response.detail) }
        return response
    }

    func setDebugLog(_ on: Bool) { backend?.setDebugLog(on) }

    // MARK: Fed by backends

    func setLink(_ state: LinkState) {
        if state == .connected && link != .connected { lastStatusAt = Date() }   // start the heartbeat clock
        link = state
        checkHeartbeat()
    }

    private func checkHeartbeat() {
        let late = lastStatusAt.map { Date().timeIntervalSince($0) > Self.heartbeatTimeout } ?? false
        let now = link == .connected && late
        if now != silent { silent = now }
    }
    func setPackName(_ name: String) { packName = name }

    func found(_ pack: DiscoveredPack) {
        if let i = discovered.firstIndex(where: { $0.id == pack.id }) { discovered[i] = pack }
        else { discovered.append(pack) }
    }

    /// One characteristic value. Unparseable values are kept in `raw` but don't replace good data.
    func receive(_ uuid: CBUUID, _ data: Data) {
        raw[uuid] = data
        switch uuid {
        case MonolithUUID.protocolVersion: version = ProtocolVersion(data: data) ?? version
        case MonolithUUID.status:
            if let v = Status(data: data) { status = v; lastUpdate = Date(); lastStatusAt = lastUpdate; checkHeartbeat() }
        case MonolithUUID.ports: if let v = Ports(data: data) { ports = v; lastUpdate = Date() }
        case MonolithUUID.temperatures: if let v = Temperatures(data: data) { temperatures = v; lastUpdate = Date() }
        case MonolithUUID.settings: settings = Settings(data: data)
        case MonolithUUID.gaugeHealth: gauge = GaugeHealth(data: data) ?? gauge
        case MonolithUUID.packLife: life = PackLife(data: data) ?? life
        case MonolithUUID.debugLog: appendDebug(String(decoding: data, as: UTF8.self))
        default: break
        }
    }

    func appendDebug(_ line: String) {
        let t = Date().formatted(date: .omitted, time: .standard)
        debugLines.append("\(t)  \(line)")
        if debugLines.count > 300 { debugLines.removeFirst(debugLines.count - 300) }
    }

    private func clear() {
        version = nil; status = nil; ports = nil; temperatures = nil
        settings = nil; gauge = nil; life = nil; lastUpdate = nil; lastStatusAt = nil; silent = false; raw = [:]; debugLines = []
    }
}
