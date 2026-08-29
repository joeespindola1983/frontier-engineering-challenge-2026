import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://wake-rowing-intelligence.joe-espindola.chatgpt.site'),
  title: 'WAKE — Evidence-backed rowing session review',
  description:
    'WAKE helps rowing coaches reconcile plans, telemetry, conditions, and human context into a verified session briefing.',
  openGraph: {
    type: 'website',
    url: '/',
    title: 'WAKE — Agentic Rowing Intelligence',
    description:
      'Evidence-backed rowing session review for coaches. Every row leaves a wake.',
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'WAKE — Every row leaves a wake.',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'WAKE — Agentic Rowing Intelligence',
    description:
      'Evidence-backed rowing session review for coaches. Every row leaves a wake.',
    images: ['/og.png'],
  },
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
