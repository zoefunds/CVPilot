# CVPilot Intelligent Contract

A GenLayer Intelligent Contract that performs verifiable, consensus-driven
evaluation of a job application (CV + cover letter + job description).

## Source

`cvpilot_contract.py`

## Deploy to StudioNet (web IDE)

You will deploy this contract once and paste the resulting address back into
the project. After that, every `LLM_BACKEND=genlayer` evaluation calls this
on-chain contract instead of the local stub.

### 1. Open GenLayer Studio

Visit **https://studio.genlayer.com**

If you have not connected a wallet/account yet, follow the Studio onboarding.
Make sure the network selector shows **StudioNet**.

### 2. Paste the contract

1. In Studio, open a new contract / project.
2. Copy the entire contents of `cvpilot_contract.py`.
3. Paste it into the Studio code editor.

### 3. Compile

Click **Compile**. You should see no errors. The Studio tooling will detect
the `@gl.contract` class `CVPilotEvaluator`.

### 4. Deploy

1. Click **Deploy**.
2. Constructor takes no arguments — leave fields blank.
3. Confirm the transaction.
4. Wait for finalization (a few seconds on StudioNet).

### 5. Copy the contract address

Studio will display the deployed contract address (`0x...`).
**Copy this address.** It is what we will paste into `.env`:
GENLAYER_CONTRACT_ADDRESS=0xYourDeployedAddressHere

### 6. Smoke-test from Studio
In the Studio UI you can call methods directly:
- `contract_version()` should return `"0.1.0"`.
- `evaluation_count()` should return `0`.
- `has_evaluation("0x0000...")` should return `false`.
You don't need to call `evaluate_application` from Studio — our backend will
drive that call in Phase 5B Part 2.
### 7. Hand the address back
Paste the contract address into this chat. I will:
1. Update `.env` (`GENLAYER_CONTRACT_ADDRESS=...`).
2. Implement `services/llm/genlayer.py` to call this contract.
3. Add a smoke test that flips `LLM_BACKEND=genlayer` and runs a real
   on-chain evaluation.
## Why this design
- **Idempotency** — same inputs hash to the same key, so re-evaluating costs
  no extra LLM consensus calls and returns the canonical stored verdict.
- **Schema stability** — the contract NORMALIZES the LLM output before
  storage, so backend code never sees malformed JSON.
- **Validator consensus** — `gl.eq_principle.prompt_comparative` enforces
  that multiple validators must agree (within tolerance) on the scoring
  before it lands on-chain. That is CVPilot's trust layer.
- **On-chain auditability** — every evaluation lives in `evaluations`
  keyed by `sha256(cv || cover_letter || job || title || url)`. Anyone
  can replay the lookup and verify the verdict.
