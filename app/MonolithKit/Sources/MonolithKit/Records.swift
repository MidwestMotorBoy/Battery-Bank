import Foundation

// Every record has `init?(data:)` (app side, tolerant of longer or shorter
// payloads per spec §1) and `encode()` (FakePack / firmware-reference side,
// always the full v1.0 length).

public struct ProtocolVersion: Equatable, Sendable {
    public var protoMajor: UInt8
    public var protoMinor: UInt8
    public var fwMajor: UInt8
    public var fwMinor: UInt8
    public var fwPatch: UInt8
    public var hwRev: UInt8
    public var fwBuild: UInt16

    public init(protoMajor: UInt8 = MonolithProtocol.major, protoMinor: UInt8 = MonolithProtocol.minor,
                fwMajor: UInt8 = 0, fwMinor: UInt8 = 1, fwPatch: UInt8 = 0, hwRev: UInt8 = 1, fwBuild: UInt16 = 0) {
        self.protoMajor = protoMajor; self.protoMinor = protoMinor
        self.fwMajor = fwMajor; self.fwMinor = fwMinor; self.fwPatch = fwPatch
        self.hwRev = hwRev; self.fwBuild = fwBuild
    }

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let a = r.u8(), let b = r.u8() else { return nil }
        protoMajor = a; protoMinor = b
        fwMajor = r.u8() ?? 0; fwMinor = r.u8() ?? 0; fwPatch = r.u8() ?? 0
        hwRev = r.u8() ?? 0; fwBuild = r.u16() ?? 0
    }

    public func encode() -> Data {
        var w = ByteWriter()
        w.u8(protoMajor); w.u8(protoMinor); w.u8(fwMajor); w.u8(fwMinor); w.u8(fwPatch); w.u8(hwRev); w.u16(fwBuild)
        return w.data
    }

    public var firmwareString: String { "\(fwMajor).\(fwMinor).\(fwPatch)" + (fwBuild != 0 ? "+\(fwBuild)" : "") }
    public var isSupported: Bool { protoMajor == MonolithProtocol.major }
}

public struct Status: Equatable, Sendable {
    public var socPct: UInt8 = 0
    public var chargeStage: Decoded<ChargeStage> = .known(.idle)
    public var limitReason: Decoded<LimitReason> = .known(.none)
    public var flags: StatusFlags = []
    public var packMV: UInt16 = 0
    public var packMA: Int16 = 0            // + into cells
    public var remainingDWh: UInt16 = 0     // 0.1 Wh
    public var timeToEmptyMin: UInt16? = nil
    public var timeToFullMin: UInt16? = nil
    public var cellMV: [UInt16] = [0, 0, 0, 0]
    public var chargeTargetMA: Int16 = 0
    public var outputDW: UInt16 = 0         // 0.1 W
    public var inputDW: UInt16 = 0
    public var powerState: Decoded<PowerState> = .known(.idle)
    public var sensorsOKBoard: UInt8 = 0
    public var uptimeS: UInt32 = 0

    public init() {}

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let soc = r.u8(), let stage = r.u8(), let reason = r.u8() else { return nil }
        socPct = soc
        chargeStage = Decoded(stage)
        limitReason = Decoded(reason)
        r.skip(1)
        flags = StatusFlags(rawValue: r.u16() ?? 0)
        packMV = r.u16() ?? 0
        packMA = r.s16() ?? 0
        remainingDWh = r.u16() ?? 0
        timeToEmptyMin = (r.u16() ?? Sentinel.u16NotAvailable).nonSentinel
        timeToFullMin = (r.u16() ?? Sentinel.u16NotAvailable).nonSentinel
        cellMV = (0..<4).map { _ in r.u16() ?? 0 }
        chargeTargetMA = r.s16() ?? 0
        outputDW = r.u16() ?? 0
        inputDW = r.u16() ?? 0
        powerState = Decoded(r.u8() ?? PowerState.idle.rawValue)
        sensorsOKBoard = r.u8() ?? 0
        uptimeS = r.u32() ?? 0
    }

    public func encode() -> Data {
        var w = ByteWriter()
        w.u8(socPct); w.u8(chargeStage.raw); w.u8(limitReason.raw); w.u8(0)
        w.u16(flags.rawValue); w.u16(packMV); w.s16(packMA); w.u16(remainingDWh)
        w.u16(timeToEmptyMin ?? Sentinel.u16NotAvailable)
        w.u16(timeToFullMin ?? Sentinel.u16NotAvailable)
        for i in 0..<4 { w.u16(i < cellMV.count ? cellMV[i] : 0) }
        w.s16(chargeTargetMA); w.u16(outputDW); w.u16(inputDW)
        w.u8(powerState.raw); w.u8(sensorsOKBoard); w.u32(uptimeS)
        return w.data
    }

    // Convenience, in SI units.
    public var packVolts: Double { Double(packMV) / 1000 }
    public var packAmps: Double { Double(packMA) / 1000 }
    public var packWatts: Double { packVolts * packAmps }
    public var remainingWh: Double { Double(remainingDWh) / 10 }
    public var outputWatts: Double { Double(outputDW) / 10 }
    public var inputWatts: Double { Double(inputDW) / 10 }
}

