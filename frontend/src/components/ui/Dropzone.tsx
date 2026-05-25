'use client';

import { DragEvent, useId, useRef, useState } from 'react';

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
  accept = '.pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain',
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
      <label
        htmlFor={id}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={handleDrop}
        className={[
          'flex cursor-pointer flex-col items-start gap-2 rounded-2xl border border-dashed px-5 py-6 transition-colors',
          over
            ? 'border-[#2b4f3a] bg-[#2b4f3a]/5'
            : 'border-[#1a1814]/25 bg-white/40 hover:bg-white/60',
          disabled ? 'pointer-events-none opacity-60' : '',
        ].join(' ')}
      >
        <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
          {label}
        </span>
        {file ? (
          <div className="flex w-full items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate font-medium text-[#1a1814]">{file.name}</p>
              <p className="text-xs text-[#3a342c]/70">
                {formatBytes(file.size)} · {file.type || 'unknown type'}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                onFile(null);
                if (ref.current) ref.current.value = '';
              }}
              className="rounded-full border border-[#1a1814]/30 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
            >
              Replace
            </button>
          </div>
        ) : (
          <div>
            <p className="text-[#1a1814]">
              Drop a file here, or click to choose.
            </p>
            <p className="mt-1 text-xs text-[#3a342c]/70">
              {helperText || 'PDF, DOCX, or TXT. Up to 10 MB.'}
            </p>
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
