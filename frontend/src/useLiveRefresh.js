import { useEffect, useRef } from "react";

/** Refetch the open screen so Telegram writes show up without a reload. */
export function useLiveRefresh(refresh, intervalMs = 4000) {
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;

  useEffect(() => {
    let stopped = false;

    async function tick() {
      if (stopped || document.visibilityState === "hidden") return;
      try {
        await refreshRef.current();
      } catch {
        // Keep the current screen if a background refresh fails.
      }
    }

    const timer = window.setInterval(tick, intervalMs);
    window.addEventListener("focus", tick);
    document.addEventListener("visibilitychange", tick);
    return () => {
      stopped = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", tick);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [intervalMs]);
}
