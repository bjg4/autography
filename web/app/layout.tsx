import type { Metadata, Viewport } from 'next'
import './globals.css'
import { PostHogProvider } from '@/components/PostHogProvider'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export const metadata: Metadata = {
  title: 'Autography - PM Knowledge Base',
  description: 'Search the product management knowledge base',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <PostHogProvider>
          {children}
        </PostHogProvider>
      </body>
    </html>
  )
}
