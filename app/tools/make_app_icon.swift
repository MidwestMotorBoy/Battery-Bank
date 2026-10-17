// Draws the Monolith app icon (1024 × 1024, opaque) with CoreGraphics.
// Run from app/:  swift tools/make_app_icon.swift Monolith/Assets.xcassets/AppIcon.appiconset/AppIcon.png
// The pack seen side-on: white tube with a top cap and two USB-C ports, a green charge level, a bolt.
import AppKit

let size = 1024.0
let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "AppIcon.png"

func color(_ hex: UInt32, _ a: CGFloat = 1) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255, alpha: a)
}

let space = CGColorSpace(name: CGColorSpace.sRGB)!
let ctx = CGContext(data: nil, width: Int(size), height: Int(size), bitsPerComponent: 8, bytesPerRow: 0,
                    space: space, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
// CoreGraphics' origin is bottom-left; flip so y grows downward like the layout numbers below.
ctx.translateBy(x: 0, y: size); ctx.scaleBy(x: 1, y: -1)

func linear(_ colors: [CGColor], from: CGPoint, to: CGPoint) {
    let g = CGGradient(colorsSpace: space, colors: colors as CFArray, locations: nil)!
    ctx.drawLinearGradient(g, start: from, end: to, options: [.drawsBeforeStartLocation, .drawsAfterEndLocation])
}

func rounded(_ r: CGRect, _ radius: CGFloat) -> CGPath {
    CGPath(roundedRect: r, cornerWidth: radius, cornerHeight: radius, transform: nil)
}

// Background: deep slate, lighter at the top.
linear([color(0x22344D), color(0x0B1320)], from: CGPoint(x: 0, y: 0), to: CGPoint(x: 0, y: size))

// Soft shadow under the pack.
ctx.saveGState()
ctx.setShadow(offset: CGSize(width: 0, height: 24), blur: 60, color: color(0x000000, 0.45))
let body = CGRect(x: 342, y: 150, width: 340, height: 740)
ctx.addPath(rounded(body, 96)); ctx.setFillColor(color(0xF2F4F7)); ctx.fillPath()
ctx.restoreGState()

// Body shading: a light gradient across the tube.
ctx.saveGState()
ctx.addPath(rounded(body, 96)); ctx.clip()
linear([color(0xFFFFFF), color(0xDCE1E8)], from: CGPoint(x: body.minX, y: 0), to: CGPoint(x: body.maxX, y: 0))
ctx.restoreGState()

// Two USB-C receptacles in the top cap.
for x in [452.0, 572.0] {
    let port = CGRect(x: x - 42, y: 196, width: 84, height: 28)
    ctx.addPath(rounded(port, 14)); ctx.setFillColor(color(0x1B2636)); ctx.fillPath()
    ctx.addPath(rounded(port.insetBy(dx: 14, dy: 10), 4)); ctx.setFillColor(color(0x55657A)); ctx.fillPath()
}

// Window into the cells.
let window = CGRect(x: body.minX + 34, y: 262, width: body.width - 68, height: body.maxY - 34 - 262)
ctx.addPath(rounded(window, 66)); ctx.setFillColor(color(0x101A28)); ctx.fillPath()

// Charge level, about three quarters.
let level = 0.74
ctx.saveGState()
ctx.addPath(rounded(window, 66)); ctx.clip()
let fillTop = window.maxY - window.height * level
ctx.clip(to: CGRect(x: window.minX, y: fillTop, width: window.width, height: window.maxY - fillTop))
linear([color(0x5BE584), color(0x22B455)], from: CGPoint(x: 0, y: fillTop), to: CGPoint(x: 0, y: window.maxY))
ctx.restoreGState()

// Bolt, centred in the charge.
let cx = window.midX, cy = fillTop + (window.maxY - fillTop) / 2
let bolt = CGMutablePath()
let pts: [(Double, Double)] = [(28, -150), (-82, 22), (-6, 22), (-30, 150), (82, -24), (6, -24)]
bolt.move(to: CGPoint(x: cx + pts[0].0, y: cy + pts[0].1))
for p in pts.dropFirst() { bolt.addLine(to: CGPoint(x: cx + p.0, y: cy + p.1)) }
bolt.closeSubpath()
ctx.addPath(bolt); ctx.setFillColor(color(0xFFFFFF)); ctx.fillPath()

let image = ctx.makeImage()!
let rep = NSBitmapImageRep(cgImage: image)
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
print("wrote \(out)")
