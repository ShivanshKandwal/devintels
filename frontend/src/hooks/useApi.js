import { useState, useEffect, useCallback, useRef } from 'react'
import { useDemoMode } from '../context/DemoModeContext'

/**
 * Custom hook that tries the API first, falls back to demo data.
 * Respects global Demo Mode state.
 * @param {Function} apiFn  — API call function (should return a promise)
 * @param {*} fallback      — Demo data to use if API fails or Demo Mode is active
 * @param {boolean} immediate — Whether to call immediately on mount
 */
export function useApi(apiFn, fallback, immediate = true) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)
  const [isDemo, setIsDemo] = useState(false)
  const { demoMode } = useDemoMode()

  const fallbackRef = useRef(fallback)
  useEffect(() => {
    fallbackRef.current = fallback
  }, [fallback])

  const execute = useCallback(
    async (...args) => {
      setLoading(true)
      setError(null)

      if (demoMode) {
        // Simulate a small loading latency for smooth transitions
        await new Promise((r) => setTimeout(r, 450))
        setData(fallbackRef.current)
        setIsDemo(true)
        setLoading(false)
        return
      }

      try {
        const res = await apiFn(...args)
        setData(res.data)
        setIsDemo(false)
      } catch (err) {
        console.warn('API unavailable, using demo data:', err.message)
        setData(fallbackRef.current)
        setIsDemo(true)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [apiFn, demoMode]
  )

  useEffect(() => {
    if (immediate) execute()
  }, [execute, immediate])

  return { data, loading, error, isDemo, execute, setData }
}
