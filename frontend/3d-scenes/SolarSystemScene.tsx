"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";

function Planet({ radius, color, orbitRadius, speed }: { radius: number; color: string; orbitRadius: number; speed: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const angleRef = useRef(Math.random() * Math.PI * 2);

  useFrame((_, delta) => {
    angleRef.current += delta * speed;
    const x = Math.cos(angleRef.current) * orbitRadius;
    const z = Math.sin(angleRef.current) * orbitRadius;
    if (meshRef.current) {
      meshRef.current.position.set(x, 0, z);
      meshRef.current.rotation.y += delta;
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.22} />
    </mesh>
  );
}

export function SolarSystemScene() {
  const planets = useMemo(
    () => [
      { radius: 0.35, color: "#90e0ef", orbitRadius: 2.5, speed: 1.2 },
      { radius: 0.48, color: "#ffd166", orbitRadius: 4, speed: 0.8 },
      { radius: 0.42, color: "#ff6b6b", orbitRadius: 5.7, speed: 0.6 }
    ],
    []
  );

  return (
    <div className="h-[380px] w-full rounded-2xl border border-white/20 bg-slate-950/80">
      <Canvas camera={{ position: [0, 4, 9], fov: 55 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[0, 0, 0]} intensity={2.4} color="#ffad33" />
        <mesh>
          <sphereGeometry args={[1, 64, 64]} />
          <meshStandardMaterial color="#fca311" emissive="#ffba08" emissiveIntensity={0.9} />
        </mesh>
        {planets.map((planet) => (
          <Planet key={planet.orbitRadius} {...planet} />
        ))}
        <Stars radius={50} depth={30} count={1800} factor={3} />
        <OrbitControls enablePan={false} />
      </Canvas>
    </div>
  );
}
