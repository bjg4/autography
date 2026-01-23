'use client'

import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { useEffect, useState } from 'react'

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
    if (!key) {
      console.log('PostHog: NEXT_PUBLIC_POSTHOG_KEY not set - analytics disabled')
      return
    }

    posthog.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
      person_profiles: 'identified_only',
      capture_pageview: true,
      capture_pageleave: true,
      autocapture: true,
      persistence: 'localStorage+cookie',
      loaded: () => setInitialized(true),
    })
  }, [])

  // Only wrap with PostHog provider if initialized
  if (!initialized) {
    return <>{children}</>
  }

  return <PHProvider client={posthog}>{children}</PHProvider>
}
