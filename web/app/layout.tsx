import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LabelGuard AI",
  description:
    "AI compliance checking for packaged commodities under Legal Metrology (PC) Rules, 2011",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
