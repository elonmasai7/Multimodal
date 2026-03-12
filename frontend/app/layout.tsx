import type { Metadata } from "next";

import { ClientProviders } from "@/components/layout/ClientProviders";
import { DockNavigation } from "@/components/navigation/DockNavigation";

import "./globals.css";

export const metadata: Metadata = {
  title: "Modal Learning World",
  description: "Immersive multimodal AI learning platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClientProviders>
          {children}
          <DockNavigation />
        </ClientProviders>
      </body>
    </html>
  );
}
