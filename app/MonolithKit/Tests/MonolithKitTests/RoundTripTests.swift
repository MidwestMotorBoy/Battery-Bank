import XCTest
@testable import MonolithKit

final class RoundTripTests: XCTestCase {
    func testStatusRoundTripAndLength() {
        var s = Status()
        s.socPct = 73; s.chargeStage = .known(.fast); s.limitReason = .known(.sourceTooSmall)
        s.flags = [.charging, .fastActive, .pairingWindow]
        s.packMV = 15_420; s.packMA = 5_600; s.remainingDWh = 598
        s.timeToEmptyMin = nil; s.timeToFullMin = 42
        s.cellMV = [3855, 3860, 3851, 3854]; s.chargeTargetMA = 5600
        s.outputDW = 0; s.inputDW = 920; s.powerState = .known(.charging); s.sensorsOKBoard = 3; s.uptimeS = 123_456
        let d = s.encode()
        XCTAssertEqual(d.count, 36)
        XCTAssertEqual(Status(data: d), s)
        XCTAssertEqual(d[0], 73)
        XCTAssertEqual(d[12], 0xFF); XCTAssertEqual(d[13], 0xFF) // time_to_empty = n/a
    }

    func testShorterPayloadStillParses() {
        let d = Status().encode().prefix(10) // only through pack_ma
        let s = Status(data: Data(d))
        XCTAssertNotNil(s)
        XCTAssertEqual(s?.cellMV, [0, 0, 0, 0])
    }

    func testLongerPayloadIgnoresTail() {
        let d = Status().encode() + Data([1, 2, 3, 4])
        XCTAssertEqual(Status(data: d), Status())
    }

    func testUnknownEnumKept() {
        var d = Status().encode()
        d[1] = 200
        XCTAssertEqual(Status(data: d)?.chargeStage.raw, 200)
        XCTAssertNil(Status(data: d)?.chargeStage.value)
    }

    func testPortsRoundTrip() {
        var p = Ports()
        p.usb1.state = .known(.sourcing); p.usb1.flags = [.pdContract, .emarked5A, .priority]
        p.usb1.contractMV = 20_000; p.usb1.contractMA = 5_000; p.usb1.powerDW = 872
        p.usb2.state = .known(.sinking); p.usb2.contractMV = 5_000; p.usb2.contractMA = 1_500; p.usb2.powerDW = -71
        let d = p.encode()
        XCTAssertEqual(d.count, 16)
        XCTAssertEqual(Ports(data: d), p)
    }

    func testTemperaturesSentinels() {
        var t = Temperatures()
        t.deciC[0] = 231; t.deciC[5] = 612
        t.notFitted = [.heatsink, .protectionFETs]
        t.faultMask = 1 << 7
        let d = t.encode()
        XCTAssertEqual(d.count, 22)
        let back = Temperatures(data: d)!
        XCTAssertEqual(back, t)
        XCTAssertEqual(back.celsius(.usb1Stage), 61.2)
        XCTAssertNil(back.celsius(.connectors))
        XCTAssertTrue(back.isBroken(.connectors))
        XCTAssertTrue(back.notFitted.contains(.heatsink))
    }

    func testSettingsDefaultsAndValidation() {
        let s = Settings()
        XCTAssertEqual(s.encode(), Data([95, 0, 20, 1, 30, 0, 0, 0]))
        XCTAssertTrue(s.isValid)
        var bad = s; bad.maxSOCPct = 59
        XCTAssertFalse(bad.isValid)
    }

    func testCommands() {
        XCTAssertEqual(Command.tripMode(true, hours: 24).encode(), Data([0x02, 1, 24]))
        XCTAssertEqual(Command.clearBonds.encode(), Data([0x03, 0xA5]))
        XCTAssertEqual(Command(data: Data([0x06]))?.opcode, .identify)
        XCTAssertNil(Command(data: Data([0x7F])))
        let r = CommandResponse(opcode: 0x02, result: .refusedState, detail: 7)
        XCTAssertEqual(CommandResponse(data: r.encode()), r)
    }

    func testUUIDs() {
        XCTAssertEqual(MonolithUUID.status.uuidString, "DDE70102-422D-4970-B281-8D5F2C2119C3")
    }

    func testPackLifeRoundTripAndLength() {
        var l = PackLife()
        l.manufactureDate = PackLife.packDate(year: 2026, month: 11, day: 3)
        l.runtime2h = 1_234; l.bandTime2h = [3, 40, 200, 500, 300, 180, 1]
        l.thresholdsC = [0, 10, 20, 25, 45, 55]
        l.cellMaxMV = 4_201; l.cellMinMV = 3_012; l.maxDeltaCellMV = 41
        l.maxChargeMA = 5_640; l.maxDischargeMA = -7_900
        l.maxTempCellC = 47; l.minTempCellC = -4; l.maxTempFETC = 61
        l.shutdowns = 2; l.fullCharges = 37; l.safetyEvents = 1; l.lastSafetyCycle = 18
        l.qmaxUpdates = 6; l.maxBalanceTime2h = 9; l.collecting = true
        let d = l.encode()
        XCTAssertEqual(d.count, 48)
        XCTAssertEqual(PackLife(data: d), l)
        XCTAssertEqual(PackLife(data: d)?.manufactured, DateComponents(year: 2026, month: 11, day: 3))
        XCTAssertEqual(l.range(of: .ut).0, nil); XCTAssertEqual(l.range(of: .ut).1, 0)
        XCTAssertEqual(l.range(of: .ot).0, 55); XCTAssertEqual(l.range(of: .ot).1, nil)
        XCTAssertEqual(d[34], UInt8(bitPattern: 47)); XCTAssertEqual(d[35], UInt8(bitPattern: -4))
    }

    func testPackLifeDefaultsMeanNotMeasured() {
        let l = PackLife(data: PackLife().encode())!
        XCTAssertFalse(l.hasCellVoltageExtremes)
        XCTAssertFalse(l.hasCellTempExtremes)
        XCTAssertNil(l.lastSafetyCycle)
        XCTAssertNil(l.manufactured)
        XCTAssertNotNil(PackLife(data: Data([0, 0])))   // short payload still parses
    }
}
