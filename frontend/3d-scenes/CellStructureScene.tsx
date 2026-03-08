"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

export function CellStructureScene() {
  return (
    <div className="h-[320px] w-full rounded-2xl border border-white/20 bg-slate-950/80">
      <Canvas camera={{ position: [0, 0, 6] }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[0, 3, 4]} intensity={1.4} />
        <mesh>
          <sphereGeometry args={[2, 48, 48]} />
          <meshStandardMaterial color="#2ec4b6" transparent opacity={0.35} />
        </mesh>
        <mesh position={[0.6, 0.4, 0.6]}>
          <sphereGeometry args={[0.8, 32, 32]} />
          <meshStandardMaterial color="#ff006e" emissive="#ff4d8d" emissiveIntensity={0.25} />
        </mesh>
        <mesh position={[-0.8, -0.4, 0.2]}>
          <sphereGeometry args={[0.45, 32, 32]} />
          <meshStandardMaterial color="#ffd166" emissive="#ffd166" emissiveIntensity={0.16} />
        </mesh>
        <OrbitControls />
      </Canvas>
    </div>
  );
}
