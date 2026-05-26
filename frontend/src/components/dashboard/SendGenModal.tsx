"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, walletApi } from "@/lib/api";
import { useToast } from "@/contexts/ToastContext";
import { useWallet } from "@/contexts/WalletContext";
import { Icon } from "@/components/icons/Icon";

interface Props {
  open: boolean;
  onClose: () => void;
}

const ADDR_RE = /^0x[0-9a-fA-F]{40}$/;

function isValidAmount(
  s: string,
  balanceGen: string | undefined,
): { ok: boolean; reason?: string } {
  const n = Number(s);
  if (!s || !Number.isFinite(n) || n <= 0)
    return { ok: false, reason: "Enter an amount greater than zero." };
  const bal = Number(balanceGen || "0");
  if (Number.isFinite(bal) && n > bal)
    return { ok: false, reason: "Amount exceeds your balance." };
  return { ok: true };
}

export function SendGenModal({ open, onClose }: Props) {
  const { wallet, refresh } = useWallet();
  const { push } = useToast();
  const [to, setTo] = useState("");
  const [amount, setAmount] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (open) {
      setTo("");
      setAmount("");
      setError(null);
      setConfirming(false);
      setBusy(false);
    }
  }, [open]);

  if (!open) return null;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!ADDR_RE.test(to.trim())) {
      setError("Recipient must be a 0x address (42 characters).");
      return;
    }
    if (wallet && to.trim().toLowerCase() === wallet.address.toLowerCase()) {
      setError("You cannot send to your own wallet.");
      return;
    }
    const v = isValidAmount(amount, wallet?.balance_gen);
    if (!v.ok) {
      setError(v.reason || "Invalid amount.");
      return;
    }
    setConfirming(true);
  }

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const res = await walletApi.send({
        to_address: to.trim(),
        amount_gen: amount,
      });
      push({
        tone: "success",
        title: "GEN sent.",
        message: `tx ${res.tx_hash.slice(0, 10)}…`,
      });
      void refresh();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Send failed.");
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-[#1c1c17]/45 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-3xl border border-[#cdc5bc]/60 bg-[#fcf9f1] p-7 shadow-2xl shadow-[#1c1c17]/15">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
              Wallet
            </p>
            <h2
              className="mt-1 text-[24px] leading-tight text-[#1c1c17]"
              style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
            >
              Send GEN
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-[#4b463f] transition-colors hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <p className="mt-2 text-[12px] text-[#7c766e]">
          From{" "}
          <span className="font-mono text-[#1c1c17]">
            {wallet?.address.slice(0, 8)}…{wallet?.address.slice(-6)}
          </span>
          {" · "}Balance{" "}
          <span className="font-semibold text-[#1c1c17]">
            {wallet?.balance_gen || "0"} GEN
          </span>
        </p>

        {!confirming ? (
          <form onSubmit={onSubmit} className="mt-5 flex flex-col gap-4">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
                Recipient
              </label>
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="0x…"
                autoComplete="off"
                spellCheck={false}
                required
                className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 font-mono text-[13px] text-[#1c1c17] placeholder:text-[#a8a298] focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10"
              />
              <p className="mt-1.5 text-[11px] text-[#7c766e]">
                A 0x address on StudioNet.
              </p>
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
                Amount
              </label>
              <input
                type="number"
                step="any"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.5"
                required
                className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[14px] text-[#1c1c17] placeholder:text-[#a8a298] focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10"
              />
              <p className="mt-1.5 text-[11px] text-[#7c766e]">
                Maximum {wallet?.balance_gen || "0"} GEN.
              </p>
            </div>
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[12px] text-red-800">
                {error}
              </div>
            ) : null}
            <div className="mt-1 flex flex-wrap gap-2">
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
              >
                Review
                <Icon name="chevron_right" size={13} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-5 flex flex-col gap-4">
            <div className="rounded-2xl border border-[#cdc5bc] bg-white p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                Confirm
              </p>
              <p className="mt-2 text-[14px] text-[#1c1c17]">
                Send{" "}
                <span
                  className="font-semibold"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  {amount} GEN
                </span>{" "}
                to:
              </p>
              <p className="mt-1 break-all font-mono text-[12px] text-[#1c1c17]">
                {to.trim()}
              </p>
              <p className="mt-3 text-[11px] text-[#7c766e]">
                This transfer is irreversible. Double check the address.
              </p>
            </div>
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[12px] text-red-800">
                {error}
              </div>
            ) : null}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={confirm}
                disabled={busy}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Sending…" : "Confirm send"}
                {busy ? null : <Icon name="send" size={13} />}
              </button>
              <button
                type="button"
                onClick={() => {
                  setConfirming(false);
                  setError(null);
                }}
                disabled={busy}
                className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1] disabled:opacity-60"
              >
                Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
