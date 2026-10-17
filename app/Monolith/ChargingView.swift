import SwiftUI
import MonolithKit

struct ChargingView: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        NavigationStack {
            List {
                if let s = store.status {
                    Section("Charger") {
                        LabeledContent("Stage", value: s.chargeStage.label)
                        LabeledContent("Limited by", value: s.limitReason.label)
                        LabeledContent("Target current", value: Fmt.amps(Double(s.chargeTargetMA) / 1000))
                        LabeledContent("Mode", value: s.powerState.label)
                        let active = activeFlags(s.flags)
                        if !active.isEmpty { LabeledContent("Active", value: active.joined(separator: ", ")) }
                    }
                    Section("Battery") {
                        LabeledContent("Voltage", value: Fmt.volts(s.packVolts))
                        LabeledContent("Current", value: Fmt.amps(s.packAmps))
                        LabeledContent("Energy left", value: Fmt.wh(s.remainingWh))
                    }
                    Section {
                        ForEach(Array(s.cellMV.enumerated()), id: \.offset) { i, mv in
                            LabeledContent("Cell \(i + 1)", value: "\(mv) mV").monospacedDigit()
                        }
                        if let lo = s.cellMV.min(), let hi = s.cellMV.max() {
                            LabeledContent("Spread", value: "\(hi - lo) mV").monospacedDigit()
                        }
                    } header: {
                        Text("Cells")
                    } footer: {
                        if s.flags.contains(.balancing) { Text("The gauge is balancing the cells.") }
                    }
                }
            }
            .staleWhenOffline()
            .navigationTitle("Charging")
            .packToolbar()
        }
    }

    private func activeFlags(_ f: StatusFlags) -> [String] {
        var a: [String] = []
        if f.contains(.fastActive) { a.append("Fast charge") }
        if f.contains(.tripMode) { a.append("Trip mode") }
        if f.contains(.fullOncePending) { a.append("Full charge once") }
        if f.contains(.passThrough) { a.append("Pass-through") }
        if f.contains(.solar) { a.append("Solar") }
        if f.contains(.otaPending) { a.append("Update pending") }
        return a
    }
}
