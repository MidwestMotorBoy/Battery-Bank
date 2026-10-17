import Foundation
import Combine
import MonolithKit

/// The simulated pack. Everything the GATT exposes comes from here; the UI
/// edits it, `PeripheralServer` serialises it. A 1 Hz tick makes SOC, energy
/// and timers move so the app's "live" paths get exercised.
@MainActor
final class PackModel: ObservableObject {
    // MARK: Pack-level state
    @Published var socPct: Double = 73
    @Published var chargeStage: ChargeStage = .idle
    @Published var limitReason: LimitReason = .none
    @Published var flags: StatusFlags = []
    @Published var cycleCount: UInt16 = 12
    @Published var fullChargeMAh: UInt16 = 5540
    @Published var sohPct: UInt8 = 98
    @Published var cellDeltaMV: UInt16 = 8
    @Published var gaugeStatus: GaugeStatus = []
    @Published var simulate: Bool = true         // let SOC/energy move with current
    @Published var uptimeS: UInt32 = 0
    @Published var pairingWindowOpen: Bool = false

    // MARK: Ports
    @Published var usb1 = Port()
    @Published var usb2 = Port()

    // MARK: Temperatures (°C). nil = broken. notFitted hides the slot.
    @Published var tempC: [Double?] = [23.5, 23.4, 23.8, 23.6, 24.0, 31.0, 28.0, 25.5, nil, nil]
    @Published var notFitted: Set<TemperatureSlot> = [.heatsink, .protectionFETs]
    @Published var broken: Set<TemperatureSlot> = []

    // MARK: Settings and commands (written by the phone)
    @Published var settings = Settings()
    @Published var fullOncePending = false
    @Published var tripModeHoursLeft: Int = 0
    @Published var log: [String] = []

    let version = ProtocolVersion(fwMajor: 0, fwMinor: 1, fwPatch: 0, hwRev: 1, fwBuild: 1)
    let throttle = GaugeHealth()

    init() {
        usb1.flags.insert(.priority)
    }

    // MARK: Derived
    var designWh: Double { 82.0 }
    var packMV: UInt16 {
        // Simple OCV curve for 4S NMC: 3.0 V at 0 % to 4.2 V at 100 %, flat in the middle.
        let s = socPct / 100
        let v = 3.0 + 1.2 * (0.15 + 0.7 * s + 0.15 * s * s * s)
        return UInt16(min(16_800, max(12_000, v * 4 * 1000)))
    }
    var cellMV: [UInt16] {
        let base = Int(packMV) / 4
        return [base + 2, base - 1, base + 3, base - 4].map { UInt16(max(2_500, min(4_250, $0))) }
    }
    /// + into the cells.
    var packMA: Int16 {
        let outW = Double(usb1.powerDW + usb2.powerDW) / 10   // + out of the pack
        let v = Double(packMV) / 1000
        return Int16(clamping: Int((-outW / v) * 1000))
    }
    var remainingDWh: UInt16 { UInt16(designWh * Double(fullChargeMAh) / 5600 * socPct / 100 * 10) }
    var outputDW: UInt16 { UInt16(max(0, Int(usb1.powerDW)) + max(0, Int(usb2.powerDW))) }
    var inputDW: UInt16 { UInt16(max(0, -Int(usb1.powerDW)) + max(0, -Int(usb2.powerDW))) }

    var sensorsOKBoard: UInt8 {
        UInt8(TemperatureSlot.allCases.filter { $0.isBoard && !notFitted.contains($0) && !broken.contains($0) }.count)
    }

    var powerState: PowerState {
        let sinking = [usb1, usb2].contains { $0.state.value == .sinking }
        let sourcing = [usb1, usb2].contains { $0.state.value == .sourcing }
        switch (sinking, sourcing) {
        case (true, true): return .passThrough
        case (true, false): return .charging
        case (false, true): return .sourcing
        default: return .idle
        }
    }

    // MARK: Records for the GATT
    func statusRecord() -> Status {
        var s = Status()
        s.socPct = UInt8(socPct.rounded())
        s.chargeStage = .known(chargeStage)
        s.limitReason = .known(limitReason)
        var f = flags
        if packMA > 50 { f.insert(.charging) } else { f.remove(.charging) }
        if packMA < -50 { f.insert(.discharging) } else { f.remove(.discharging) }
        if sensorsOKBoard < 3 { f.insert(.sensorsDegraded) } else { f.remove(.sensorsDegraded) }
        if settings.fastCharge && chargeStage == .fast { f.insert(.fastActive) } else { f.remove(.fastActive) }
        if tripModeHoursLeft > 0 { f.insert(.tripMode) } else { f.remove(.tripMode) }
        if fullOncePending { f.insert(.fullOncePending) } else { f.remove(.fullOncePending) }
        if pairingWindowOpen { f.insert(.pairingWindow) } else { f.remove(.pairingWindow) }
        if powerState == .passThrough { f.insert(.passThrough) } else { f.remove(.passThrough) }
        if socPct <= 10 { f.insert(.lowSOC) } else { f.remove(.lowSOC) }
        if [usb1, usb2].contains(where: { $0.flags.contains(.solarSource) }) { f.insert(.solar) } else { f.remove(.solar) }
        s.flags = f
        s.packMV = packMV
        s.packMA = packMA
        s.remainingDWh = remainingDWh
        let w = Double(packMV) / 1000 * Double(packMA) / 1000
        if w < -0.5 {
            s.timeToEmptyMin = UInt16(min(65_534, Double(remainingDWh) / 10 / -w * 60))
        }
        if w > 0.5 {
            let missing = designWh * Double(fullChargeMAh) / 5600 * (Double(settings.maxSOCPct) - socPct) / 100
            s.timeToFullMin = UInt16(min(65_534, max(0, missing) / w * 60))
        }
        s.cellMV = cellMV
        s.chargeTargetMA = chargeStage == .idle ? 0 : (chargeStage == .fast ? 5600 : 2800)
        s.outputDW = outputDW
        s.inputDW = inputDW
        s.powerState = .known(powerState)
        s.sensorsOKBoard = sensorsOKBoard
        s.uptimeS = uptimeS
        return s
    }

