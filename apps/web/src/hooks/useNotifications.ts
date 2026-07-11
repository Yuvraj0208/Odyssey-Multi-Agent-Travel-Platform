"use client";

import { useEffect } from "react";
import { getNotifications, streamNotifications } from "@/lib/api";
import { useStore } from "@/lib/store";

/** Opens the long-lived proactive-notification stream and feeds the store. */
export function useNotifications() {
  const addNotification = useStore((s) => s.addNotification);

  useEffect(() => {
    let stopped = false;
    const ctrl = new AbortController();

    getNotifications()
      .then((list) => list.reverse().forEach(addNotification))
      .catch(() => {});

    (async () => {
      while (!stopped) {
        try {
          await streamNotifications(addNotification, ctrl.signal);
        } catch {
          /* connection dropped */
        }
        if (stopped) break;
        await new Promise((r) => setTimeout(r, 3000)); // reconnect backoff
      }
    })();

    return () => {
      stopped = true;
      ctrl.abort();
    };
  }, [addNotification]);
}
