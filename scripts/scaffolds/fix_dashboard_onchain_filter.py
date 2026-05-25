"""
Dashboard list shows only applications that genuinely produced an on-chain
write (or are in progress / failed). Cache-hit completions and stub-only
completions are excluded.

Filter rule:
  - app.status != 'complete' (in-progress, ready, evaluating, etc.)  -> SHOW
  - app.status == 'failed'                                            -> SHOW
  - app.status == 'complete' AND evaluation has contract_tx_hash      -> SHOW
  - app.status == 'complete' AND no contract_tx_hash (cache or stub)  -> HIDE
"""
from pathlib import Path

TARGET = Path("/Users/macbook/CVPilot/backend/app/routes/applications.py")
text = TARGET.read_text(encoding="utf-8")

OLD_LIST = '''@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Application).where(Application.user_id == current_user.id).order_by(Application.created_at.desc())
    ).all()
    return [ApplicationListItem.model_validate(r) for r in rows]'''

NEW_LIST = '''@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard list: show applications that produced a real on-chain write,
    plus in-progress and failed ones. Hide completed evaluations that have
    no contract_tx_hash (cache hits or stub-only) so the dashboard reflects
    real chain activity.
    """
    from backend.app.models.evaluation import Evaluation

    rows = db.execute(
        select(Application)
        .outerjoin(Evaluation, Evaluation.application_id == Application.id)
        .where(Application.user_id == current_user.id)
        .where(
            (Application.status != "complete")
            | (Evaluation.contract_tx_hash.isnot(None))
        )
        .order_by(Application.created_at.desc())
    ).scalars().unique().all()
    return [ApplicationListItem.model_validate(r) for r in rows]'''

if OLD_LIST in text:
    TARGET.write_text(text.replace(OLD_LIST, NEW_LIST), encoding="utf-8")
    print(f"patched {TARGET.name}: list filtered to on-chain or in-progress only")
else:
    print("warn: anchor not found in applications.py; please review")
