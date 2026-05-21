import { useEffect, useState } from 'react'

/**
 * Return `value` only after it has stopped changing for `delayMs`. Used by the
 * search box so a request fires once the user pauses, not on every keystroke.
 */
export function useDebounce<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(id)
  }, [value, delayMs])

  return debounced
}
