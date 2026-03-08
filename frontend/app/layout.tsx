import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";

import { ClientProviders } from "@/components/layout/ClientProviders";
import { DockNavigation } from "@/components/navigation/DockNavigation";

import "./globals.css";

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-body" });
const space = Space_Grotesk({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Modal Learning World",
  description: "Immersive multimodal AI learning platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${jakarta.variable} ${space.variable}`}>
      <body>
        <ClientProviders>
          {children}
          <DockNavigation />
        </ClientProviders>
      </body>
    </html>
  );
}
