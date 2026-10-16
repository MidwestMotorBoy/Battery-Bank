import Foundation

/// Little-endian reader. Reads past the end return nil, which callers map to
/// "field not available" (spec §1: shorter-than-expected values are not errors).
public struct ByteReader {
    private let data: Data
    public private(set) var offset: Int = 0

    public init(_ data: Data) { self.data = Data(data) } // copy so indices start at 0

    public var remaining: Int { data.count - offset }

    public mutating func u8() -> UInt8? {
        guard offset + 1 <= data.count else { return nil }
        defer { offset += 1 }
        return data[offset]
    }

    public mutating func u16() -> UInt16? {
        guard offset + 2 <= data.count else { return nil }
        defer { offset += 2 }
        return UInt16(data[offset]) | (UInt16(data[offset + 1]) << 8)
    }

    public mutating func s16() -> Int16? {
        u16().map { Int16(bitPattern: $0) }
    }

    public mutating func u32() -> UInt32? {
        guard offset + 4 <= data.count else { return nil }
        defer { offset += 4 }
        return UInt32(data[offset]) | (UInt32(data[offset + 1]) << 8)
            | (UInt32(data[offset + 2]) << 16) | (UInt32(data[offset + 3]) << 24)
    }

    public mutating func skip(_ n: Int) { offset = min(offset + n, data.count) }
}

/// Little-endian writer.
public struct ByteWriter {
    public private(set) var data = Data()
    public init() {}

    public mutating func u8(_ v: UInt8) { data.append(v) }
    public mutating func u16(_ v: UInt16) { data.append(contentsOf: [UInt8(v & 0xFF), UInt8(v >> 8)]) }
    public mutating func s16(_ v: Int16) { u16(UInt16(bitPattern: v)) }
    public mutating func u32(_ v: UInt32) {
        data.append(contentsOf: [UInt8(v & 0xFF), UInt8((v >> 8) & 0xFF), UInt8((v >> 16) & 0xFF), UInt8(v >> 24)])
    }
}

/// Sentinels from spec §1 / §4.4.
public enum Sentinel {
    public static let s16Invalid: Int16 = 0x7FFF      // no reading / broken
    public static let s16NotFitted: Int16 = 0x7FFE    // DNP footprint
    public static let u16NotAvailable: UInt16 = 0xFFFF
}
