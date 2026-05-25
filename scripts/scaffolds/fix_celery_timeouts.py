"""
Increase Celery task time limits to accommodate GenLayer write + finalize +
read-poll cycles which can take up to ~5 minutes on StudioNet.
"""
from pathlib import Path
p = Path("/Users/macbook/CVPilot/workers/celery_app.py")
text = p.read_text(encoding="utf-8")
text = text.replace("task_time_limit=180,", "task_time_limit=540,")
text = text.replace("task_soft_time_limit=150,", "task_soft_time_limit=480,")
p.write_text(text, encoding="utf-8")
print("bumped celery time limits to 480s soft / 540s hard")