public struct Port: Equatable, Sendable {
    public var state: Decoded<PortState> = .known(.detached)
    public var flags: PortFlags = []
    public var contractMV: UInt16 = 0
    public var contractMA: UInt16 = 0
    public var powerDW: Int16 = 0           // + out of the pack

    public init() {}

    init?(reader r: inout ByteReader) {
        guard let s = r.u8() else { return nil }
        state = Decoded(s)
        flags = PortFlags(rawValue: r.u8() ?? 0)
        contractMV = r.u16() ?? 0
        contractMA = r.u16() ?? 0
        powerDW = r.s16() ?? 0
    }

    func encode(into w: inout ByteWriter) {
        w.u8(state.raw); w.u8(flags.rawValue); w.u16(contractMV); w.u16(contractMA); w.s16(powerDW)
    }

    public var contractWatts: Double { Double(contractMV) * Double(contractMA) / 1_000_000 }
    public var watts: Double { Double(powerDW) / 10 }
}

public struct Ports: Equatable, Sendable {
    public var usb1 = Port()
    public var usb2 = Port()

    public init() { usb1.flags.insert(.priority) }

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let p1 = Port(reader: &r) else { return nil }
        usb1 = p1
        usb2 = Port(reader: &r) ?? Port()
    }

    public func encode() -> Data {
        var w = ByteWriter()
        usb1.encode(into: &w); usb2.encode(into: &w)
        return w.data
    }
}

public struct Temperatures: Equatable, Sendable {
    /// Ten slots in `TemperatureSlot` order. nil = broken or absent; use `notFitted` to tell them apart.
    public var deciC: [Int16?] = Array(repeating: nil, count: TemperatureSlot.allCases.count)
    public var notFitted: Set<TemperatureSlot> = []
    public var faultMask: UInt16 = 0

    public init() {}

    public init?(data: Data) {
        var r = ByteReader(data)
        guard r.remaining >= 2 else { return nil }
        for slot in TemperatureSlot.allCases {
            guard let v = r.s16() else { break }
            switch v {
            case Sentinel.s16Invalid: deciC[slot.rawValue] = nil
            case Sentinel.s16NotFitted: deciC[slot.rawValue] = nil; notFitted.insert(slot)
            default: deciC[slot.rawValue] = v
            }
        }
        faultMask = r.u16() ?? 0
    }

    public func encode() -> Data {
        var w = ByteWriter()
        for slot in TemperatureSlot.allCases {
            if notFitted.contains(slot) { w.s16(Sentinel.s16NotFitted) }
            else { w.s16(deciC[slot.rawValue] ?? Sentinel.s16Invalid) }
        }
        w.u16(faultMask)
        return w.data
    }

    public func celsius(_ slot: TemperatureSlot) -> Double? { deciC[slot.rawValue].map { Double($0) / 10 } }
    public func isBroken(_ slot: TemperatureSlot) -> Bool { faultMask & (1 << UInt16(slot.rawValue)) != 0 }
}

public struct Settings: Equatable, Sendable {
    public var maxSOCPct: UInt8 = 95
    public var fastCharge: Bool = false
    public var usb2MinW: UInt8 = 20
    public var ledMode: UInt8 = 1
    public var autoFullChargeDays: UInt8 = 30

    public static let maxSOCRange: ClosedRange<UInt8> = 60...100
    public static let usb2MinWRange: ClosedRange<UInt8> = 10...30
    public static let maxSOCChoices: [UInt8] = [60, 70, 80, 90, 95, 100]

    public init() {}

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let m = r.u8() else { return nil }
        maxSOCPct = m
        fastCharge = (r.u8() ?? 0) != 0
        usb2MinW = r.u8() ?? 20
        ledMode = r.u8() ?? 1
        autoFullChargeDays = r.u8() ?? 30
    }

    /// Always 8 bytes with the reserved tail zeroed (whole-record writes, spec §4.5).
    public func encode() -> Data {
        var w = ByteWriter()
        w.u8(maxSOCPct); w.u8(fastCharge ? 1 : 0); w.u8(usb2MinW); w.u8(ledMode); w.u8(autoFullChargeDays)
        w.u8(0); w.u8(0); w.u8(0)
        return w.data
    }

    public var isValid: Bool {
        Self.maxSOCRange.contains(maxSOCPct) && Self.usb2MinWRange.contains(usb2MinW) && ledMode <= 2
    }
}

