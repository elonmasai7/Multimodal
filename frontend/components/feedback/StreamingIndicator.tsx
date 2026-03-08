"use client";

import { useSpring, animated } from "@react-spring/web";

export function StreamingIndicator({ active }: { active: boolean }) {
  const styles = useSpring({
    opacity: active ? 1 : 0.35,
    transform: active ? "scale(1)" : "scale(0.94)",
    config: { tension: 170, friction: 18 }
  });

  return (
    <animated.div style={styles} className="inline-flex items-center gap-2 rounded-full border border-cyan-200/40 px-3 py-1 text-xs text-cyan-100">
      <span className="h-2 w-2 rounded-full bg-cyan-300" />
      {active ? "Streaming live" : "Idle"}
    </animated.div>
  );
}
