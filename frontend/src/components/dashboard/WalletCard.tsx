"use client";

import { useState } from "react";
import { ApiError, walletApi } from "@/lib/api";
import { useToast } from "@/contexts/ToastContext";
import { LOW_BALANCE_WEI, useWallet } from "@/contexts/WalletContext";
import { SendGenModal } from "@/components/dashboard/SendGenModal";
import { Icon } from "@/components/icons/Icon";
import { Skeleton } from "@/components/ui/Skeleton";

export function WalletCard({
  onActivityChanged,
}: {
  onActivityChanged?: () => void;
}) {
  const { wallet, isLoading, error, refresh } = useWallet();
  const [revealed, setRevealed] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [sendOpen, setSendOpen] = useState(false);
  const { push } = useToast();

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: "success", title: "Copied.", message: label });
    } catch {
      push({ tone: "error", title: "Could not copy." });
    }
  }

  async function exportKey() {
    if (revealed) {
      setRevealed(null);
      return;
    }
    setExporting(true);
    try {
      const x = await walletApi.export();
      setRevealed(x.private_key);
      push({
        tone: "info",
        title: "Private key revealed.",
        message: "Save it offline. CVPilot will never ask for it.",
      });
    } catch (e) {
      push({
        tone: "error",
        title: "Could not export.",
        message: e instanceof ApiError ? e.message : undefined,
      });
    } finally {
      setExporting(false);
    }
  }

  if (error && !wallet) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-[13px] text-red-800">
        {error}
      </div>
    );
  }

  if (!wallet) {
    return (
      <div className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 sm:p-7">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="mt-2 h-6 w-56" />
        <Skeleton className="mt-3 h-4 w-full max-w-md" />
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-white p-4">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="mt-2 h-4 w-full" />
            <Skeleton className="mt-3 h-7 w-28" />
          </div>
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-white p-4">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="mt-2 h-8 w-32" />
            <Skeleton className="mt-3 h-7 w-40" />
          </div>
        </div>
      </div>
    );
  }

  const lowBalance = wallet.balance_wei < LOW_BALANCE_WEI;

  return (
    <>
      <div className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
              GenLayer wallet
            </p>
            <h2
              className="mt-1 text-[22px] text-[#1c1c17]"
              style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
            >
              Your onchain identity
            </h2>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            StudioNet
          </span>
        </div>
        <p className="mt-2 text-[13px] leading-relaxed text-[#4b463f]">
          This wallet signs your onchain evaluations. Validators need GEN here to
          run the LLM. Fund it on the StudioNet faucet using the address below.
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              Address
            </p>
            <p className="mt-2 break-all font-mono text-[12px] text-[#1c1c17]">
              {wallet.address}
            </p>
            <button
              type="button"
              onClick={() => copy(wallet.address, "Wallet address")}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1.5 text-[11px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
            >
              <Icon name="document" size={12} />
              Copy address
            </button>
          </div>

          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-white p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              Balance
            </p>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span
                className="text-[32px] font-bold leading-none text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif" }}
              >
                {wallet.balance_gen}
              </span>
              <span className="text-[12px] text-[#7c766e]">GEN</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void refresh()}
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1.5 text-[11px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1] disabled:opacity-60"
              >
                {isLoading ? "Refreshing…" : "Refresh"}
              </button>
              <button
                type="button"
                onClick={() => setSendOpen(true)}
                disabled={wallet.balance_wei === 0}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#1c1c17] px-3 py-1.5 text-[11px] font-semibold text-white shadow-sm shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95 disabled:opacity-50"
              >
                <Icon name="send" size={11} />
                Send GEN
              </button>
            </div>
            {lowBalance ? (
              <p className="mt-3 rounded-lg border border-amber-300/60 bg-amber-50 px-2.5 py-1.5 text-[11px] text-amber-900">
                Balance is too low to run an evaluation. Fund the wallet on the
                StudioNet faucet.
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={exportKey}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#cdc5bc] bg-white px-4 py-2.5 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1] disabled:opacity-60"
          >
            <Icon name="shield_check" size={13} />
            {revealed
              ? "Hide private key"
              : exporting
              ? "Working…"
              : "Export private key"}
          </button>
          <span className="text-[11px] text-[#7c766e]">
            Audited. Treat the key like a password.
          </span>
        </div>

        {revealed ? (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50/70 p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-red-800">
              Private key
            </p>
            <p className="mt-2 break-all font-mono text-[12px] text-red-900">
              {revealed}
            </p>
            <button
              type="button"
              onClick={() => copy(revealed, "Private key")}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-[11px] font-medium text-red-800 hover:bg-red-50"
            >
              Copy private key
            </button>
            <p className="mt-3 text-[11px] leading-relaxed text-[#4b463f]">
              Save this securely. Anyone who has it can move every GEN in this
              wallet. CVPilot will never ask you for it.
            </p>
          </div>
        ) : null}
      </div>

      <SendGenModal
        open={sendOpen}
        onClose={() => {
          setSendOpen(false);
          onActivityChanged?.();
        }}
      />
    </>
  );
}
