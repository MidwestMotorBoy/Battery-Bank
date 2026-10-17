import SwiftUI
import MonolithKit

struct ContentView: View {
    @EnvironmentObject var model: PackModel
    @EnvironmentObject var server: PeripheralServer

    var body: some View {
        HSplitView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    radioSection
                    packSection
                    PortEditor(title: "USB1 (priority)", port: $model.usb1)
                    PortEditor(title: "USB2", port: $model.usb2)
                    temperatureSection
                    settingsSection
                }
                .padding()
            }
            .frame(minWidth: 460)
            logPane
                .frame(minWidth: 320)
        }
        .frame(minWidth: 860, minHeight: 640)
    }

    // MARK: Sections

    private var radioSection: some View {
        GroupBox("Radio") {
            HStack {
                Circle().fill(server.advertising ? .green : .orange).frame(width: 10, height: 10)
                Text(server.stateText)
                Spacer()
                Button(server.advertising ? "Stop advertising" : "Advertise") {
                    server.advertising ? server.stopAdvertising() : server.startAdvertising()
                }
            }
            if !server.subscribers.isEmpty {
                Text("Subscribed: " + server.subscribers.keys.sorted().joined(separator: ", "))
                    .font(.caption).foregroundStyle(.secondary)
            }
            Toggle("Pairing window open (flag only; macOS decides real pairing)", isOn: $model.pairingWindowOpen)
        }
    }

    private var packSection: some View {
        GroupBox("Pack") {
            Grid(alignment: .leading, verticalSpacing: 8) {
                GridRow {
                    Text("SOC")
                    Slider(value: $model.socPct, in: 0...100)
                    Text("\(Int(model.socPct)) %").monospacedDigit().frame(width: 60, alignment: .trailing)
                }
                GridRow {
                    Text("Stage")
                    Picker("", selection: $model.chargeStage) {
                        ForEach(ChargeStage.allCases, id: \.self) { Text($0.label).tag($0) }
                    }.labelsHidden()
                    Toggle("Simulate", isOn: $model.simulate)
                }
                GridRow {
                    Text("Limit")
                    Picker("", selection: $model.limitReason) {
                        ForEach(LimitReason.allCases, id: \.self) { Text($0.label).tag($0) }
                    }.labelsHidden()
                    Text("")
                }
                GridRow {
                    Text("Health")
                    HStack {
                        Stepper("SOH \(model.sohPct) %", value: $model.sohPct, in: 50...100)
                        Stepper("Cycles \(model.cycleCount)", value: $model.cycleCount, in: 0...2000)
                        Stepper("FCC \(model.fullChargeMAh)", value: $model.fullChargeMAh, in: 3000...5700, step: 20)
                    }
                    Text("")
                }
            }
            HStack {
                flagToggle("Throttle (20 W)", .throttle)
                flagToggle("Gauge fault", .gaugeFault)
                flagToggle("Hard shutdown", .hardShutdown)
                flagToggle("Balancing", .balancing)
                flagToggle("OTA pending", .otaPending)
            }
            HStack {
                Text("Derived:").foregroundStyle(.secondary)
                Text("\(Double(model.packMV) / 1000, specifier: "%.2f") V  \(Double(model.packMA) / 1000, specifier: "%+.2f") A  \(Double(model.remainingDWh) / 10, specifier: "%.1f") Wh  \(model.powerState.label)")
                    .monospacedDigit()
            }.font(.caption)
        }
    }

    private func flagToggle(_ title: String, _ flag: StatusFlags) -> some View {
        Toggle(title, isOn: Binding(
            get: { model.flags.contains(flag) },
            set: { $0 ? model.flags.insert(flag) : model.flags.remove(flag) }
        ))
    }

    private var temperatureSection: some View {
        GroupBox("Temperatures") {
            ForEach(TemperatureSlot.allCases, id: \.self) { slot in
                HStack {
                    Text(slot.label).frame(width: 120, alignment: .leading)
                    if model.notFitted.contains(slot) {
                        Text("not fitted").foregroundStyle(.secondary).frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        Slider(value: Binding(
                            get: { model.tempC[slot.rawValue] ?? 25 },
                            set: { model.tempC[slot.rawValue] = $0 }
                        ), in: -20...110)
                        Text("\(model.tempC[slot.rawValue] ?? 25, specifier: "%.1f") °C").monospacedDigit().frame(width: 64, alignment: .trailing)
                    }
                    Toggle("Broken", isOn: setBinding($model.broken, slot)).frame(width: 80)
                    if slot.isBoard {
                        Toggle("Not fitted", isOn: setBinding($model.notFitted, slot)).frame(width: 90)
                    } else {
                        Spacer().frame(width: 90)
                    }
                }
            }
            Text("Throttle points reported to the app: cells \(Double(model.throttle.throttleCellDC) / 10, specifier: "%.0f") °C, board \(Double(model.throttle.throttleBoardDC) / 10, specifier: "%.0f") °C, connectors \(Double(model.throttle.throttleConnDC) / 10, specifier: "%.0f") °C")
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    private func setBinding(_ set: Binding<Set<TemperatureSlot>>, _ slot: TemperatureSlot) -> Binding<Bool> {
        Binding(get: { set.wrappedValue.contains(slot) },
                set: { $0 ? set.wrappedValue.insert(slot) : set.wrappedValue.remove(slot) })
    }

    private var settingsSection: some View {
        GroupBox("Settings (as written by the phone)") {
            HStack(spacing: 16) {
                Text("Max SOC \(model.settings.maxSOCPct) %")
                Text("Fast charge \(model.settings.fastCharge ? "on" : "off")")
                Text("USB2 min \(model.settings.usb2MinW) W")
                Text("LED \(model.settings.ledMode)")
                Text("Auto full \(model.settings.autoFullChargeDays) d")
            }.font(.callout)
            HStack {
                Toggle("Charge-to-100 pending", isOn: $model.fullOncePending)
                Stepper("Trip mode hours left: \(model.tripModeHoursLeft)", value: $model.tripModeHoursLeft, in: 0...168)
            }
        }
    }

    private var logPane: some View {
        VStack(alignment: .leading) {
            HStack {
                Text("Log").font(.headline)
                Spacer()
                Button("Clear") { model.log.removeAll() }
            }
            ScrollViewReader { proxy in
                List(Array(model.log.enumerated()), id: \.offset) { i, line in
                    Text(line).font(.system(.caption, design: .monospaced)).id(i)
                }
                .onChange(of: model.log.count) { _, n in
                    if n > 0 { proxy.scrollTo(n - 1) }
                }
            }
        }
        .padding()
    }
}

/// One port's editable record.
struct PortEditor: View {
    let title: String
    @Binding var port: Port

    var body: some View {
        GroupBox(title) {
            Grid(alignment: .leading, verticalSpacing: 8) {
                GridRow {
                    Text("State")
                    Picker("", selection: Binding(
                        get: { port.state.value ?? .detached },
                        set: { port.state = .known($0) }
                    )) {
                        ForEach(PortState.allCases, id: \.self) { Text($0.label).tag($0) }
                    }.labelsHidden()
                    HStack {
                        Button("5 V 3 A") { set(5000, 3000, pd: false) }
                        Button("9 V 2.22 A") { set(9000, 2220) }
                        Button("20 V 5 A") { set(20000, 5000, emarked: true) }
                        Button("Solar 5 V") { set(5000, 1500, pd: false, solar: true) }
                    }
                }
                GridRow {
                    Text("Contract")
                    HStack {
                        TextField("mV", value: $port.contractMV, format: .number).frame(width: 70)
                        Text("mV")
                        TextField("mA", value: $port.contractMA, format: .number).frame(width: 70)
                        Text("mA")
                        Text("= \(port.contractWatts, specifier: "%.1f") W").foregroundStyle(.secondary)
                    }
                    Text("")
                }
                GridRow {
                    Text("Power")
                    Slider(value: Binding(get: { Double(port.powerDW) / 10 }, set: { port.powerDW = Int16($0 * 10) }), in: -100...100)
                    Text("\(port.watts, specifier: "%+.1f") W").monospacedDigit().frame(width: 70, alignment: .trailing)
                }
            }
            HStack {
                flag("PD", .pdContract); flag("5 A cable", .emarked5A); flag("Solar", .solarSource)
                flag("Throttled", .throttled); flag("Loop", .loopDetected); flag("Source-only", .sourceOnly); flag("OCP", .overcurrent)
            }
            Text("Power: + out of the pack (sourcing), − into the pack (sinking)").font(.caption).foregroundStyle(.secondary)
        }
    }

    private func set(_ mv: UInt16, _ ma: UInt16, pd: Bool = true, emarked: Bool = false, solar: Bool = false) {
        port.contractMV = mv; port.contractMA = ma
        if pd { port.flags.insert(.pdContract) } else { port.flags.remove(.pdContract) }
        if emarked { port.flags.insert(.emarked5A) } else { port.flags.remove(.emarked5A) }
        if solar { port.flags.insert(.solarSource); port.state = .known(.sinking); port.powerDW = -Int16(min(Int(mv) * Int(ma) / 100_000, 150)) }
        else { port.flags.remove(.solarSource) }
        if port.state.value == .detached { port.state = .known(.sourcing) }
        if port.powerDW == 0 { port.powerDW = Int16(min(Int(mv) * Int(ma) / 100_000, 1000)) * (port.state.value == .sinking ? -1 : 1) }
    }

    private func flag(_ title: String, _ f: PortFlags) -> some View {
        Toggle(title, isOn: Binding(get: { port.flags.contains(f) }, set: { $0 ? port.flags.insert(f) : port.flags.remove(f) }))
    }
}

private extension PowerState {
    var label: String {
        switch self {
        case .charging: "charging"; case .sourcing: "sourcing"; case .idle: "idle"
        case .reset: "reset"; case .passThrough: "pass-through"; case .ship: "ship"
        }
    }
}
