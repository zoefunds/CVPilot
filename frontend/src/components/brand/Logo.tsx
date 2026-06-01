import type { SVGProps } from "react";

type LogoProps = SVGProps<SVGSVGElement> & {
  size?: number;
};

/**
 * CVPilot mark.
 * Dark checkmark with a paper plane folded into the apex.
 * Single colour by default; override via the `color` prop or className.
 */
export function LogoMark({ size = 32, color = "#1c1c17", ...rest }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="CVPilot"
      {...rest}
    >
      {/* Bold checkmark */}
      <path
        d="M8 34 L24 50 L56 14"
        stroke={color}
        strokeWidth={9}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Paper plane body */}
      <path
        d="M18 32 L42 22 L28 38 Z"
        fill="#f4f0e8"
      />
      {/* Plane fold */}
      <path
        d="M28 38 L32 44 L42 22 Z"
        fill="#cdc5bc"
      />
      {/* Plane outline */}
      <path
        d="M18 32 L42 22 L28 38 L32 44 L42 22"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

export function LogoWordmark({
  size = 32,
  tagline,
}: {
  size?: number;
  tagline?: string;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark size={size} />
      <div className="flex flex-col leading-none">
        <span
          className="text-[22px] font-bold tracking-tight text-[#1c1c17]"
          style={{ fontFamily: "Literata, serif" }}
        >
          CVPilot
        </span>
        {tagline ? (
          <span className="mt-0.5 text-[11px] font-medium uppercase tracking-[0.12em] text-[#7c766e]">
            {tagline}
          </span>
        ) : null}
      </div>
    </div>
  );
}
