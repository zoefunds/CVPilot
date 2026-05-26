import type { SVGProps } from "react";

export type IconName =
  | "verified"
  | "check"
  | "bolt"
  | "spark"
  | "filter"
  | "analytics"
  | "edit"
  | "shield_check"
  | "psychology"
  | "send"
  | "grid"
  | "plus"
  | "settings"
  | "logout"
  | "menu"
  | "wallet"
  | "document"
  | "chevron_right";

type Props = Omit<SVGProps<SVGSVGElement>, "name"> & {
  name: IconName;
  size?: number;
};

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  viewBox: "0 0 24 24",
};

export function Icon({ name, size = 20, ...rest }: Props) {
  switch (name) {
    case "verified":
    case "check":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <circle cx="12" cy="12" r="10" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case "bolt":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" fill="currentColor" />
        </svg>
      );
    case "spark":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="m12 3 1.6 4.8L18 9l-4.4 1.2L12 15l-1.6-4.8L6 9l4.4-1.2L12 3z" fill="currentColor" />
          <path d="M19 14v4M17 16h4M5 17v3M3.5 18.5h3" />
        </svg>
      );
    case "filter":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M22 3H2l8 9.5V19l4 2v-8.5L22 3z" />
        </svg>
      );
    case "analytics":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <line x1="6" y1="20" x2="6" y2="14" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="3" y1="20" x2="21" y2="20" />
        </svg>
      );
    case "edit":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
      );
    case "shield_check":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case "psychology":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 0 4 3 3 0 0 0 3 3 3 3 0 0 0 5 1 3 3 0 0 0 5-1 3 3 0 0 0 3-3 3 3 0 0 0 0-4 3 3 0 0 0-2-5 3 3 0 0 0-3-3 3 3 0 0 0-3 1 3 3 0 0 0-3-1z" />
          <path d="M12 8v6" />
          <path d="M10 11h4" />
        </svg>
      );
    case "send":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M22 2 11 13" />
          <path d="M22 2 15 22 11 13 2 9z" />
        </svg>
      );
    case "grid":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      );
    case "plus":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M12 5v14M5 12h14" />
        </svg>
      );
    case "settings":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      );
    case "logout":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="m16 17 5-5-5-5" />
          <path d="M21 12H9" />
        </svg>
      );
    case "menu":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M3 6h18M3 12h18M3 18h18" />
        </svg>
      );
    case "wallet":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M3 6a2 2 0 0 1 2-2h13" />
          <path d="M3 6v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8a1 1 0 0 0-1-1H4a1 1 0 0 1-1-1z" />
          <circle cx="17" cy="14" r="1.3" fill="currentColor" />
        </svg>
      );
    case "document":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
          <polyline points="14 3 14 9 20 9" />
          <line x1="8" y1="13" x2="16" y2="13" />
          <line x1="8" y1="17" x2="14" y2="17" />
        </svg>
      );
    case "chevron_right":
      return (
        <svg width={size} height={size} {...base} {...rest}>
          <polyline points="9 18 15 12 9 6" />
        </svg>
      );
    default:
      return null;
  }
}
