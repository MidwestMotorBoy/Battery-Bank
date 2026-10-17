import SwiftUI
import MonolithKit

/// All ten sensors (spec §4.4) drawn where they sit in the pack, colored against their throttle points.
struct TemperaturesView: View {
    @EnvironmentObject private var store: PackStore
    @State private var selected: TemperatureSlot?
    @State private var clearing = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            List {
                Section { WarningBanners().listRowInsets(EdgeInsets()).listRowBackground(Color.clear) }
                if let t = store.temperatures {
                    Section {
                        // Detail above the drawing so it stays on screen when a sensor is tapped.
                        if let slot = selected { SensorDetail(slot: slot, temps: t, gauge: store.gauge) }
                        PackDiagram(temps: t, gauge: store.gauge, selected: $selected)
                            .frame(maxWidth: .infinity)
                            .listRowBackground(Color.clear)
                    } footer: {
                        Text("Placeholder drawing until the enclosure design is final. Tap a sensor for details.")
                    }
                    Section("All sensors") {
                        ForEach(TemperatureSlot.allCases.filter { !t.notFitted.contains($0) }, id: \.self) { slot in
                            Button { selected = slot } label: { SensorRow(slot: slot, temps: t, gauge: store.gauge) }
                                .foregroundStyle(.primary)
                        }
                    }
                    if t.faultMask != 0 {
                        Section {
                            Button("Re-test sensors now") { clearFaults() }.disabled(clearing || !store.isLive)
                        } footer: {
                            Text(error ?? "The pack retries broken sensors on its own; this re-tests them immediately.")
                        }
                    }
                }
                if let s = store.status {
                    Section {
                        LabeledContent("Board sensors working", value: "\(s.sensorsOKBoard)")
                    } footer: {
                        Text("Throttle points come from the pack's firmware.")
                    }
                }
            }
            .staleWhenOffline()
            .navigationTitle("Temperatures")
            .packToolbar()
        }
    }

    private func clearFaults() {
        clearing = true
        Task {
            defer { clearing = false }
            do { try await store.run(.clearSensorFaults); error = nil }
            catch { self.error = error.localizedDescription }
        }
    }
}

// MARK: Reading one sensor

/// What the UI needs to know about one slot right now.
struct SensorReading {
    enum State { case ok(Double), broken, noReading, notFitted }
    let state: State
    let throttle: Double?

    init(_ slot: TemperatureSlot, _ t: Temperatures, _ g: GaugeHealth?) {
        throttle = g.map { Double(slot.throttleDC($0)) / 10 }
        if t.notFitted.contains(slot) { state = .notFitted }
        else if t.isBroken(slot) { state = .broken }
        else if let c = t.celsius(slot) { state = .ok(c) }
        else { state = .noReading }
    }

    var text: String {
        switch state {
        case .ok(let c): c.formatted(.number.precision(.fractionLength(0))) + "°"
        case .broken: "!"
        case .noReading: "?"
        case .notFitted: "—"
        }
    }

    /// Cool blue → green → yellow, then orange within 5 °C of the throttle point and red at it.
    var color: Color {
        guard case .ok(let c) = state else { return Color(.systemGray3) }
        if let th = throttle {
            if c >= th { return .red }
            if c >= th - 5 { return .orange }
        }
        switch c {
        case ..<5: return .blue
        case ..<15: return .teal
        case ..<35: return .green
        default: return .yellow
        }
    }

    var isNearLimit: Bool {
        if case .ok(let c) = state, let th = throttle { return c >= th - 5 }
        return false
    }
}

struct SensorRow: View {
    let slot: TemperatureSlot
    let temps: Temperatures
    let gauge: GaugeHealth?

    var body: some View {
        let r = SensorReading(slot, temps, gauge)
        HStack {
            Circle().fill(r.color).frame(width: 10, height: 10)
            Text(slot.label)
            Spacer()
            switch r.state {
            case .ok(let c):
                Text(Fmt.celsius(c)).monospacedDigit().fontWeight(r.isNearLimit ? .semibold : .regular)
                    .foregroundStyle(r.isNearLimit ? .orange : .primary)
            case .broken: Label("Broken", systemImage: "exclamationmark.triangle.fill").foregroundStyle(.red)
            case .noReading, .notFitted: Text("No reading").foregroundStyle(.secondary)
            }
        }
    }
}

struct SensorDetail: View {
    let slot: TemperatureSlot
    let temps: Temperatures
    let gauge: GaugeHealth?

    var body: some View {
        let r = SensorReading(slot, temps, gauge)
        VStack(alignment: .leading, spacing: 4) {
            Text(slot.label).font(.headline)
            Text(location).font(.subheadline).foregroundStyle(.secondary)
            HStack {
                switch r.state {
                case .ok(let c): Text(Fmt.celsius(c)).font(.title2.weight(.semibold)).monospacedDigit().foregroundStyle(r.color)
                case .broken: Text("Broken: firmware stopped trusting this sensor").foregroundStyle(.red)
                case .noReading: Text("No reading")
                case .notFitted: Text("Not fitted on this board").foregroundStyle(.secondary)
                }
                Spacer()
                if let th = r.throttle { Text("throttles at \(Fmt.celsius(th))").font(.caption).foregroundStyle(.secondary) }
            }
        }
        .padding(.vertical, 4)
    }

