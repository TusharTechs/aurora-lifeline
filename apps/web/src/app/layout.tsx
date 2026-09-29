import type { Metadata, Viewport } from "next";
import { Inter, Noto_Sans_Devanagari, Noto_Sans_Telugu, Sora } from "next/font/google";
import "./globals.css";

const sora = Sora({
  subsets: ["latin"],
  weight: ["300", "400", "600"],
  variable: "--font-sora",
  display: "swap",
});
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const telugu = Noto_Sans_Telugu({
  subsets: ["telugu"],
  weight: ["400", "600"],
  variable: "--font-telugu",
  display: "swap",
});
const devanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "600"],
  variable: "--font-devanagari",
  display: "swap",
});

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
    <html
      lang="en"
      className={`${sora.variable} ${inter.variable} ${telugu.variable} ${devanagari.variable}`}
    >
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
