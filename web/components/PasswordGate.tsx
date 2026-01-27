'use client'

import { useState, useEffect } from 'react'

const CORRECT_PASSWORD = 'AIA'
const STORAGE_KEY = 'autography_access'

export function PasswordGate({ children }: { children: React.ReactNode }) {
  const [authorized, setAuthorized] = useState<boolean | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    setAuthorized(stored === 'granted')
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (password.toUpperCase() === CORRECT_PASSWORD) {
      localStorage.setItem(STORAGE_KEY, 'granted')
      setAuthorized(true)
      setError(false)
    } else {
      setError(true)
      setPassword('')
    }
  }

  // Still checking localStorage
  if (authorized === null) {
    return (
      <div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-[#C45A3B] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Authorized - show app
  if (authorized) {
    return <>{children}</>
  }

  // Not authorized - show password page
  return (
    <div className="min-h-screen bg-[#FDFBF7] flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold text-[#2D2A26] tracking-tight">
              Autography
            </h1>
            <p className="text-[#7D756A] mt-2">
              Product management wisdom from the people who shaped it
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  setError(false)
                }}
                placeholder="Enter access code"
                autoFocus
                className={`w-full px-4 py-3 text-base bg-white border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91] ${
                  error ? 'border-red-400' : 'border-[#E5E0D8]'
                }`}
              />
              {error && (
                <p className="mt-2 text-sm text-red-500">
                  Incorrect access code
                </p>
              )}
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-[#C45A3B] text-white font-medium rounded-xl hover:bg-[#a84832] transition-colors"
            >
              Enter
            </button>
          </form>
        </div>
      </div>

      <footer className="py-8 text-center">
        <p className="text-[10px] text-[#A89F91] uppercase tracking-widest">
          Made by GullyGorge in Portland, Ore
        </p>
      </footer>
    </div>
  )
}
