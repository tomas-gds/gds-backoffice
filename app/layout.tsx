import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tools Workspace",
  description: "A modular workspace for local data and research applications.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
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
