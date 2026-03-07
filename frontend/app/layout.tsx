import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Multimodal Learning Platform",
  description: "Interactive storybooks and AI explainers"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="mx-auto max-w-6xl p-6">{children}</body>
    </html>
  );
}
