import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AURORA Lifeline",
  description:
    "Which hospitals, PHCs, shelters and villages a cyclone will cut off, how likely and when, derived from the official IMD forecast.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}
