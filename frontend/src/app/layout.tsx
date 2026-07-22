import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FocusAI - Smart Attention Tracker",
  description: "Privacy-first Edge AI student monitoring.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-white" suppressHydrationWarning>{children}</body>
    </html>
  );
}
