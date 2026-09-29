import fs from "node:fs";
import path from "node:path";
import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const alt =
  "AURORA Lifeline: which PHCs a cyclone cuts off, how likely, when, and what to move there now";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  const mark = fs.readFileSync(path.join(process.cwd(), "public/brand/aurora-mark-dark-bg.svg"), "utf8");
  const src = `data:image/svg+xml;base64,${Buffer.from(mark).toString("base64")}`;
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "72px",
        background: "radial-gradient(900px 500px at 85% 0%, #2a2160, #05080f 70%)",
        color: "#eef2f7",
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
        <img src={src} width={120} height={120} alt="" />
        <div style={{ display: "flex", fontSize: 64, letterSpacing: 6, fontWeight: 600 }}>
          AURORA{" "}
          <span style={{ fontWeight: 300, color: "#a3b0c2", marginLeft: 18, letterSpacing: 2 }}>
            Lifeline
          </span>
        </div>
      </div>
      <div style={{ marginTop: 48, fontSize: 44, lineHeight: 1.25, maxWidth: 1000 }}>
        IMD tells you the storm. AURORA tells you which PHC is cut off, how likely, when, and what to move
        there now.
      </div>
      <div style={{ marginTop: 36, fontSize: 26, color: "#3ee6c4" }}>
        Google Gemini · ADK · WeatherNext · Earth Engine · Cloud Run
      </div>
    </div>,
    size,
  );
}
