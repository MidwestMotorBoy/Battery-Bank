import SwiftUI
import MonolithKit

/// The conditions a dead sensor in a potted pack would otherwise hide (docs/app/README.md, design rules).
struct WarningBanners: View {
    @EnvironmentObject private var store: PackStore

    private var warnings: [(String, String)] {
        guard let s = store.status else { return [] }
        var w: [(String, String)] = []
        if s.flags.contains(.hardShutdown) { w.append(("flame.fill", "Outputs off: over-temperature shutdown")) }
        if s.flags.contains(.throttle) { w.append(("thermometer.high", "Thermal throttle: limited to 20 W")) }
        if s.flags.contains(.gaugeFault) { w.append(("exclamationmark.octagon.fill", "Battery gauge fault")) }
        if s.flags.contains(.sensorsDegraded) { w.append(("sensor.fill", "Fewer than 3 board temperature sensors working")) }
        if let t = store.temperatures {
            let broken = TemperatureSlot.allCases.filter { t.isBroken($0) }.map(\.label)
            if !broken.isEmpty { w.append(("exclamationmark.triangle.fill", "Sensor broken: " + broken.joined(separator: ", "))) }
        }
        return w
    }

    var body: some View {
        ForEach(warnings, id: \.1) { icon, text in
            Label(text, systemImage: icon)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(.red.gradient, in: RoundedRectangle(cornerRadius: 12))
        }
    }
}

/// Connection state, for the navigation bar.
struct LinkBadge: View {
    @EnvironmentObject private var store: PackStore

    var body: some View {
        let (text, color): (String, Color) = switch store.link {
        case .connected: ("Connected", .green)
        case .demo: ("Demo", .blue)
        case .connecting: ("Reconnecting…", .orange)
        default: ("Offline", .gray)
        }
        // HStack, not Label: toolbars render a Label icon-only.
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(text)
        }
        .font(.caption.weight(.medium))
        .padding(.horizontal, 6)
        .fixedSize()
        .accessibilityElement(children: .combine)
    }
}

/// Greys content and says how old it is while the pack is out of range.
struct StaleModifier: ViewModifier {
    @EnvironmentObject private var store: PackStore

    func body(content: Content) -> some View {
        VStack(spacing: 8) {
            if !store.isLive, let t = store.lastUpdate {
                TimelineView(.periodic(from: .now, by: 30)) { _ in
                    Label("Last seen \(t.formatted(.relative(presentation: .named)))", systemImage: "clock")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            content
                .opacity(store.isLive ? 1 : 0.45)
                .saturation(store.isLive ? 1 : 0)
        }
    }
}

extension View {
    func staleWhenOffline() -> some View { modifier(StaleModifier()) }

    func packToolbar() -> some View {
        toolbar { ToolbarItem(placement: .topBarTrailing) { LinkBadge() } }
    }
}

/// Rounded card used on the dashboard.
struct Card<Content: View>: View {
    @ViewBuilder var content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 8) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 16))
    }
}
