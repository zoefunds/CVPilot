import Link from 'next/link';
import { ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost';

const styles: Record<Variant, string> = {
  primary:
    'bg-[#1a1814] text-[#efece4] hover:bg-[#3a342c] focus-visible:outline-[#2b4f3a]',
  secondary:
    'bg-[#2b4f3a] text-[#efece4] hover:bg-[#1f3a2a] focus-visible:outline-[#1a1814]',
  ghost:
    'bg-transparent text-[#1a1814] border border-[#1a1814]/30 hover:bg-[#1a1814]/5',
};

const base =
  'inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:pointer-events-none';

export function Button({
  href,
  children,
  variant = 'primary',
  className = '',
  ...rest
}: {
  href?: string;
  children: ReactNode;
  variant?: Variant;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const cls = `${base} ${styles[variant]} ${className}`;
  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" className={cls} {...rest}>
      {children}
    </button>
  );
}
