"use client";

import { useSpring, animated } from "@react-spring/web";

export function AudioVisualizer({ active }: { active: boolean }) {
  const props = useSpring({
    from: { scale: 0.95, opacity: 0.4 },
    to: { scale: active ? 1.05 : 0.95, opacity: active ? 1 : 0.4 },
    loop: active,
    config: { tension: 120, friction: 18 }
  });

  return (
    <animated.div style={props} className="h-8 w-24 rounded-full bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-amber-300" />
  );
}
