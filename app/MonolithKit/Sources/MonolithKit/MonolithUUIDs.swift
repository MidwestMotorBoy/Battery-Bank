import Foundation
import CoreBluetooth

/// UUIDs from docs/app/ble-gatt-spec.md §3.
public enum MonolithUUID {
    /// Base `DDE7xxxx-422D-4970-B281-8D5F2C2119C3`.
    public static func custom(_ short: UInt16) -> CBUUID {
        CBUUID(string: String(format: "DDE7%04X-422D-4970-B281-8D5F2C2119C3", short))
    }

    // Standard services
    public static let batteryService = CBUUID(string: "180F")
    public static let batteryLevel = CBUUID(string: "2A19")
    public static let deviceInfoService = CBUUID(string: "180A")
    public static let manufacturerName = CBUUID(string: "2A29")
    public static let modelNumber = CBUUID(string: "2A24")
    public static let firmwareRevision = CBUUID(string: "2A26")
    public static let hardwareRevision = CBUUID(string: "2A27")
    public static let serialNumber = CBUUID(string: "2A25")

    // Monolith service
    public static let monolithService = custom(0x0001)
    public static let protocolVersion = custom(0x0101)
    public static let status = custom(0x0102)
    public static let ports = custom(0x0103)
    public static let temperatures = custom(0x0104)
    public static let settings = custom(0x0105)
    public static let command = custom(0x0106)
    public static let commandResult = custom(0x0107)
    public static let gaugeHealth = custom(0x0108)
    public static let debugLog = custom(0x0109)
    public static let packLife = custom(0x010A)   // 1.1

    public static let localName = "Monolith"
    public static let manufacturerNameValue = "Monolith"
}

public enum MonolithProtocol {
    public static let major: UInt8 = 1
    public static let minor: UInt8 = 1
    /// Firmware requests this ATT MTU; no characteristic exceeds 48 bytes.
    public static let requestedMTU = 128
}
