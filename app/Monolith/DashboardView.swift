import SwiftUI
import MonolithKit

/// First tab: state of charge, where the power is flowing, port voltages and time to full/empty.
struct DashboardView: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    WarningBanners()
                    if let s = store.status {
                        VStack(spacing: 14) {
                            SOCRing(status: s, limit: store.settings?.maxSOCPct)
                                .padding(.vertical, 8)
                            HStack(spacing: 14) {
                                Card { timeStat(s).frame(maxHeight: .infinity, alignment: .topLeading) }
                                Card { Stat(title: "Energy left", value: Fmt.wh(s.remainingWh)).frame(maxHeight: .infinity, alignment: .topLeading) }
                            }
                            .fixedSize(horizontal: false, vertical: true)
                            if let p = store.ports { PowerFlowCard(status: s, ports: p) }
                        }
                        .staleWhenOffline()
                    }
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle(store.packName)
            .packToolbar()
        }
    }

    @ViewBuilder private func timeStat(_ s: Status) -> some View {
        if let m = s.timeToFullMin {
            Stat(title: "Full in", value: Fmt.duration(minutes: m),
                 caption: store.settings.map { $0.maxSOCPct < 100 ? "to the \($0.maxSOCPct)% limit" : "to 100%" })
        } else if let m = s.timeToEmptyMin {
            Stat(title: "Empty in", value: Fmt.duration(minutes: m), caption: "at this draw")
        } else {
            Stat(title: "Time", value: "—", caption: "not charging or discharging")
        }
    }
}

/// Sources on top, the battery in the middle, loads below, each with voltage, current and power.
struct PowerFlowCard: View {
    let status: Status
    let ports: Ports

    private var named: [(String, MonolithKit.Port)] { [("USB-C 1", ports.usb1), ("USB-C 2", ports.usb2)] }
    private var sources: [(String, MonolithKit.Port)] { named.filter { $0.1.state.value == .sinking } }
    private var loads: [(String, MonolithKit.Port)] { named.filter { $0.1.state.value == .sourcing } }
    private var idle: [(String, MonolithKit.Port)] { named.filter { ![.sinking, .sourcing].contains($0.1.state.value) } }

    var body: some View {
        Card {
            HStack {
                Text("Power flow").font(.headline)
                Spacer()
                Text("\(Fmt.watts(status.inputWatts)) in · \(Fmt.watts(status.outputWatts)) out")
                    .font(.caption).foregroundStyle(.secondary).monospacedDigit()
            }
            VStack(spacing: 0) {
                ForEach(sources, id: \.0) { name, port in
                    portRow(name, port, role: "Input", icon: "arrow.down.circle.fill", tint: .green)
                    arrow(.green)
                }
                batteryRow
                ForEach(loads, id: \.0) { name, port in
                    arrow(.orange)
                    portRow(name, port, role: "Output", icon: "arrow.up.circle.fill", tint: .orange)
                }
            }
            if !idle.isEmpty {
                Divider()
                ForEach(idle, id: \.0) { name, port in
                    HStack {
                        Image(systemName: port.state.value == .fault ? "exclamationmark.triangle.fill" : "circle.dashed")
                            .foregroundStyle(port.state.value == .fault ? .red : .secondary)
                        Text(name)
                        Spacer()
                        Text(port.state.label).foregroundStyle(.secondary)
                    }
                    .font(.subheadline)
                }
            }
        }
    }

    private var batteryRow: some View {
        let charging = status.packMA > 0
        let tint: Color = status.packMA == 0 ? .secondary : charging ? .green : .orange
        return FlowRow(
            icon: "battery.75percent", tint: tint,
            title: "Battery", subtitle: status.packMA == 0 ? "Idle" : charging ? "Charging" : "Discharging",
            volts: status.packVolts, amps: status.packAmps, watts: status.packWatts, signed: true
        )
        .padding(.vertical, 6)
        .padding(.horizontal, 8)
        .background(tint.opacity(0.1), in: RoundedRectangle(cornerRadius: 10))
    }

