"use client";

export function FileUploader() {
  return (
    <label className="block rounded-2xl border border-dashed border-white/25 bg-white/5 p-4 text-center text-sm text-slate-300">
      Upload worksheet or diagram
      <input type="file" className="hidden" />
    </label>
  );
}
