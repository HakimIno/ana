import { motion } from "framer-motion";
import { JSX } from "react";

// Path traced directly from the original image
const LINE_PATH =
    "M399.6 3.7 Q347.4 26.1 310.1 75.0 Q272.8 123.9 281.7 177.2 Q290.6 230.6 328.6 261.2 Q366.6 291.8 346.0 330.0 Q325.5 368.3 279.2 378.0 Q232.8 387.7 190.9 361.5 Q149.0 335.4 170.2 272.0 Q191.3 208.6 183.3 188.6 Q175.3 168.7 200.0 161.8 Q224.7 154.9 221.7 142.0 Q218.7 129.1 195.4 138.0 Q172.0 147.0 170.4 126.8 Q168.7 106.7 164.4 131.7 Q160.1 156.7 134.6 158.0 Q109.0 159.3 112.5 137.9 Q116.0 116.4 76.9 117.0 Q37.8 117.5 19.4 164.2 Q1.1 210.8 18.9 169.4 Q36.7 128.0 34.1 163.4 Q31.5 198.9 51.4 159.2 Q71.2 119.4 65.2 157.4 Q59.3 195.5 84.5 160.2 Q109.7 125.0 94.4 165.5 Q79.0 206.0 114.0 182.6 Q149.0 159.3 128.8 184.5 Q108.6 209.7 126.4 225.8 Q144.2 241.8 156.8 230.4 Q169.4 219.0 167.2 199.8 Q165.0 180.6 173.9 186.8 Q182.8 192.9 162.0 272.6 Q141.2 352.2 188.1 375.5 Q235.0 398.9 281.9 390.3 Q328.8 381.7 350.3 361.0 Q371.8 340.3 376.1 312.8 Q380.4 285.4 341.2 254.6 Q302.1 223.9 292.1 176.2 Q282.1 128.4 340.8 66.0 Z";

// Circle: cx=173.9 cy=63.4 r=48.2 (terracotta)
const CIRCLE = { cx: 173.9, cy: 63.4, r: 42 };

interface BrainFlowProps {
    size?: number;
}

export default function BrainFlow({ size = 120 }: BrainFlowProps): JSX.Element {
    return (
        <div className="brainflow-container">
            <svg
                width={size}
                height={size}
                viewBox="0 0 400 400"
                fill="none"
            >
                <defs>
                    {/* Dash animation: moving highlight along the path */}
                    <style>{`
            @keyframes flow {
              from { stroke-dashoffset: 3000; }
              to   { stroke-dashoffset: 0; }
            }
            @keyframes flowReverse {
              from { stroke-dashoffset: 0; }
              to   { stroke-dashoffset: -3000; }
            }
            @keyframes pulse {
              0%, 100% { r: 42; opacity: 0.95; }
              50%       { r: 46; opacity: 1; }
            }
            @keyframes ringPulse {
              0%   { r: 42; opacity: 0.5; stroke-width: 3; }
              100% { r: 90; opacity: 0; stroke-width: 1; }
            }
          `}</style>

                    <filter id="glow-white" x="-30%" y="-30%" width="160%" height="160%">
                        <feGaussianBlur stdDeviation="6" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>

                    <filter id="glow-dot" x="-60%" y="-60%" width="220%" height="220%">
                        <feGaussianBlur stdDeviation="10" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>

                    {/* Gradient for the flowing highlight */}
                    <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="white" stopOpacity="0" />
                        <stop offset="50%" stopColor="white" stopOpacity="1" />
                        <stop offset="100%" stopColor="white" stopOpacity="0" />
                    </linearGradient>
                </defs>

                {/* ── 1. Base line — dim static ── */}
                <motion.path
                    d={LINE_PATH}
                    stroke="currentColor"
                    strokeOpacity={0.12}
                    strokeWidth={14}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 2.4, ease: [0.4, 0, 0.2, 1] }}
                />

                {/* ── 2. Brighter inner line ── */}
                <motion.path
                    d={LINE_PATH}
                    stroke="currentColor"
                    strokeOpacity={0.4}
                    strokeWidth={4}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 2.6, ease: [0.4, 0, 0.2, 1], delay: 0.2 }}
                />

                {/* ── 3. Moving glow pulse ── */}
                <path
                    d={LINE_PATH}
                    stroke="currentColor"
                    strokeWidth={8}
                    strokeLinecap="round"
                    fill="none"
                    strokeDasharray="140 3000"
                    style={{
                        animation: "flow 4s linear infinite",
                        filter: "blur(4px)", // Simple glow for better theme compatibility
                        opacity: 0.8,
                    }}
                />

                {/* Second pulse ── */}
                <path
                    d={LINE_PATH}
                    stroke="currentColor"
                    strokeWidth={5}
                    strokeLinecap="round"
                    fill="none"
                    strokeDasharray="80 3000"
                    style={{
                        animation: "flow 4s linear infinite",
                        animationDelay: "-2s",
                        filter: "blur(2px)",
                        opacity: 0.5,
                    }}
                />

                {/* Terracotta pulse — slower ── */}
                <path
                    d={LINE_PATH}
                    stroke="#c1705a"
                    strokeWidth={7}
                    strokeLinecap="round"
                    fill="none"
                    strokeDasharray="100 3000"
                    style={{
                        animation: "flow 6s linear infinite",
                        animationDelay: "-1s",
                        opacity: 0.7,
                    }}
                />

                {/* ── 4. Terracotta circle ── */}
                <motion.circle
                    cx={CIRCLE.cx}
                    cy={CIRCLE.cy}
                    r={CIRCLE.r}
                    fill="#c1705a"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.7, delay: 0.8, ease: [0.34, 1.56, 0.64, 1] }}
                    style={{ originX: `${CIRCLE.cx}px`, originY: `${CIRCLE.cy}px` }}
                />

                {/* Expanding rings */}
                <circle
                    cx={CIRCLE.cx}
                    cy={CIRCLE.cy}
                    r={CIRCLE.r}
                    fill="none"
                    stroke="#c1705a"
                    style={{ animation: "ringPulse 3s ease-out infinite", animationDelay: "1s" }}
                />
                <circle
                    cx={CIRCLE.cx}
                    cy={CIRCLE.cy}
                    r={CIRCLE.r}
                    fill="none"
                    stroke="#c1705a"
                    style={{ animation: "ringPulse 3s ease-out infinite", animationDelay: "2.5s" }}
                />
            </svg>
        </div>
    );
}