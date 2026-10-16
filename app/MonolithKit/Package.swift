// swift-tools-version:5.9
import PackageDescription

// MonolithKit: the BLE protocol (docs/app/ble-gatt-spec.md) as Swift.
// Shared by the iPhone app and the FakePack macOS simulator so they can
// never disagree about a byte layout.
let package = Package(
    name: "MonolithKit",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "MonolithKit", targets: ["MonolithKit"]),
    ],
    targets: [
        .target(name: "MonolithKit", path: "Sources/MonolithKit"),
        .testTarget(name: "MonolithKitTests", dependencies: ["MonolithKit"], path: "Tests/MonolithKitTests"),
    ]
)
