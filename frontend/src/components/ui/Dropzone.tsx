"use client";

import { DragEvent, useId, useRef, useState } from "react";
import { Icon } from "@/components/icons/Icon";

interface Props {
  label: string;
  accept?: string;
  file: File | null;
  onFile: (file: File | null) => void;
  disabled?: boolean;
  helperText?: string;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export function Dropzone({
  label,
  accept = ".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain",
  file,
  onFile,
  disabled,
  helperText,
}: Props) {
  const id = useId();
  const ref = useRef<HTMLInputElement | null>(null);
  const [over, setOver] = useState(false);

  function handleDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setOver(false);
    if (disabled) return;
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFile(dropped);
  }

  return (
    <div>
      <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
        {label}
      </span>
      <label
        htmlFor={id}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={handleDrop}
        className={[
          "mt-2 flex cursor-pointer flex-col items-stretch rounded-xl border-2 border-dashed px-5 py-5 transition-all",
          over
            ? "border-[#1c1c17] bg-[#1c1c17]/5"
            : "border-[#cdc5bc] bg-white hover:border-[#1c1c17]/40 hover:bg-[#fcf9f1]",
          disabled ? "pointer-events-none opacity-60" : "",
        ].join(" ")}
      >
        {file ? (
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1c1c17] text-white">
                <Icon name="document" size={18} />
              </span>
              <div className="min-w-0">
                <p className="truncate text-[14px] font-semibold text-[#1c1c17]">
                  {file.name}
                </p>
                <p className="truncate text-[12px] text-[#7c766e]">
                  {formatBytes(file.size)} · {file.type || "unknown"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                onFile(null);
                if (ref.current) ref.current.value = "";
              }}
              className="shrink-0 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1.5 text-[12px] font-medium text-[#4b463f] hover:bg-[#f1eee6] hover:text-[#1c1c17]"
            >
              Replace
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17]">
              <Icon name="plus" size={18} />
            </span>
            <div>
              <p className="text-[14px] font-medium text-[#1c1c17]">
                Drop a file here, or click to choose
              </p>
              <p className="mt-0.5 text-[12px] text-[#7c766e]">
                {helperText || "PDF, DOCX, or TXT. Up to 4 MiB."}
              </p>
            </div>
          </div>
        )}
        <input
          id={id}
          ref={ref}
          type="file"
          accept={accept}
          className="sr-only"
          disabled={disabled}
          onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        />
      </label>
    </div>
  );
}
