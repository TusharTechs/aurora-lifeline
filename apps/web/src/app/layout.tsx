import type { Metadata, Viewport } from "next";
// Fonts are self-hosted from npm (Fontsource, SIL OFL): the build never depends on a network fetch.
import "@fontsource-variable/inter";
import "@fontsource-variable/sora";
import "@fontsource/noto-sans-telugu/400.css";
import "@fontsource/noto-sans-telugu/600.css";
import "@fontsource/noto-sans-devanagari/400.css";
import "@fontsource/noto-sans-devanagari/600.css";
import "./globals.css";

const DESCRIPTION =
  "From the official IMD cyclone bulletin to a district plan: which PHCs, hospitals, shelters and villages lose road access, how likely, when, and what to move there now.";

export const metadata: Metadata = {
  metadataBase: new URL("https://aurora-lifeline.web.app"),
  title: {
    default: "AURORA Lifeline · cyclone road-access forecasts for district control rooms",
    template: "%s · AURORA Lifeline",
  },
  description: DESCRIPTION,
  applicationName: "AURORA Lifeline",
  openGraph: {
    title: "AURORA Lifeline",
    description: DESCRIPTION,
    url: "https://aurora-lifeline.web.app",
    siteName: "AURORA Lifeline",
    type: "website",
  },
};

export const viewport: Viewport = { themeColor: "#05080f", colorScheme: "dark" };

// Applies saved accessibility preferences before first paint (no flash of the wrong mode).
const PREFS = `try{var p=JSON.parse(localStorage.getItem("aurora-a11y")||"{}");var d=document.documentElement;if(p.motion)d.dataset.motion="reduce";if(p.contrast)d.dataset.contrast="high";if(p.text)d.dataset.text="large"}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: PREFS }} />
      </head>
      <body className="min-h-screen antialiased">
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
