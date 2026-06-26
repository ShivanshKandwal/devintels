import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook that tries the API first, falls back to demo data.
 * @param {Function} apiFn  — API call function (should return a promise)
 * @param {*} fallback      — Demo data to use if API fails
 * @param {boolean} immediate — Whether to call immediately on mount
 */
export function useApi(apiFn, fallback, immediate = true) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)
  const [isDemo, setIsDemo] = useState(false)

  const execute = useCallback(
    async (...args) => {
      setLoading(true)
      setError(null)
      try {
        const res = await apiFn(...args)
        setData(res.data)
        setIsDemo(false)
      } catch (err) {
        console.warn('API unavailable, using demo data:', err.message)
        setData(fallback)
        setIsDemo(true)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [apiFn, fallback]
  )

  useEffect(() => {
    if (immediate) execute()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, isDemo, execute, setData }
}
