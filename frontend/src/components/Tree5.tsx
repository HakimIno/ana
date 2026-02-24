import { motion, useAnimation } from "framer-motion";
import { useEffect } from "react";

type AnimationControls = ReturnType<typeof useAnimation>;

interface Flower {
    x: number;
    groundY: number;
    height: number;
    scale: number;
}

interface FlowerPaths {
    ground: string;
    stem: string;
    leafL: string;
    leafR: string;
    fcx: number;
    fcy: number;
    fr: number;
    petalPaths: string[];
}

interface FlowerControls {
    ground: AnimationControls;
    stem: AnimationControls;
    leafL: AnimationControls;
    leafR: AnimationControls;
    flower: AnimationControls;
    petals: AnimationControls[];
}

// 5 flowers at different positions/sizes across the field
const FLOWERS: Flower[] = [
    { x: 18, groundY: 88, height: 22, scale: 0.75 },
    { x: 38, groundY: 90, height: 30, scale: 1.0 },
    { x: 58, groundY: 89, height: 26, scale: 0.88 },
    { x: 75, groundY: 91, height: 18, scale: 0.65 },
    { x: 90, groundY: 88, height: 28, scale: 0.95 },
];

function buildFlowerPaths(flower: Flower): FlowerPaths {
    const { x, groundY, height, scale } = flower;
    const s = scale;
    const topY = groundY - height;

    // Ground mound
    const ground = `M${x - 7 * s} ${groundY} Q${x} ${groundY - 5 * s} ${x + 7 * s} ${groundY}`;

    // Stem — slight natural curve
    const stem = `M${x} ${groundY - 1} C${x - 1} ${groundY - height * 0.5} ${x + 1} ${groundY - height * 0.7} ${x} ${topY + 2}`;

    // Left leaf
    const leafL = `M${x - 1} ${groundY - height * 0.55} C${x - 9 * s} ${groundY - height * 0.65} ${x - 13 * s} ${groundY - height * 0.5} ${x - 11 * s} ${groundY - height * 0.38} C${x - 6 * s} ${groundY - height * 0.42} ${x - 1} ${groundY - height * 0.55} Z`;

    // Right leaf
    const leafR = `M${x + 1} ${groundY - height * 0.7} C${x + 8 * s} ${groundY - height * 0.8} ${x + 12 * s} ${groundY - height * 0.68} ${x + 10 * s} ${groundY - height * 0.56} C${x + 5 * s} ${groundY - height * 0.6} ${x + 1} ${groundY - height * 0.7} Z`;

    // Flower center circle
    const fcx = x, fcy = topY;
    const fr = 4 * s;

    // 6 petals
    const petalAngles = [270, 330, 30, 90, 150, 210];
    const petalPaths = petalAngles.map((angle) => {
        const rad = (angle * Math.PI) / 180;
        const pcx = fcx + Math.cos(rad) * (fr + 2 * s) * 1.6;
        const pcy = fcy + Math.sin(rad) * (fr + 2 * s) * 1.6;
        const r1 = 3.2 * s, r2 = 1.8 * s;
        const cos = Math.cos(rad), sin = Math.sin(rad);
        const ax = (pcx + cos * r1).toFixed(2);
        const ay = (pcy + sin * r1).toFixed(2);
        const bx = (pcx - sin * r2).toFixed(2);
        const by = (pcy + cos * r2).toFixed(2);
        const q1x = (pcx + cos * r1 * 0.4 - sin * r2 * 1.2).toFixed(2);
        const q1y = (pcy + sin * r1 * 0.4 + cos * r2 * 1.2).toFixed(2);
        const q2x = (pcx - cos * r1 * 0.4 - sin * r2 * 0.6).toFixed(2);
        const q2y = (pcy - sin * r1 * 0.4 + cos * r2 * 0.6).toFixed(2);
        return `M${ax} ${ay} Q${q1x} ${q1y} ${bx} ${by} Q${q2x} ${q2y} ${ax} ${ay}`;
    });

    return { ground, stem, leafL, leafR, fcx, fcy, fr, petalPaths };
}

