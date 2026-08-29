import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WAKE — Evidence-backed rowing session review',
  description:
    'WAKE helps rowing coaches reconcile plans, telemetry, conditions, and human context into a verified session briefing.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
