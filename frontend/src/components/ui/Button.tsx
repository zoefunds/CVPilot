import Link from "next/link";
import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const sizes: Record<Size, string> = {
  sm: "px-4 py-2 text-[13px]",
  md: "px-6 py-3 text-[14px]",
  lg: "px-8 py-3.5 text-[15px]",
};

const variants: Record<Variant, string> = {
  primary:
    "bg-[#1c1c17] text-white shadow-lg shadow-[#1c1c17]/15 hover:bg-[#332f28]",
  secondary:
    "border border-[#cdc5bc] bg-white text-[#1c1c17] hover:bg-[#fcf9f1]",
  ghost:
    "text-[#4b463f] hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]",
  danger:
    "bg-red-600 text-white shadow-lg shadow-red-600/20 hover:bg-red-700",
};

const baseClasses =
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60";

type SharedProps = {
  variant?: Variant;
  size?: Size;
  className?: string;
  children?: ReactNode;
};

type ButtonAsButton = SharedProps &
  ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined };

type ButtonAsLink = SharedProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & { href: string };

type ButtonProps = ButtonAsButton | ButtonAsLink;

export function Button(props: ButtonProps) {
  const {
    variant = "primary",
    size = "md",
    className = "",
    children,
    ...rest
  } = props;
  const merged = [baseClasses, sizes[size], variants[variant], className].join(" ");

  if ("href" in props && props.href) {
    const { href, ...anchorRest } = rest as ButtonAsLink;
    return (
      <Link href={href} className={merged} {...anchorRest}>
        {children}
      </Link>
    );
  }

  return (
    <button {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)} className={merged}>
      {children}
    </button>
  );
}
