import { forwardRef, type InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className = "", ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      {...rest}
      className={[
        "w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3",
        "text-[15px] text-[#1c1c17] placeholder:text-[#a8a298]",
        "transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      ].join(" ")}
    />
  );
});
