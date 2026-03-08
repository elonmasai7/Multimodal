"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

function Atom({ position, color }: { position: [number, number, number]; color: string }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.4, 32, 32]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.25} />
    </mesh>
  );
}

export function MoleculeViewer() {
  return (
    <div className="h-[320px] w-full rounded-2xl border border-white/20 bg-slate-950/80">
      <Canvas camera={{ position: [0, 0, 6] }}>
        <ambientLight intensity={0.45} />
        <pointLight position={[2, 2, 2]} intensity={1.2} />
        <Atom position={[-1, 0, 0]} color="#80ed99" />
        <Atom position={[1, 0, 0]} color="#4cc9f0" />
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.08, 0.08, 2, 24]} />
          <meshStandardMaterial color="#f8fafc" />
        </mesh>
        <OrbitControls />
      </Canvas>
    </div>
  );
}
