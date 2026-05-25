"""
When a GenLayer evaluation completes via the contract's idempotency cache
(same content_hash already stored on-chain, no new tx written), the
contract_tx_hash field on the Evaluation row is null but content_hash is
populated and the contract_address is set. That state is still verifiable
on-chain. Update the dashboard detail page to surface it correctly instead
of falling back to 'Scored locally'.
"""
from pathlib import Path

TARGET = Path("/Users/macbook/CVPilot/frontend/src/app/dashboard/applications/[id]/page.tsx")
text = TARGET.read_text(encoding="utf-8")

# Replace the verified/scored-locally section with one that handles three
# states: fresh tx (most verifiable), cache hit (still verifiable), local.
OLD = '''            {tx ? (
              <button
                type="button"
                onClick={() => onCopy(tx, 'Transaction hash')}
                className="mt-5 inline-flex flex-col items-start rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3 text-left transition-colors hover:bg-[#2b4f3a]/20"
                title="Click to copy"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                  Verified on StudioNet
                </span>
                <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                  tx {shortHash(tx)}
                </span>
                {ev.content_hash && (
                  <span className="mt-0.5 font-mono text-[10px] text-[#2b4f3a]/70">
                    hash {shortHash(ev.content_hash)}
                  </span>
                )}
              </button>
            ) : (
              <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
                Scored locally
              </span>
            )}'''

NEW = '''            {tx ? (
              <button
                type="button"
                onClick={() => onCopy(tx, 'Transaction hash')}
                className="mt-5 inline-flex flex-col items-start rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3 text-left transition-colors hover:bg-[#2b4f3a]/20"
                title="Click to copy"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                  Verified on StudioNet
                </span>
                <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                  tx {shortHash(tx)}
                </span>
                {ev.content_hash && (
                  <span className="mt-0.5 font-mono text-[10px] text-[#2b4f3a]/70">
                    hash {shortHash(ev.content_hash)}
                  </span>
                )}
              </button>
            ) : ev.content_hash && ev.contract_address ? (
              <button
                type="button"
                onClick={() => onCopy(ev.content_hash, 'Content hash')}
                className="mt-5 inline-flex flex-col items-start rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3 text-left transition-colors hover:bg-[#2b4f3a]/20"
                title="This evaluation is stored on-chain under this content hash (cached, no new transaction was written because the inputs were already evaluated). Click to copy."
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                  Verified on StudioNet \u00b7 cached
                </span>
                <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                  hash {shortHash(ev.content_hash)}
                </span>
                <span className="mt-0.5 text-[10px] text-[#2b4f3a]/70">
                  Same inputs already evaluated on-chain
                </span>
              </button>
            ) : (
              <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
                Scored locally
              </span>
            )}'''

if OLD in text:
    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"patched {TARGET.name}: cache-hit badge added")
else:
    print("warn: anchor not found; no change made (manual review needed)")
