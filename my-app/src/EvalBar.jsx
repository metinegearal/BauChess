import React from "react";

export default function EvalBar({ evaluation }) {
  // Clamp eval to prevent overflow in extreme cases
  const clamped = Math.max(-1000, Math.min(1000, evaluation || 0));
  const whitePercent = ((clamped + 1000) / 2000) * 100; // 0–100%

  // Format for readability: convert centipawns to pawns
  const displayEval =
    Math.abs(evaluation) > 10000
      ? (evaluation > 0 ? "M" + (100000 - evaluation) / 10000 : "-M" + (100000 + evaluation) / 10000)
      : (evaluation / 100).toFixed(2);

  return (
    <div
      style={{
        position: "relative",
        width: "40px",
        height: "700px",
        border: "1px solid #999",
        borderRadius: "4px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#000",
      }}
    >
      {/* White portion */}
      <div
        style={{
          backgroundColor: "#fff",
          height: `${whitePercent}%`,
          transition: "height 0.3s ease-in-out",
        }}
      />

      {/* Centered Eval Text */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          fontSize: "14px",
          fontWeight: "bold",
          color: whitePercent > 50 ? "#000" : "#fff",
          textShadow: "0 0 3px rgba(0,0,0,0.4)",
          userSelect: "none",
        }}
      >
        {displayEval}
      </div>
    </div>
  );
}
