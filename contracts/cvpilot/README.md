# CVPilot Intelligent Contract

The on-chain trust layer for CVPilot. This contract evaluates job application
inputs with nondeterministic LLM reasoning and uses GenLayer validator
consensus to finalize the result.

## Source

`cvpilot_contract.py`

## Current deployment

| Property | Value |
|----------|-------|
| Contract | `CVPilotEvaluator` |
| Version | `1.0.5` |
| Network | GenLayer StudioNet |
| Address | `0xcB5C521f2Ccc2496F40218Ba344F3AB7eE8C6C70` |

## What it does

- Evaluates CVs, cover letters, and job descriptions.
- Generates a final score and reasoning payload.
- Produces skills gap, interview, salary, portfolio, career, and strategy
  outputs.
- Stores results by content hash so repeated submissions are deterministic at
  the storage layer.
- Uses validator consensus to finalize each write path.

## Why it matters

The contract is the part that makes CVPilot auditable. The backend can present
results, but the contract is the source of truth that validators agree on.

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
2. Constructor takes no arguments - leave fields blank.
3. Confirm the transaction.
4. Wait for finalization on StudioNet.

### 5. Copy the contract address

Studio will display the deployed contract address (`0x...`).
Copy this address. It is what we paste into `.env`:

`GENLAYER_CONTRACT_ADDRESS=0xYourDeployedAddressHere`

### 6. Smoke-test from Studio

In the Studio UI you can call methods directly:

- `contract_version()` should return the deployed version string.
- `evaluation_count()` should return `0`.
- `has_evaluation("0x0000...")` should return `false`.

You do not need to call `evaluate_application` from Studio. Our backend drives
that call in production.

### 7. Hand the address back

Paste the contract address into the chat. I will:

1. Update `.env` (`GENLAYER_CONTRACT_ADDRESS=...`).
2. Implement or refresh `services/llm/genlayer.py` to call this contract.
3. Add or run a smoke test that flips `LLM_BACKEND=genlayer` and performs a
   real on-chain evaluation.

## Why this design

- **Idempotency** - the same inputs map to the same content hash, so repeated
  evaluation is stable.
- **Schema stability** - the contract normalizes LLM output before storage so
  the backend receives JSON instead of raw model text.
- **Validator consensus** - `gl.eq_principle.prompt_comparative` keeps the
  validator set involved while tolerating broader variance between results.
- **On-chain auditability** - every evaluation lives in contract storage and
  can be replayed from the original content hash.
