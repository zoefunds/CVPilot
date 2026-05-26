import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement>;

/**
 * Animated shimmer placeholder. Compose with width/height utility classes.
 * Example: <Skeleton className="h-4 w-32" />
 */
export function Skeleton({ className = "", ...rest }: Props) {
  return (
    <div
      aria-hidden="true"
      className={[
        "animate-pulse rounded-lg bg-[#1c1c17]/8",
        className,
      ].join(" ")}
      {...rest}
    />
  );
}

/**
 * A vertical stack of skeleton rows for list placeholders.
 */
export function SkeletonRows({
  rows = 3,
  className = "",
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={["flex flex-col gap-3", className].join(" ")}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}
