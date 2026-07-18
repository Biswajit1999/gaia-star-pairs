import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  return reduced;
}

function DemandClock({ active }) {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    invalidate();
    if (!active) return undefined;
    const timer = window.setInterval(invalidate, 1000 / 20);
    return () => window.clearInterval(timer);
  }, [active, invalidate]);

  return null;
}

function StarField() {
  const positions = useMemo(() => {
    const points = new Float32Array(150 * 3);
    for (let index = 0; index < 150; index += 1) {
      const phase = index * 2.399963;
      const radius = 5 + (index % 19) * 0.22;
      points[index * 3] = Math.cos(phase) * radius;
      points[index * 3 + 1] = ((index * 37) % 83) / 8 - 5;
      points[index * 3 + 2] = Math.sin(phase) * radius - 1;
    }
    return points;
  }, []);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#ead79a" size={0.035} sizeAttenuation transparent opacity={0.72} />
    </points>
  );
}

function SolarCells() {
  const cells = [];
  for (let index = 0; index < 12; index += 1) {
    const angle = (index / 12) * Math.PI * 2;
    cells.push(
      <mesh key={index} position={[Math.cos(angle) * 1.1, -0.075, Math.sin(angle) * 1.1]} rotation={[0, -angle, 0]}>
        <boxGeometry args={[0.48, 0.025, 1.25]} />
        <meshStandardMaterial color={index % 2 === 0 ? '#4a3514' : '#65471b'} metalness={0.62} roughness={0.34} />
      </mesh>,
    );
  }
  return <group>{cells}</group>;
}

function GaiaDisc({ animate }) {
  const satellite = useRef(null);

  useFrame(({ clock }) => {
    if (!satellite.current || !animate) return;
    const elapsed = clock.getElapsedTime();
    satellite.current.rotation.y = elapsed * 0.12;
    satellite.current.position.y = Math.sin(elapsed * 0.55) * 0.07;
  });

  return (
    <group ref={satellite} rotation={[0.05, 0, -0.07]}>
      <mesh>
        <cylinderGeometry args={[2.05, 2.05, 0.09, 48]} />
        <meshStandardMaterial color="#a77b2f" metalness={0.72} roughness={0.3} />
      </mesh>
      <SolarCells />
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[2.02, 0.055, 8, 48]} />
        <meshStandardMaterial color="#d5b76c" metalness={0.78} roughness={0.24} />
      </mesh>
      <mesh position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.56, 0.7, 0.95, 12]} />
        <meshStandardMaterial color="#d5d0c2" metalness={0.5} roughness={0.43} />
      </mesh>
      <mesh position={[0, 1.02, 0]}>
        <cylinderGeometry args={[0.48, 0.48, 0.12, 12]} />
        <meshStandardMaterial color="#6f685b" metalness={0.65} roughness={0.3} />
      </mesh>
      <group position={[0.18, 0.92, 0]} rotation={[0, -0.35, Math.PI / 2]}>
        <mesh position={[0, 0.42, 0.24]}>
          <cylinderGeometry args={[0.18, 0.24, 0.75, 12]} />
          <meshStandardMaterial color="#272b31" metalness={0.55} roughness={0.34} />
        </mesh>
        <mesh position={[0, 0.42, -0.24]}>
          <cylinderGeometry args={[0.18, 0.24, 0.75, 12]} />
          <meshStandardMaterial color="#272b31" metalness={0.55} roughness={0.34} />
        </mesh>
      </group>
      <mesh position={[0, 0.12, 0]}>
        <cylinderGeometry args={[0.25, 0.25, 0.25, 12]} />
        <meshStandardMaterial color="#514731" metalness={0.62} roughness={0.33} />
      </mesh>
    </group>
  );
}

export default function GaiaHero() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="gaia-canvas" role="img" aria-label="Procedural low-poly illustration of a Gaia-like spinning survey satellite">
      <Canvas
        camera={{ position: [4.9, 3.3, 5.7], fov: 37 }}
        dpr={[1, 1.35]}
        frameloop="demand"
        gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }}
      >
        <ambientLight intensity={1.25} />
        <directionalLight position={[4, 6, 3]} intensity={3.2} color="#fff1c6" />
        <pointLight position={[-4, 1, -2]} intensity={18} color="#a06c20" />
        <StarField />
        <GaiaDisc animate={!reducedMotion} />
        <DemandClock active={!reducedMotion} />
      </Canvas>
    </div>
  );
}
