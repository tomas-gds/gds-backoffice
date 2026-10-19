import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GDS Backoffice",
  description: "A modular workspace for local data and research applications.",
  icons: {
    icon: "/gds-icon.png",
    shortcut: "/gds-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
