import { useCallback, useEffect, useState } from 'react'

/** What a data-fetching view needs: the result, the two async flags, a retry. */
export interface ApiState<T> {
  data: T | undefined
  loading: boolean
  error: Error | null
  reload: () => void
}

/**
 * Run an async fetcher and track its result, loading, and error state.
 *
 * Two deliberate behaviors:
 *
 * - Stale and unmounted responses are ignored. An `ignore` flag, flipped by
 *   the effect cleanup, discards any response that resolves after a newer
 *   request started or after the component unmounted. This also makes React
 *   StrictMode's double-invoke in development harmless.
 *
 * - On a refetch the previous `data` is kept. Only the very first load has
 *   `data === undefined`; a later refetch (for example a date-filter change)
 *   leaves the last result in place while `loading` is true, so the caller can
 *   keep the chart on screen instead of flashing a spinner.
 *
 * `deps` is passed explicitly by the caller because the `fetcher` closure is a
 * new function every render; the effect re-runs when a value in `deps`, or the
 * reload token, changes.
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
): ApiState<T> {
  const [data, setData] = useState<T | undefined>(undefined)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => setReloadToken((n) => n + 1), [])

  useEffect(() => {
    let ignore = false
    // A request is starting: enter the loading state and clear any prior
    // error. For an async data-fetching effect these updates are intentional,
    // not a render loop (the effect re-runs on the request inputs, not on the
    // flags it sets here), so set-state-in-effect is disabled for them.
    /* eslint-disable react-hooks/set-state-in-effect */
    setLoading(true)
    setError(null)
    /* eslint-enable react-hooks/set-state-in-effect */
    fetcher()
      .then((result) => {
        if (!ignore) setData(result)
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setError(err instanceof Error ? err : new Error(String(err)))
        }
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadToken])

  return { data, loading, error, reload }
}
