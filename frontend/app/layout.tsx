import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChangeStory — Python diff analyzer",
  description:
    "Analyze Python Git diffs: changed symbols, impact, risks, test recommendations, and verification.",
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
