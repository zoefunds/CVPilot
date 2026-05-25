import { forwardRef, InputHTMLAttributes } from 'react';

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(function Input({ className = '', ...rest }, ref) {
  const base =
    'w-full rounded-2xl border border-[#1a1814]/15 bg-white/60 px-4 py-3 text-[#1a1814] placeholder:text-[#3a342c]/50 outline-none transition-colors focus:border-[#2b4f3a] focus:bg-white disabled:opacity-60';
  return <input ref={ref} className={`${base} ${className}`} {...rest} />;
});
