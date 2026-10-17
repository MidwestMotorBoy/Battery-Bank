import SwiftUI
import Charts
import MonolithKit

/// Health tab: Gauge Health plus Pack Life (spec §4.7, §4.9), for "how is this pack aging?".
struct PackLifeView: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        List {
            if let l = store.life {
                if !l.collecting {
                    Label("The gauge isn't recording lifetime data on this pack (LF_EN off), so these numbers aren't being updated.",
                          systemImage: "exclamationmark.triangle")
                        .font(.subheadline).foregroundStyle(.orange)
                }
                summary(l)
                temperatureBands(l)
                extremes(l)
                protection(l)
            } else {
                Text("This pack's firmware doesn't report lifetime data (needs protocol 1.1).")
                    .foregroundStyle(.secondary)
            }
        }
        .staleWhenOffline()
        .navigationTitle("Health")
        .packToolbar()
    }

    // MARK: Sections

    @ViewBuilder private func summary(_ l: PackLife) -> some View {
        Section {
            if let g = store.gauge {
                VStack(alignment: .leading, spacing: 6) {
                    HStack(alignment: .firstTextBaseline) {
                        Text("\(g.sohPct)%").font(.largeTitle.weight(.bold)).monospacedDigit()
                        Text("health").foregroundStyle(.secondary)
                        Spacer()
                        Text("\(g.fullChargeMAh) / \(g.designMAh) mAh").font(.subheadline).foregroundStyle(.secondary).monospacedDigit()
                    }
                    ProgressView(value: Double(min(g.sohPct, 100)), total: 100).tint(healthTint(g.sohPct))
                }
                .padding(.vertical, 4)
                LabeledContent("Charge cycles", value: "\(g.cycleCount)")
            }
            LabeledContent("Full charges", value: "\(l.fullCharges)")
            if let made = l.manufactured, let date = Calendar(identifier: .gregorian).date(from: made) {
                LabeledContent("Age", value: age(since: date))
            }
            LabeledContent("Powered on", value: hoursText(l.runtimeHours))
        } header: {
            Text("Overview")
        } footer: {
            if store.gauge?.gaugeStatus.contains(.notLearned) == true {
                Text("The gauge hasn't learned this pack's capacity yet; a full charge and discharge will fix that.")
            } else {
                Text("Health is the capacity the gauge measures now, against new. It has re-learned the capacity \(l.qmaxUpdates) time\(l.qmaxUpdates == 1 ? "" : "s").")
            }
        }
    }

    @ViewBuilder private func temperatureBands(_ l: PackLife) -> some View {
        let total = max(1, PackLife.Band.allCases.reduce(0) { $0 + l.hours(in: $1) })
        Section {
            Chart(PackLife.Band.allCases, id: \.self) { band in
                BarMark(x: .value("Band", bandLabel(l, band)), y: .value("Hours", l.hours(in: band)))
                    .foregroundStyle(bandColor(band))
                    .annotation(position: .top) {
                        let pct = Double(l.hours(in: band)) / Double(total)
                        if pct >= 0.01 {
                            Text(pct.formatted(.percent.precision(.fractionLength(0)))).font(.caption2).foregroundStyle(.secondary)
                        }
                    }
            }
            .chartYAxis { AxisMarks(position: .leading) { AxisGridLine(); AxisValueLabel() } }
            .chartXAxis { AxisMarks { AxisValueLabel().font(.caption2) } }
            .frame(height: 180)
            .padding(.vertical, 6)
        } header: {
            Text("Time at temperature")
        } footer: {
            Text("Hours the cells have spent in each band, in °C. Heat ages lithium cells fastest; time above \(l.thresholdsC[4]) °C counts most.")
        }
    }

    @ViewBuilder private func extremes(_ l: PackLife) -> some View {
        Section {
            if l.hasCellVoltageExtremes {
                LabeledContent("Cell voltage", value: "\(volts(l.cellMinMV)) – \(volts(l.cellMaxMV))")
                LabeledContent("Worst imbalance", value: "\(l.maxDeltaCellMV) mV")
            }
            if l.hasCellTempExtremes {
                LabeledContent("Cell temperature", value: "\(l.minTempCellC) to \(l.maxTempCellC) °C")
            }
            if l.maxTempFETC != -128 { LabeledContent("Hottest FETs", value: "\(l.maxTempFETC) °C") }
            LabeledContent("Peak charge", value: Fmt.amps(Double(l.maxChargeMA) / 1000))
            LabeledContent("Peak discharge", value: Fmt.amps(Double(-l.maxDischargeMA) / 1000))
        } header: {
            Text("Lifetime extremes")
        } footer: {
            Text("The widest values the gauge has ever measured. Cells are rated 2.5–4.2 V.")
        }
    }

    @ViewBuilder private func protection(_ l: PackLife) -> some View {
        Section {
            HStack {
                Text("Protection trips")
                Spacer()
                Text("\(l.safetyEvents)").foregroundStyle(l.safetyEvents > 0 ? .orange : .secondary)
            }
            if let c = l.lastSafetyCycle { LabeledContent("Last trip", value: "at cycle \(c)") }
            LabeledContent("Shutdowns", value: "\(l.shutdowns)")
            LabeledContent("Cell balancing", value: l.maxBalanceTime2h == 255 ? "510 h or more" : hoursText(Int(l.maxBalanceTime2h) * 2))
        } header: {
            Text("Protection")
        } footer: {
            Text("A trip is the gauge cutting power for over- or under-voltage, overcurrent, a short, or temperature. An occasional one from a shorted cable is normal; a rising count is worth a look.")
        }
    }

    // MARK: Formatting

    private func bandLabel(_ l: PackLife, _ band: PackLife.Band) -> String {
        switch l.range(of: band) {
        case (nil, let hi?): "<\(hi)"
        case (let lo?, nil): ">\(lo)"
        case (let lo?, let hi?): "\(lo)–\(hi)"
        default: "?"
        }
    }

    private func bandColor(_ band: PackLife.Band) -> Color {
        switch band {
        case .ut: .indigo
        case .lt: .blue
        case .stl: .teal
        case .rt: .green
        case .sth: .yellow
        case .ht: .orange
        case .ot: .red
        }
    }

    private func healthTint(_ soh: UInt8) -> Color { soh >= 80 ? .green : soh >= 70 ? .orange : .red }

    private func volts(_ mv: UInt16) -> String { (Double(mv) / 1000).formatted(.number.precision(.fractionLength(2))) + " V" }

    private func hoursText(_ h: Int) -> String {
        h < 48 ? "\(h) h" : "\((Double(h) / 24).formatted(.number.precision(.fractionLength(0)))) days"
    }

    private func age(since date: Date) -> String {
        let m = Calendar.current.dateComponents([.month], from: date, to: .now).month ?? 0
        let made = date.formatted(.dateTime.month(.abbreviated).year())
        if m < 1 { return "New · \(made)" }
        return (m < 24 ? "\(m) month\(m == 1 ? "" : "s")" : "\(m / 12) years") + " · \(made)"
    }
}