function FlowerInstance({ paths, animCtrl }: { paths: FlowerPaths, animCtrl: FlowerControls }) {
    const { ground, stem, leafL, leafR, fcx, fcy, fr, petalPaths } = paths;
    const STROKE = { stroke: "white", strokeLinecap: "round", strokeLinejoin: "round", fill: "transparent" } as const;

    return (
        <g>
            <motion.path d={ground} {...STROKE} strokeWidth="1.6" animate={animCtrl.ground} initial={{ pathLength: 0, opacity: 0 }} />
            <motion.path d={stem}   {...STROKE} strokeWidth="1.5" animate={animCtrl.stem} initial={{ pathLength: 0, opacity: 0 }} />
            <motion.path d={leafL}  {...STROKE} strokeWidth="1.3" animate={animCtrl.leafL} initial={{ pathLength: 0, opacity: 0 }} />
            <motion.path d={leafR}  {...STROKE} strokeWidth="1.3" animate={animCtrl.leafR} initial={{ pathLength: 0, opacity: 0 }} />
            <motion.circle cx={fcx} cy={fcy} r={fr} stroke="white" strokeWidth="1.5" fill="transparent"
                animate={animCtrl.flower} initial={{ pathLength: 0, opacity: 0 }} />
            {petalPaths.map((d, i) => (
                <motion.path key={i} d={d} stroke="white" strokeWidth="1.3"
                    strokeLinecap="round" strokeLinejoin="round" fill="transparent"
                    animate={animCtrl.petals[i]} initial={{ pathLength: 0, opacity: 0 }} />
            ))}
        </g>
    );
}

function useFlowerControls(): FlowerControls {
    return {
        ground: useAnimation(),
        stem: useAnimation(),
        leafL: useAnimation(),
        leafR: useAnimation(),
        flower: useAnimation(),
        petals: [useAnimation(), useAnimation(), useAnimation(), useAnimation(), useAnimation(), useAnimation()],
    };
}

const DRAW_EASE = [0.4, 0, 0.2, 1] as const;
const ERASE_EASE = [0.6, 0, 0.4, 1] as const;

function draw(ctrl: AnimationControls, dur: number, delay = 0) {
    return ctrl.start({
        pathLength: 1,
        opacity: 1,
        transition: { duration: dur, delay, ease: DRAW_EASE as any }
    });
}
function erase(ctrl: AnimationControls, dur: number, delay = 0) {
    return ctrl.start({
        pathLength: 0,
        transition: { duration: dur, delay, ease: ERASE_EASE as any }
    });
}
function reset(ctrl: AnimationControls) { ctrl.set({ pathLength: 0, opacity: 0 }); }

function drawFlower(c: FlowerControls, baseDelay: number) {
    const d = baseDelay;
    draw(c.ground, 0.3, d);
    draw(c.stem, 0.5, d + 0.3);
    draw(c.leafL, 0.4, d + 0.8);
    draw(c.leafR, 0.4, d + 1.2);
    draw(c.flower, 0.45, d + 1.6);
    c.petals.forEach((p, i) => draw(p, 0.18, d + 2.05 + i * 0.18));
}

async function eraseFlower(c: FlowerControls, waitBefore: number) {
    await new Promise(r => setTimeout(r, waitBefore));
    for (let i = 5; i >= 0; i--) {
        erase(c.petals[i], 0.14);
        await new Promise(r => setTimeout(r, 130));
    }
    erase(c.flower, 0.3);
    await new Promise(r => setTimeout(r, 320));
    erase(c.leafR, 0.3);
    await new Promise(r => setTimeout(r, 310));
    erase(c.leafL, 0.3);
    await new Promise(r => setTimeout(r, 310));
    erase(c.stem, 0.4);
    await new Promise(r => setTimeout(r, 420));
    erase(c.ground, 0.25);
    await new Promise(r => setTimeout(r, 350));
}

export default function FlowerField() {
    const allPaths = FLOWERS.map(buildFlowerPaths);

    // Must call hooks unconditionally at top level
    const controls: FlowerControls[] = [
        useFlowerControls(),
        useFlowerControls(),
        useFlowerControls(),
        useFlowerControls(),
        useFlowerControls()
    ];

    useEffect(() => {
        const loop = async () => {
            while (true) {
                // Reset all
                controls.forEach(c => {
                    reset(c.ground); reset(c.stem); reset(c.leafL); reset(c.leafR); reset(c.flower);
                    c.petals.forEach(reset);
                });
                await new Promise(r => setTimeout(r, 400));

                // Draw one by one — each flower starts after previous finishes (~3.2s each)
                const perFlower = 3.2;
                controls.forEach((c, i) => drawFlower(c, i * perFlower));

                // Wait until all drawn + hold pause
                const totalDraw = (controls.length * perFlower + 1.2) * 1000;
                await new Promise(r => setTimeout(r, totalDraw + 2000));

                // Erase in reverse order — last flower first
                for (let i = controls.length - 1; i >= 0; i--) {
                    await eraseFlower(controls[i], 0);
                }
                await new Promise(r => setTimeout(r, 500));
            }
        };
        loop();
    }, [controls]);

    return (
        <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "100%", height: "100%", background: "transparent",
        }}>
            <svg width="100%" height="100%" viewBox="0 0 110 100"
                preserveAspectRatio="xMidYMid meet"
                style={{ maxWidth: 700, maxHeight: 420 }}>
                {allPaths.map((paths, i) => (
                    <FlowerInstance key={i} paths={paths} animCtrl={controls[i]} />
                ))}
            </svg>
        </div>
    );
}