public struct Command: Equatable, Sendable {
    public var opcode: CommandOpcode
    public var args: [UInt8]

    public init(_ opcode: CommandOpcode, args: [UInt8] = []) { self.opcode = opcode; self.args = Array(args.prefix(3)) }

    public static let chargeTo100Once = Command(.chargeTo100Once)
    public static func tripMode(_ enable: Bool, hours: UInt8 = 48) -> Command { Command(.tripMode, args: [enable ? 1 : 0, hours]) }
    public static let clearBonds = Command(.clearBonds, args: [0xA5])
    public static let enterOTA = Command(.enterOTA, args: [0x5A])
    public static let shipMode = Command(.shipMode, args: [0x3C])
    public static let identify = Command(.identify)
    public static let resetMCU = Command(.resetMCU, args: [0x99])
    public static let openPairing = Command(.openPairing)
    public static let clearSensorFaults = Command(.clearSensorFaults)

    public func encode() -> Data { Data([opcode.rawValue] + args) }

    /// Firmware-side parse (used by FakePack).
    public init?(data: Data) {
        guard let first = data.first, let op = CommandOpcode(rawValue: first) else { return nil }
        opcode = op
        args = Array(data.dropFirst().prefix(3))
    }
}

public struct CommandResponse: Equatable, Sendable {
    public var opcode: UInt8
    public var result: Decoded<CommandResult>
    public var detail: UInt16

    public init(opcode: UInt8, result: CommandResult, detail: UInt16 = 0) {
        self.opcode = opcode; self.result = .known(result); self.detail = detail
    }

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let op = r.u8(), let res = r.u8() else { return nil }
        opcode = op; result = Decoded(res); detail = r.u16() ?? 0
    }

    public func encode() -> Data {
        var w = ByteWriter()
        w.u8(opcode); w.u8(result.raw); w.u16(detail)
        return w.data
    }
}

public struct GaugeHealth: Equatable, Sendable {
    public var fullChargeMAh: UInt16 = 5600
    public var designMAh: UInt16 = 5600
    public var cycleCount: UInt16 = 0
    public var sohPct: UInt8 = 100
    public var gaugeStatus: GaugeStatus = []
    public var cellDeltaMV: UInt16 = 0
    public var throttleCellDC: Int16 = 450
    public var throttleBoardDC: Int16 = 800
    public var throttleConnDC: Int16 = 650

    public init() {}

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let fcc = r.u16() else { return nil }
        fullChargeMAh = fcc
        designMAh = r.u16() ?? 5600
        cycleCount = r.u16() ?? 0
        sohPct = r.u8() ?? 0
        gaugeStatus = GaugeStatus(rawValue: r.u8() ?? 0)
        cellDeltaMV = r.u16() ?? 0
        throttleCellDC = r.s16() ?? 450
        throttleBoardDC = r.s16() ?? 800
        throttleConnDC = r.s16() ?? 650
    }

    public func encode() -> Data {
        var w = ByteWriter()
        w.u16(fullChargeMAh); w.u16(designMAh); w.u16(cycleCount); w.u8(sohPct); w.u8(gaugeStatus.rawValue)
        w.u16(cellDeltaMV); w.s16(throttleCellDC); w.s16(throttleBoardDC); w.s16(throttleConnDC)
        return w.data
    }
}

/// Pack Life (spec §4.9, added in 1.1): the BQ40Z50-R2 Lifetime Data blocks condensed into 48 bytes.
public struct PackLife: Equatable, Sendable {
    /// Temperature bands of the gauge's lifetime timers, coldest first (TRM SLUUBK0 ch. 10).
    public enum Band: Int, CaseIterable, Sendable { case ut = 0, lt, stl, rt, sth, ht, ot }

