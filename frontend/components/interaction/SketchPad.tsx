"use client";

import { useEffect, useRef, useState } from "react";

function getBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("Canvas is empty"))), "image/png")
  );
}

export function SketchPad() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const lastPos = useRef<{ x: number; y: number } | null>(null);
  const [color, setColor] = useState("#67e8f9");
  const [size, setSize] = useState(3);
  const [erasing, setErasing] = useState(false);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, []);

  function flash(msg: string) {
    setStatus(msg);
    setTimeout(() => setStatus(""), 2500);
  }

  function getPos(e: React.MouseEvent | React.TouchEvent) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    if ("touches" in e) {
      const t = e.touches[0];
      return { x: (t.clientX - rect.left) * scaleX, y: (t.clientY - rect.top) * scaleY };
    }
    return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
  }

  function startDraw(e: React.MouseEvent | React.TouchEvent) {
    drawing.current = true;
    lastPos.current = getPos(e);
  }

  function draw(e: React.MouseEvent | React.TouchEvent) {
    if (!drawing.current) return;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const pos = getPos(e);
    const from = lastPos.current ?? pos;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(pos.x, pos.y);
    ctx.strokeStyle = erasing ? "#0f172a" : color;
    ctx.lineWidth = erasing ? size * 4 : size;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
    lastPos.current = pos;
  }

  function stopDraw() {
    drawing.current = false;
    lastPos.current = null;
  }

  function clear() {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function download() {
    const canvas = canvasRef.current!;
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = `sketch-${Date.now()}.png`;
    a.click();
  }

  async function copyToClipboard() {
    try {
      const blob = await getBlob(canvasRef.current!);
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
      flash("Copied! Paste into Notion, Google Docs, or anywhere.");
    } catch {
      flash("Copy failed — try downloading instead.");
    }
  }

  async function share() {
    try {
      const blob = await getBlob(canvasRef.current!);
      const file = new File([blob], "sketch.png", { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: "My Sketch Notes" });
      } else {
        // Fallback: download
        download();
        flash("Shared as download.");
      }
    } catch {
      // user cancelled or not supported
    }
  }

  const colors = ["#67e8f9", "#ffffff", "#fbbf24", "#34d399", "#f87171", "#a78bfa"];

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3 space-y-2">
      {/* Top toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Sketch Notes</p>
        <div className="flex flex-wrap items-center gap-1.5">
          {colors.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => { setColor(c); setErasing(false); }}
              className={`h-4 w-4 rounded-full border-2 transition-transform ${color === c && !erasing ? "border-white scale-125" : "border-transparent"}`}
              style={{ backgroundColor: c }}
            />
          ))}
          <button
            type="button"
            onClick={() => setErasing((v) => !v)}
            className={`rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors ${erasing ? "bg-white text-slate-900" : "bg-white/10 text-slate-300 hover:bg-white/20"}`}
          >
            Erase
          </button>
          <input
            type="range"
            min={1}
            max={12}
            value={size}
            onChange={(e) => setSize(Number(e.target.value))}
            className="w-14 accent-cyan-400"
          />
          <button
            type="button"
            onClick={clear}
            className="rounded px-1.5 py-0.5 text-[10px] font-medium bg-white/10 text-slate-300 hover:bg-red-500/30 hover:text-red-300 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={600}
        height={300}
        className="w-full rounded-xl cursor-crosshair touch-none"
        style={{ imageRendering: "pixelated" }}
        onMouseDown={startDraw}
        onMouseMove={draw}
        onMouseUp={stopDraw}
        onMouseLeave={stopDraw}
        onTouchStart={startDraw}
        onTouchMove={draw}
        onTouchEnd={stopDraw}
      />

      {/* Bottom action bar */}
      <div className="flex items-center justify-between gap-2 pt-1">
        <div className="flex gap-1.5">
          {/* Copy — paste into Notion / Google Docs */}
          <button
            type="button"
            onClick={copyToClipboard}
            className="flex items-center gap-1 rounded-lg bg-violet-500/20 px-2.5 py-1 text-xs font-medium text-violet-300 hover:bg-violet-500/30 transition-colors"
            title="Copy image — then paste directly into Notion or Google Docs"
          >
            <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h-1v1H2V6h1V5H2z"/>
            </svg>
            Copy for Notion / Docs
          </button>

          {/* Download PNG */}
          <button
            type="button"
            onClick={download}
            className="flex items-center gap-1 rounded-lg bg-cyan-500/20 px-2.5 py-1 text-xs font-medium text-cyan-300 hover:bg-cyan-500/30 transition-colors"
          >
            <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
            </svg>
            Download PNG
          </button>

          {/* Share (mobile native share) */}
          <button
            type="button"
            onClick={share}
            className="flex items-center gap-1 rounded-lg bg-emerald-500/20 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/30 transition-colors"
          >
            <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
              <path d="M13.5 1a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM11 2.5a2.5 2.5 0 1 1 .603 1.628l-6.718 3.12a2.499 2.499 0 0 1 0 1.504l6.718 3.12a2.5 2.5 0 1 1-.488.876l-6.718-3.12a2.5 2.5 0 1 1 0-3.256l6.718-3.12A2.5 2.5 0 0 1 11 2.5zm-8.5 4a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm11 5.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/>
            </svg>
            Share
          </button>
        </div>

        {/* Status feedback */}
        {status && (
          <p className="text-[10px] text-emerald-300 animate-pulse">{status}</p>
        )}
      </div>
    </div>
  );
}