    func portsRecord() -> Ports {
        var p = Ports()
        p.usb1 = usb1; p.usb2 = usb2
        p.usb1.flags.insert(.priority)
        return p
    }

    func temperaturesRecord() -> Temperatures {
        var t = Temperatures()
        t.notFitted = notFitted
        for slot in TemperatureSlot.allCases {
            if broken.contains(slot) {
                t.deciC[slot.rawValue] = nil
                t.faultMask |= 1 << UInt16(slot.rawValue)
            } else {
                t.deciC[slot.rawValue] = tempC[slot.rawValue].map { Int16($0 * 10) }
            }
        }
        return t
    }

    func gaugeHealthRecord() -> GaugeHealth {
        var g = throttle
        g.fullChargeMAh = fullChargeMAh; g.cycleCount = cycleCount; g.sohPct = sohPct
        g.cellDeltaMV = cellDeltaMV; g.gaugeStatus = gaugeStatus
        return g
    }

    // MARK: Writes from the phone
    /// Returns nil on success or an ATT error reason string.
    func apply(settingsData: Data) -> String? {
        guard let s = Settings(data: settingsData) else { return "too short" }
        guard s.isValid else { return "out of range" }
        settings = s
        logLine("Settings: maxSOC \(s.maxSOCPct)% fast \(s.fastCharge) usb2min \(s.usb2MinW) W led \(s.ledMode) autoFull \(s.autoFullChargeDays) d")
        return nil
    }

    func apply(command: Command) -> CommandResponse {
        func ok(_ detail: UInt16 = 0) -> CommandResponse { CommandResponse(opcode: command.opcode.rawValue, result: .ok, detail: detail) }
        func no(_ r: CommandResult, _ detail: UInt16 = 0) -> CommandResponse { CommandResponse(opcode: command.opcode.rawValue, result: r, detail: detail) }
        logLine("Command \(command.opcode) args \(command.args)")
        switch command.opcode {
        case .chargeTo100Once:
            fullOncePending = true; return ok()
        case .tripMode:
            guard let en = command.args.first else { return no(.badArg) }
            let hours = command.args.count > 1 && command.args[1] != 0 ? Int(command.args[1]) : 48
            tripModeHoursLeft = en != 0 ? hours : 0
            return ok(UInt16(tripModeHoursLeft))
        case .clearBonds:
            guard command.args.first == 0xA5 else { return no(.badArg) }
            logLine("(would clear bonds and disconnect)"); return ok()
        case .enterOTA:
            guard command.args.first == 0x5A else { return no(.badArg) }
            if socPct < 20 { return no(.refusedState, 1) }
            if outputDW > 200 { return no(.refusedState, 2) }
            logLine("(would reboot into OAD)"); return ok()
        case .shipMode:
            guard command.args.first == 0x3C else { return no(.badArg) }
            if usb1.state.value != .detached || usb2.state.value != .detached { return no(.refusedState, 1) }
            logLine("(would enter ship mode)"); return ok()
        case .identify:
            logLine("LED blink"); return ok()
        case .resetMCU:
            guard command.args.first == 0x99 else { return no(.badArg) }
            uptimeS = 0; return ok()
        case .openPairing:
            pairingWindowOpen = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 120) { [weak self] in self?.pairingWindowOpen = false }
            return ok()
        case .clearSensorFaults:
            broken.removeAll(); return ok()
        }
    }

    func logLine(_ s: String) {
        let t = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        log.append("\(t)  \(s)")
        if log.count > 300 { log.removeFirst(log.count - 300) }
    }

    // MARK: Simulation tick (1 Hz)
    func tick() {
        uptimeS &+= 1
        guard simulate else { return }
        let wh = designWh * Double(fullChargeMAh) / 5600
        let w = Double(packMV) / 1000 * Double(packMA) / 1000   // + into cells
        socPct = min(100, max(0, socPct + w / wh / 3600 * 100))
        // Stage follows the inputs so the app sees transitions without hand-driving them.
        if powerState == .charging || powerState == .passThrough {
            let cap = Double(fullOncePending || tripModeHoursLeft > 0 ? 100 : settings.maxSOCPct)
            if socPct >= cap - 0.05 {
                chargeStage = .hold; limitReason = cap < 100 ? .maxSOCReached : .none
            } else if cellMV.contains(where: { $0 < 3000 }) {
                chargeStage = .precharge
            } else if settings.fastCharge && (20...80).contains(socPct) && inputDW >= 900 {
                chargeStage = .fast
            } else if socPct > 97 && cap >= 100 {
                chargeStage = .constantVoltage
            } else {
                chargeStage = .normal
                limitReason = inputDW < 500 ? .sourceTooSmall : .none
            }
        } else if chargeStage != .inhibited && chargeStage != .fault {
            chargeStage = .idle
            if limitReason == .maxSOCReached || limitReason == .sourceTooSmall { limitReason = .none }
        }
        if uptimeS % 3600 == 0 && tripModeHoursLeft > 0 { tripModeHoursLeft -= 1 }
    }
}