    public var manufactureDate: UInt16 = 0      // SBS ManufacturerDate() packing; 0 = not set
    public var runtime2h: UInt16 = 0
    public var bandTime2h: [UInt16] = Array(repeating: 0, count: Band.allCases.count)
    /// The gauge's T1, T2, T5, T6, T3, T4 in °C (ascending): band i spans thresholds[i-1]..thresholds[i].
    public var thresholdsC: [Int8] = [0, 12, 20, 25, 30, 55]
    public var cellMaxMV: UInt16 = 0
    public var cellMinMV: UInt16 = 0x7FFF
    public var maxDeltaCellMV: UInt16 = 0
    public var maxChargeMA: Int16 = 0
    public var maxDischargeMA: Int16 = 0        // ≤ 0
    public var maxTempCellC: Int8 = -128
    public var minTempCellC: Int8 = 127
    public var maxTempFETC: Int8 = -128
    public var shutdowns: UInt8 = 0
    public var fullCharges: UInt16 = 0
    public var safetyEvents: UInt16 = 0
    public var lastSafetyCycle: UInt16? = nil
    public var qmaxUpdates: UInt16 = 0
    public var maxBalanceTime2h: UInt8 = 0
    public var collecting: Bool = false

    public init() {}

    public init?(data: Data) {
        var r = ByteReader(data)
        guard let date = r.u16() else { return nil }
        manufactureDate = date
        runtime2h = r.u16() ?? 0
        bandTime2h = Band.allCases.map { _ in r.u16() ?? 0 }
        let defaults = thresholdsC
        thresholdsC = defaults.map { d in r.u8().map { Int8(bitPattern: $0) } ?? d }
        cellMaxMV = r.u16() ?? 0
        cellMinMV = r.u16() ?? 0x7FFF
        maxDeltaCellMV = r.u16() ?? 0
        maxChargeMA = r.s16() ?? 0
        maxDischargeMA = r.s16() ?? 0
        maxTempCellC = r.u8().map { Int8(bitPattern: $0) } ?? -128
        minTempCellC = r.u8().map { Int8(bitPattern: $0) } ?? 127
        maxTempFETC = r.u8().map { Int8(bitPattern: $0) } ?? -128
        shutdowns = r.u8() ?? 0
        fullCharges = r.u16() ?? 0
        safetyEvents = r.u16() ?? 0
        lastSafetyCycle = (r.u16() ?? Sentinel.u16NotAvailable).nonSentinel
        qmaxUpdates = r.u16() ?? 0
        maxBalanceTime2h = r.u8() ?? 0
        collecting = ((r.u8() ?? 0) & 1) != 0
    }

    public func encode() -> Data {
        var w = ByteWriter()
        w.u16(manufactureDate); w.u16(runtime2h)
        for i in 0..<Band.allCases.count { w.u16(i < bandTime2h.count ? bandTime2h[i] : 0) }
        for i in 0..<6 { w.u8(UInt8(bitPattern: i < thresholdsC.count ? thresholdsC[i] : 0)) }
        w.u16(cellMaxMV); w.u16(cellMinMV); w.u16(maxDeltaCellMV)
        w.s16(maxChargeMA); w.s16(maxDischargeMA)
        w.u8(UInt8(bitPattern: maxTempCellC)); w.u8(UInt8(bitPattern: minTempCellC)); w.u8(UInt8(bitPattern: maxTempFETC))
        w.u8(shutdowns); w.u16(fullCharges); w.u16(safetyEvents)
        w.u16(lastSafetyCycle ?? Sentinel.u16NotAvailable); w.u16(qmaxUpdates)
        w.u8(maxBalanceTime2h); w.u8(collecting ? 1 : 0)
        return w.data
    }

    // Convenience.
    public var runtimeHours: Int { Int(runtime2h) * 2 }
    public func hours(in band: Band) -> Int { Int(bandTime2h[band.rawValue]) * 2 }
    /// Lower and upper °C bound of a band (nil = open-ended).
    public func range(of band: Band) -> (Int?, Int?) {
        let i = band.rawValue
        return (i == 0 ? nil : Int(thresholdsC[i - 1]), i == thresholdsC.count ? nil : Int(thresholdsC[i]))
    }
    /// Gregorian date from ManufacturerDate(): day + month·32 + (year − 1980)·512.
    public var manufactured: DateComponents? {
        guard manufactureDate != 0 else { return nil }
        let day = Int(manufactureDate & 0x1F), month = Int((manufactureDate >> 5) & 0x0F), year = 1980 + Int(manufactureDate >> 9)
        guard (1...31).contains(day), (1...12).contains(month) else { return nil }
        return DateComponents(year: year, month: month, day: day)
    }
    public static func packDate(year: Int, month: Int, day: Int) -> UInt16 {
        UInt16(day + month * 32 + (year - 1980) * 512)
    }
    public var hasCellVoltageExtremes: Bool { cellMaxMV != 0 && cellMinMV != 0x7FFF }
    public var hasCellTempExtremes: Bool { maxTempCellC != -128 && minTempCellC != 127 }
}

private extension UInt16 {
    var nonSentinel: UInt16? { self == Sentinel.u16NotAvailable ? nil : self }
}
