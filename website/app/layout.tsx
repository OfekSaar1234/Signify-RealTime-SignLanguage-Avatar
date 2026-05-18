import type { Metadata, Viewport } from 'next'
import { DM_Sans, Outfit } from 'next/font/google'
import { ThemeProvider } from '@/components/theme-provider'

import './globals.css'

const fontSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
})

const fontDisplay = Outfit({
  subsets: ['latin'],
  variable: '--font-display',
})

export const metadata: Metadata = {
  title: 'Signify | Real-Time Sign Language Translation for Every Meeting',
  description:
    'Signify is an accessibility tool that translates real-time spoken audio into 3D Sign Language animation. Works locally and integrates seamlessly with Zoom meetings.',
  keywords: [
    'sign language translation',
    'accessibility tool',
    'ASL translation',
    'real-time translation',
    'Zoom accessibility',
    '3D avatar',
    'speech to sign language',
    'deaf accessibility',
    'hearing impaired',
    'video conferencing accessibility',
  ],
  authors: [{ name: 'Ofek' }, { name: 'Ori' }],
  creator: 'Signify Team',
  publisher: 'Signify',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    title: 'Signify | Real-Time Sign Language Translation',
    description:
      'Transform any meeting into an accessible experience with real-time 3D sign language translation.',
    siteName: 'Signify',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Signify | Real-Time Sign Language Translation',
    description:
      'Transform any meeting into an accessible experience with real-time 3D sign language translation.',
  },
  category: 'accessibility',
}

export const viewport: Viewport = {
  themeColor: '#1e5a8a',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${fontSans.variable} ${fontDisplay.variable} bg-background`} suppressHydrationWarning>
      <body className="font-sans antialiased bg-background text-foreground selection:bg-primary/30">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