    private func portRow(_ name: String, _ port: MonolithKit.Port, role: String, icon: String, tint: Color) -> some View {
        let volts = Double(port.contractMV) / 1000
        let watts = abs(port.watts)
        return FlowRow(icon: icon, tint: tint, title: name, subtitle: role + (port.flags.contains(.solarSource) ? " (solar)" : ""),
                       volts: volts, voltDigits: 1, amps: volts > 0 ? watts / volts : nil, watts: watts, signed: false)
            .padding(.horizontal, 8)
    }

    private func arrow(_ tint: Color) -> some View {
        Image(systemName: "arrow.down").font(.caption.weight(.bold)).foregroundStyle(tint)
            .frame(maxWidth: .infinity).padding(.vertical, 3)
    }
}

/// One line of the power flow: name on the left, V / A / W columns on the right.
struct FlowRow: View {
    let icon: String
    let tint: Color
    let title: String
    let subtitle: String
    let volts: Double
    var voltDigits = 2
    let amps: Double?
    let watts: Double
    let signed: Bool

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon).foregroundStyle(tint).font(.title3)
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(.subheadline.weight(.semibold))
                Text(subtitle).font(.caption).foregroundStyle(.secondary)
            }
            .lineLimit(1)
            .layoutPriority(1)
            Spacer(minLength: 4)
            column(volts.formatted(.number.precision(.fractionLength(voltDigits))) + " V", "volts")
            column(amps.map { (signed && $0 > 0 ? "+" : "") + Fmt.amps($0) } ?? "—", "current")
            column((signed && watts > 0 ? "+" : "") + Fmt.watts(watts), "power", bold: true)
        }
        .accessibilityElement(children: .combine)
    }

    private func column(_ value: String, _ label: String, bold: Bool = false) -> some View {
        VStack(alignment: .trailing, spacing: 1) {
            Text(value).font(.subheadline.weight(bold ? .semibold : .regular)).monospacedDigit()
            Text(label).font(.caption2).foregroundStyle(.tertiary)
        }
        .frame(minWidth: 58, alignment: .trailing)
    }
}

struct Stat: View {
    let title: String
    let value: String
    var tint: Color = .primary
    var caption: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.title3.weight(.semibold)).monospacedDigit().foregroundStyle(tint)
            if let caption { Text(caption).font(.caption2).foregroundStyle(.tertiary) }
        }
    }
}

struct SOCRing: View {
    let status: Status
    let limit: UInt8?

    private var fraction: Double { Double(status.socPct) / 100 }
    private var color: Color {
        if status.flags.contains(.lowSOC) { return .red }
        return status.socPct < 25 ? .orange : .green
    }

    var body: some View {
        ZStack {
            Circle().stroke(Color(.systemFill), lineWidth: 18)
            Circle()
                .trim(from: 0, to: fraction)
                .stroke(color.gradient, style: StrokeStyle(lineWidth: 18, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut, value: fraction)
            if let limit, limit < 100 {
                // Tick at the charge limit.
                Capsule()
                    .fill(Color.primary.opacity(0.6))
                    .frame(width: 3, height: 26)
                    .offset(y: -95)
                    .rotationEffect(.degrees(Double(limit) * 3.6))
            }
            VStack(spacing: 2) {
                Text("\(status.socPct)%")
                    .font(.system(size: 52, weight: .bold, design: .rounded))
                    .monospacedDigit()
                    .contentTransition(.numericText())
                Text(status.chargeStage.label)
                    .font(.subheadline).foregroundStyle(.secondary)
                if let limit {
                    Text("Limit \(limit)%").font(.caption).foregroundStyle(.tertiary)
                }
            }
        }
        .frame(width: 190, height: 190)
        .accessibilityElement(children: .combine)
    }
}
