export function InputField({
  label,
  value,
  onChange,
  placeholder
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-xs uppercase tracking-[0.12em] text-slate-300">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/20 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-cyan-300"
      />
    </label>
  );
}
