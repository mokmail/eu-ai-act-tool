"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Minimal fetch-on-demand hook: `const { data, error, loading, run } = useApi(fn)`.
 * `run` is what views call — fetches stay explicit, never on mount unless asked.
 */
export function useApi<T, A extends unknown[]>(fn: (...args: A) => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const seq = useRef(0);

  const run = useCallback(
    async (...args: A) => {
      const id = ++seq.current;
      setLoading(true);
      setError(null);
      try {
        const result = await fn(...args);
        if (id === seq.current) setData(result);
        return result;
      } catch (err) {
        if (id === seq.current) {
          setData(null);
          setError(err instanceof Error ? err.message : String(err));
        }
        return null;
      } finally {
        if (id === seq.current) setLoading(false);
      }
    },
    [fn]
  );

  const clear = useCallback(() => {
    seq.current++;
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => () => {
    seq.current++;
  }, []);

  return { data, error, loading, run, clear };
}
