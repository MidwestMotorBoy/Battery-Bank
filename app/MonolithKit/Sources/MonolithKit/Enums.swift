import Foundation

public enum ChargeStage: UInt8, CaseIterable, Sendable {
    case idle = 0, precharge, normal, fast, constantVoltage, hold, inhibited, fault
    public var label: String {
        switch self {
        case .idle: "Idle"
        case .precharge: "Precharge"
        case .normal: "Charging (0.5C)"
        case .fast: "Fast charging (1C)"
        case .constantVoltage: "Topping off"
        case .hold: "Holding"
        case .inhibited: "Charging paused"
        case .fault: "Fault"
        }
    }
}

public enum LimitReason: UInt8, CaseIterable, Sendable {
    case none = 0, sourceTooSmall, tooCold, tooHot, maxSOCReached, solarLimited,
         thermalThrottle, packFault, inputUndervoltage, sensorsDegraded, cableLimited
    public var label: String {
        switch self {
        case .none: "—"
        case .sourceTooSmall: "Charger too small"
        case .tooCold: "Too cold to charge"
        case .tooHot: "Too hot"
        case .maxSOCReached: "Charge limit reached"
        case .solarLimited: "Solar limited"
        case .thermalThrottle: "Thermal throttle (20 W)"
        case .packFault: "Pack fault"
        case .inputUndervoltage: "Weak source"
        case .sensorsDegraded: "Sensors degraded"
        case .cableLimited: "Cable limited to 3 A"
        }
    }
}

public enum PowerState: UInt8, CaseIterable, Sendable {
    case charging = 0, sourcing, idle, reset, passThrough, ship
}

public enum PortState: UInt8, CaseIterable, Sendable {
    case detached = 0, attached, sourcing, sinking, attachedNoPower, fault
    public var label: String {
        switch self {
        case .detached: "Empty"
        case .attached: "Connecting…"
        case .sourcing: "Powering"
        case .sinking: "Charging from"
        case .attachedNoPower: "Attached, no power"
        case .fault: "Fault"
        }
    }
}

public enum CommandResult: UInt8, CaseIterable, Sendable {
    case ok = 0, unknownOpcode, badArg, refusedState, notBonded, busy
}

/// Generic wrapper: a known case or the raw byte.
public enum Decoded<E: RawRepresentable & Sendable>: Sendable where E.RawValue == UInt8 {
    case known(E)
    case unknown(UInt8)

    public init(_ raw: UInt8) {
        if let e = E(rawValue: raw) { self = .known(e) } else { self = .unknown(raw) }
    }
    public var raw: UInt8 {
        switch self { case .known(let e): e.rawValue; case .unknown(let r): r }
    }
    public var value: E? {
        if case .known(let e) = self { return e } else { return nil }
    }
}

extension Decoded: Equatable where E: Equatable {}

public struct StatusFlags: OptionSet, Sendable {
    public let rawValue: UInt16
    public init(rawValue: UInt16) { self.rawValue = rawValue }
    public static let charging         = StatusFlags(rawValue: 1 << 0)
    public static let discharging      = StatusFlags(rawValue: 1 << 1)
    public static let throttle         = StatusFlags(rawValue: 1 << 2)
    public static let sensorsDegraded  = StatusFlags(rawValue: 1 << 3)
    public static let fastActive       = StatusFlags(rawValue: 1 << 4)
    public static let tripMode         = StatusFlags(rawValue: 1 << 5)
    public static let fullOncePending  = StatusFlags(rawValue: 1 << 6)
    public static let balancing        = StatusFlags(rawValue: 1 << 7)
    public static let gaugeFault       = StatusFlags(rawValue: 1 << 8)
    public static let pairingWindow    = StatusFlags(rawValue: 1 << 9)
    public static let hardShutdown     = StatusFlags(rawValue: 1 << 10)
    public static let passThrough      = StatusFlags(rawValue: 1 << 11)
    public static let solar            = StatusFlags(rawValue: 1 << 12)
    public static let lowSOC           = StatusFlags(rawValue: 1 << 13)
    public static let otaPending       = StatusFlags(rawValue: 1 << 14)
}

public struct PortFlags: OptionSet, Sendable {
    public let rawValue: UInt8
    public init(rawValue: UInt8) { self.rawValue = rawValue }
    public static let pdContract   = PortFlags(rawValue: 1 << 0)
    public static let emarked5A    = PortFlags(rawValue: 1 << 1)
    public static let solarSource  = PortFlags(rawValue: 1 << 2)
    public static let throttled    = PortFlags(rawValue: 1 << 3)
    public static let priority     = PortFlags(rawValue: 1 << 4)
    public static let loopDetected = PortFlags(rawValue: 1 << 5)
    public static let sourceOnly   = PortFlags(rawValue: 1 << 6)
    public static let overcurrent  = PortFlags(rawValue: 1 << 7)
}

public struct GaugeStatus: OptionSet, Sendable {
    public let rawValue: UInt8
    public init(rawValue: UInt8) { self.rawValue = rawValue }
    public static let chargeFETOff    = GaugeStatus(rawValue: 1 << 0)
    public static let dischargeFETOff = GaugeStatus(rawValue: 1 << 1)
    public static let overTemp        = GaugeStatus(rawValue: 1 << 2)
    public static let underTemp       = GaugeStatus(rawValue: 1 << 3)
    public static let cellOV          = GaugeStatus(rawValue: 1 << 4)
    public static let cellUV          = GaugeStatus(rawValue: 1 << 5)
    public static let overcurrent     = GaugeStatus(rawValue: 1 << 6)
    public static let notLearned      = GaugeStatus(rawValue: 1 << 7)
}

public enum CommandOpcode: UInt8, Sendable {
    case chargeTo100Once = 0x01
    case tripMode = 0x02
    case clearBonds = 0x03
    case enterOTA = 0x04
    case shipMode = 0x05
    case identify = 0x06
    case resetMCU = 0x07
    case openPairing = 0x08
    case clearSensorFaults = 0x09
}

/// Sensor order in the Temperatures characteristic (spec §4.4).
public enum TemperatureSlot: Int, CaseIterable, Sendable {
    case cell1 = 0, cell2, cell3, cell4, gaugeDie, usb1Stage, usb2Stage, connectors, heatsink, protectionFETs
    public var label: String {
        switch self {
        case .cell1: "Cell 1"
        case .cell2: "Cell 2"
        case .cell3: "Cell 3"
        case .cell4: "Cell 4"
        case .gaugeDie: "Gauge"
        case .usb1Stage: "USB1 converter"
        case .usb2Stage: "USB2 converter"
        case .connectors: "Connectors"
        case .heatsink: "Heatsink"
        case .protectionFETs: "Protection FETs"
        }
    }
    public var isCell: Bool { rawValue <= 3 }
    public var isBoard: Bool { rawValue >= 5 }
}
