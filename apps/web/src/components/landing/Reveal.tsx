"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";

/**
 * Scroll-reveal wrapper with a safety net.
 *
 * Framer's `whileInView` relies solely on IntersectionObserver. If IO never
 * reports (headless/non-compositing renderers, some in-app browsers, crawlers),
 * the content stays at opacity 0 — i.e. an invisible landing page. This adds a
 * scroll-position fallback and treats reduced-motion as "just show it", so the
 * animation is only ever an enhancement.
 */
export function Reveal({
  children,
  delay = 0,
  y = 22,
  className = "",
  as = "div",
}: {
  children: React.ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  as?: "div" | "section";
}) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (reduced) {
      setShown(true);
      return;
    }
    const el = ref.current;
    if (!el) {
      setShown(true);
      return;
    }

    const show = () => setShown(true);
    let io: IntersectionObserver | undefined;
    if (typeof IntersectionObserver !== "undefined") {
      io = new IntersectionObserver(([e]) => e.isIntersecting && show(), {
        threshold: 0.08,
        rootMargin: "0px 0px -6% 0px",
      });
      io.observe(el);
    }

    const check = () => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.94 && r.bottom > 0) show();
    };
    check();
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check, { passive: true });

    return () => {
      io?.disconnect();
      window.removeEventListener("scroll", check);
      window.removeEventListener("resize", check);
    };
  }, [reduced]);

  const Comp = as === "section" ? motion.section : motion.div;

  return (
    <Comp
      ref={ref as never}
      initial={false}
      animate={shown ? { opacity: 1, y: 0 } : { opacity: 0, y }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </Comp>
  );
}
