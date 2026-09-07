"""Background job registry for bounded live blockchain investigations.

Live provider calls must never be tied to a browser request deadline.  Jobs keep
the browser responsive while preserving the same evidence-producing trace path.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict
from uuid import uuid4


class LiveTraceJobManager:
    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="vasp-live-trace")
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def submit(self, work: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        job_id = "LIVETRACE-" + uuid4().hex[:12].upper()
        with self._lock:
            self._jobs[job_id] = {"job_id": job_id, "status": "QUEUED", "created_at": self._now()}

        def run():
            self._set(job_id, status="RUNNING", started_at=self._now())
            try:
                result = work()
                self._set(job_id, status="COMPLETED", completed_at=self._now(), result=result)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                self._set(job_id, status="FAILED", completed_at=self._now(), error=str(detail))

        self._executor.submit(run)
        return {"job_id": job_id, "status": "QUEUED"}

    def get(self, job_id: str) -> Dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def _set(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            self._jobs[job_id].update(changes)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
