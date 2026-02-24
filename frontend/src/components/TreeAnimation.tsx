import { motion, useAnimation } from "framer-motion";
import { useEffect } from "react";

const STROKE = {
    stroke: "white",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    fill: "transparent",
} as const;

export default function PlantDraw() {
    const ground = useAnimation();
    const stem = useAnimation();
    const leafL = useAnimation();
    const leafR = useAnimation();
    const leafS = useAnimation();
    const flower = useAnimation();
    const petals = [
        useAnimation(), useAnimation(), useAnimation(), useAnimation(),
        useAnimation(), useAnimation(), useAnimation(), useAnimation(),
    ];

    const drawPath = (ctrl, duration, delay = 0) =>
        ctrl.start({
            pathLength: 1,
            opacity: 1,
            transition: { duration, delay, ease: [0.4, 0, 0.2, 1] },
        });

    const erasePath = (ctrl, duration, delay = 0) =>
        ctrl.start({
            pathLength: 0,
            transition: { duration, delay, ease: [0.6, 0, 0.4, 1] },
        });

    const resetPath = (ctrl) => ctrl.set({ pathLength: 0, opacity: 1 });

    useEffect(() => {
        const loop = async () => {
            while (true) {
                // RESET all
                [ground, stem, leafL, leafR, leafS, flower, ...petals].forEach(resetPath);
                await new Promise((r) => setTimeout(r, 300));

                // DRAW forward — each starts after previous ends
                drawPath(ground, 0.45, 0);
                drawPath(stem, 0.7, 0.45);
                drawPath(leafL, 0.65, 1.15);
                drawPath(leafR, 0.65, 1.8);
                drawPath(leafS, 0.5, 2.45);
                drawPath(flower, 0.6, 2.95);
                petals.forEach((p, i) => drawPath(p, 0.22, 3.55 + i * 0.22));

                // Wait for all to finish + hold pause
                const totalDraw = (3.55 + 8 * 0.22) * 1000;
                await new Promise((r) => setTimeout(r, totalDraw + 1800));

                // ERASE in reverse — petals last-to-first, then upward
                for (let i = 7; i >= 0; i--) {
                    erasePath(petals[i], 0.18);
                    await new Promise((r) => setTimeout(r, 160));
                }
                erasePath(flower, 0.35);
                await new Promise((r) => setTimeout(r, 380));
                erasePath(leafS, 0.3);
                await new Promise((r) => setTimeout(r, 320));
                erasePath(leafR, 0.4);
                await new Promise((r) => setTimeout(r, 420));
                erasePath(leafL, 0.4);
                await new Promise((r) => setTimeout(r, 420));
                erasePath(stem, 0.5);
                await new Promise((r) => setTimeout(r, 520));
                erasePath(ground, 0.3);
                await new Promise((r) => setTimeout(r, 500));
            }
        };
        loop();
    }, []);

    // Build petal paths
    const petalAngles = [270, 315, 0, 45, 90, 135, 180, 225];
    const petalPaths = petalAngles.map((angle) => {
        const rad = (angle * Math.PI) / 180;
        const cx = 49 + Math.cos(rad) * 9;
        const cy = 42 + Math.sin(rad) * 9;
        const r1 = 3.5, r2 = 2.2;
        const cos = Math.cos(rad), sin = Math.sin(rad);
        const ax = (cx + cos * r1).toFixed(2);
        const ay = (cy + sin * r1).toFixed(2);
        const bx = (cx - sin * r2).toFixed(2);
        const by = (cy + cos * r2).toFixed(2);
        const q1x = (cx + cos * r1 * 0.5 - sin * r2).toFixed(2);
        const q1y = (cy + sin * r1 * 0.5 + cos * r2).toFixed(2);
        const q2x = (cx - cos * r1 * 0.5 - sin * r2 * 0.5).toFixed(2);
        const q2y = (cy - sin * r1 * 0.5 + cos * r2 * 0.5).toFixed(2);
        return `M${ax} ${ay} Q${q1x} ${q1y} ${bx} ${by} Q${q2x} ${q2y} ${ax} ${ay}`;
    });

    return (
        <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "100vw", height: "100vh", background: "#0c0c0c",
        }}>
            <svg width="320" height="320" viewBox="0 0 100 100" fill="none" style={{ overflow: "visible" }}>
                <motion.path d="M32 83 Q41 76 50 76 Q59 76 68 83"
                    {...STROKE} animate={ground} initial={{ pathLength: 0, opacity: 1 }} />
                <motion.path d="M50 76 C49 68 51 58 49 47"
                    {...STROKE} animate={stem} initial={{ pathLength: 0, opacity: 1 }} />
                <motion.path d="M48 66 C38 58 28 59 27 68 C27 68 36 73 48 66 Z"
                    {...STROKE} animate={leafL} initial={{ pathLength: 0, opacity: 1 }} />
                <motion.path d="M50 57 C58 49 69 49 71 58 C71 58 61 63 50 57 Z"
                    {...STROKE} animate={leafR} initial={{ pathLength: 0, opacity: 1 }} />
                <motion.path d="M48 52 C41 45 33 46 32 53 C32 53 39 56 48 52 Z"
                    {...STROKE} animate={leafS} initial={{ pathLength: 0, opacity: 1 }} />
                <motion.circle cx="49" cy="42" r="5"
                    stroke="white" strokeWidth="2" fill="transparent"
                    animate={flower} initial={{ pathLength: 0, opacity: 1 }} />
                {petalPaths.map((d, i) => (
                    <motion.path key={i} d={d}
                        stroke="white" strokeWidth="1.6" strokeLinecap="round"
                        strokeLinejoin="round" fill="transparent"
                        animate={petals[i]} initial={{ pathLength: 0, opacity: 1 }} />
                ))}
            </svg>
        </div>
    );
}