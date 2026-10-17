import Foundation
import MonolithKit

/// Enums with a display label; `Decoded` shows "Unknown (n)" for values this app predates (spec §1).
protocol Labeled { var label: String { get } }

extension ChargeStage: Labeled {}
extension LimitReason: Labeled {}
extension PortState: Labeled {}

extension PowerState: Labeled {
    var label: String {
        switch self {
        case .charging: "Charging"
        case .sourcing: "Powering devices"
        case .idle: "Idle"
        case .reset: "Resetting"
        case .passThrough: "Pass-through"
        case .ship: "Ship mode"
        }
    }
}

extension CommandResult: Labeled {
    var label: String {
        switch self {
        case .ok: "OK"
        case .unknownOpcode: "unknown command"
        case .badArg: "bad argument"
        case .refusedState: "not allowed right now"
        case .notBonded: "phone not paired"
        case .busy: "busy"
        }
    }
}

extension Decoded where E: Labeled {
    var label: String { value?.label ?? "Unknown (\(raw))" }
}

enum Fmt {
    static func watts(_ w: Double) -> String { w.formatted(.number.precision(.fractionLength(abs(w) < 10 ? 1 : 0))) + " W" }
    static func volts(_ v: Double) -> String { v.formatted(.number.precision(.fractionLength(2))) + " V" }
    static func amps(_ a: Double) -> String { a.formatted(.number.precision(.fractionLength(2))) + " A" }
    static func wh(_ wh: Double) -> String { wh.formatted(.number.precision(.fractionLength(1))) + " Wh" }
    static func celsius(_ c: Double) -> String { c.formatted(.number.precision(.fractionLength(1))) + " °C" }

    static func duration(minutes: UInt16) -> String {
        let h = Int(minutes) / 60, m = Int(minutes) % 60
        return h > 0 ? "\(h) h \(m) min" : "\(m) min"
    }

    static func contract(_ p: MonolithKit.Port) -> String? {
        guard p.contractMV > 0 else { return nil }
        let v = (Double(p.contractMV) / 1000).formatted(.number.precision(.fractionLength(0...1)))
        let a = (Double(p.contractMA) / 1000).formatted(.number.precision(.fractionLength(0...2)))
        return "\(v) V · \(a) A"
    }

    static func hex(_ data: Data) -> String { data.map { String(format: "%02X", $0) }.joined(separator: " ") }
}

extension TemperatureSlot {
    /// Which firmware throttle point (Gauge Health, spec §4.7) this sensor is compared against.
    func throttleDC(_ g: GaugeHealth) -> Int16 {
        if isCell { return g.throttleCellDC }
        if self == .connectors { return g.throttleConnDC }
        return g.throttleBoardDC
    }
}
