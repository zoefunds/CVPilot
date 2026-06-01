import type { Metadata, Viewport } from 'next';
import { Inter, Instrument_Serif } from 'next/font/google';
import { Providers } from '@/components/providers/Providers';
import { appName } from '@/lib/brand';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const serif = Instrument_Serif({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: `${appName}. AI Job Application Intelligence.`,
  description:
    'CVPilot evaluates your CV, cover letter, and job match with verifiable AI scoring on GenLayer StudioNet. Get the truth before you apply.',
  applicationName: appName,
  openGraph: {
    title: `${appName}. AI Job Application Intelligence.`,
    description:
      'Verifiable CV scoring, cover letter analysis and recommendations powered by GenLayer Intelligent Contracts.',
    type: 'website',
  },
  icons: { icon: '/favicon.ico' },
};

export const viewport: Viewport = {
  themeColor: '#efece4',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${serif.variable}`}>
      <body className="min-h-screen bg-[#efece4] text-[#1a1814] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
