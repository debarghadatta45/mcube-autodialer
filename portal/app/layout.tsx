import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCUBE Auto-Dialer | Vedantu Sales Automation Portal",
  description:
    "From 35 manual calls to 278+ automated daily dials. Engineered by Debargha Datta for Vedantu sales team.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