    private var location: String {
        switch slot {
        case .cell1, .cell2, .cell3, .cell4: "NTC taped to the cell, read by the gauge"
        case .gaugeDie: "Inside the gauge chip on the bottom PCB"
        case .usb1Stage: "USB-C 1 power converter, top board"
        case .usb2Stage: "USB-C 2 power converter, top board"
        case .connectors: "Between the two USB-C connectors"
        case .heatsink: "Heatsink plate under the top cap"
        case .protectionFETs: "Battery protection FETs"
        }
    }
}

// MARK: Pack diagram (placeholder)

/// Exploded view of the pack, top to bottom: top board in the cap, the 2×2 cell stack seen from above,
/// bottom PCB. Proportions are rough (see mechanical/monolith_shell.py for the real ones).
struct PackDiagram: View {
    let temps: Temperatures
    let gauge: GaugeHealth?
    @Binding var selected: TemperatureSlot?

    var body: some View {
        VStack(spacing: 0) {
            layer("Top board") {
                ZStack {
                    // USB-C receptacles along the top edge, the connector sensor between them.
                    HStack(spacing: 84) { port("USB-C 1"); port("USB-C 2") }
                        .offset(y: -38)
                    chip(.connectors).offset(y: -38)
                    chip(.usb1Stage).offset(x: -92, y: 14)
                    chip(.usb2Stage).offset(x: 92, y: 14)
                    chip(.heatsink).offset(x: -30, y: 30)
                    chip(.protectionFETs).offset(x: 30, y: 30)
                }
                .frame(width: 290, height: 130)
            }
            connector
            layer("Cells (from above)") {
                ZStack {
                    RoundedRectangle(cornerRadius: 46).fill(Color(.tertiarySystemFill)).frame(width: 196, height: 196)
                    Grid(horizontalSpacing: 8, verticalSpacing: 8) {
                        GridRow { cell(.cell1); cell(.cell2) }
                        GridRow { cell(.cell4); cell(.cell3) }
                    }
                }
                .frame(width: 290, height: 206)
            }
            connector
            layer("Bottom PCB") {
                chip(.gaugeDie).frame(width: 290, height: 64)
            }
        }
        .padding(.vertical, 8)
    }

    private func layer<Content: View>(_ title: String, @ViewBuilder _ content: () -> Content) -> some View {
        VStack(spacing: 4) {
            Text(title).font(.caption.weight(.medium)).foregroundStyle(.secondary)
            content()
                .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 18))
                .overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(Color(.separator)))
        }
    }

    private var connector: some View {
        Rectangle().fill(Color(.separator)).frame(width: 1.5, height: 18).padding(.vertical, 2)
    }

    private func port(_ name: String) -> some View {
        VStack(spacing: 2) {
            Capsule().fill(Color(.systemGray)).frame(width: 46, height: 14)
            Text(name).font(.system(size: 9)).foregroundStyle(.secondary)
        }
    }

    private func isSelected(_ slot: TemperatureSlot) -> Bool { selected == slot }

    private func cell(_ slot: TemperatureSlot) -> some View {
        let r = SensorReading(slot, temps, gauge)
        return Button { selected = slot } label: {
            ZStack {
                Circle().fill(r.color.opacity(0.25))
                Circle().strokeBorder(r.color, lineWidth: isSelected(slot) ? 4 : 2)
                VStack(spacing: 0) {
                    Text(r.text).font(.title3.weight(.semibold)).monospacedDigit()
                    Text(slot.label).font(.caption2).foregroundStyle(.secondary)
                }
            }
            .frame(width: 86, height: 86)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(slot.label), \(r.text)")
    }

    private func chip(_ slot: TemperatureSlot) -> some View {
        let r = SensorReading(slot, temps, gauge)
        let fitted = !temps.notFitted.contains(slot)
        return Button { selected = slot } label: {
            VStack(spacing: 0) {
                Text(r.text).font(.footnote.weight(.semibold)).monospacedDigit()
                Text(shortName(slot)).font(.system(size: 9)).foregroundStyle(.secondary)
            }
            .frame(width: 58, height: 34)
            .background(r.color.opacity(fitted ? 0.25 : 0), in: RoundedRectangle(cornerRadius: 6))
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .strokeBorder(r.color, style: StrokeStyle(lineWidth: isSelected(slot) ? 3 : 1.5, dash: fitted ? [] : [3, 3]))
            )
            .opacity(fitted ? 1 : 0.6)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(slot.label), \(fitted ? r.text : "not fitted")")
    }

    private func shortName(_ slot: TemperatureSlot) -> String {
        switch slot {
        case .usb1Stage: "USB1 conv"
        case .usb2Stage: "USB2 conv"
        case .connectors: "Ports"
        case .heatsink: "Heatsink"
        case .protectionFETs: "FETs"
        case .gaugeDie: "Gauge"
        default: slot.label
        }
    }
}
