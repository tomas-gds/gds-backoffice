"""Run each scraper in a disposable process so Back can stop network calls and sleeps."""
import asyncio
import json
import multiprocessing
import tempfile
import time
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4


class JobCancelled(Exception):
    pass


class JobConflict(Exception):
    pass


def _worker(arguments, directory):
    # Keep uploaded HCP temporary files inside the parent-owned job directory.
    tempfile.tempdir = directory
    try:
        from .legacy_adapter import run_legacy_workflow
        workbook = run_legacy_workflow(**arguments)
        Path(directory, "result.xlsx").write_bytes(workbook.getvalue())
        Path(directory, "status.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    except Exception as exc:
        Path(directory, "status.json").write_text(json.dumps({"ok": False, "error": str(exc)}), encoding="utf-8")


class Job:
    def __init__(self, process):
        self.process = process
        self.cancelled = False
        self.stop_lock = asyncio.Lock()

    async def stop(self):
        async with self.stop_lock:
            if self.process.is_alive():
                self.process.terminate()
            await asyncio.to_thread(self.process.join, 2)
            if self.process.is_alive():
                self.process.kill()
                await asyncio.to_thread(self.process.join, 2)
            if self.process.is_alive():
                raise RuntimeError("The PubMed process could not be stopped. Please try again.")


class PubmedJobs:
    def __init__(self):
        self.active = {}
        self.cancelled = {}
        self.context = multiprocessing.get_context("spawn")

    def normalize_id(self, job_id):
        return str(UUID(job_id))

    def prune(self):
        now = time.monotonic()
        self.cancelled = {key: expiry for key, expiry in self.cancelled.items() if expiry > now}

    async def cancel(self, job_id):
        job_id = self.normalize_id(job_id)
        self.prune()
        # Also covers cancellation arriving before the upload/export starts.
        self.cancelled[job_id] = time.monotonic() + 3600
        job = self.active.get(job_id)
        if job is not None:
            job.cancelled = True
            await job.stop()
        return {"status": "stopped", "job_id": job_id}

    async def run(self, arguments, job_id=None, request=None, worker=_worker):
        job_id = self.normalize_id(job_id) if job_id else str(uuid4())
        self.prune()
        if job_id in self.cancelled:
            raise JobCancelled("PubMed search stopped.")
        if job_id in self.active:
            raise JobConflict("This PubMed job is already running.")
        with tempfile.TemporaryDirectory(prefix="pubmed-job-") as directory:
            process = self.context.Process(target=worker, args=(arguments, directory), daemon=True)
            job = Job(process)
            process.start()
            self.active[job_id] = job
            try:
                while process.is_alive():
                    if job.cancelled or (request is not None and await request.is_disconnected()):
                        job.cancelled = True
                        raise JobCancelled("PubMed search stopped.")
                    await asyncio.sleep(0.1)
                if job.cancelled:
                    raise JobCancelled("PubMed search stopped.")
                status_path = Path(directory, "status.json")
                if not status_path.exists():
                    raise RuntimeError("The PubMed worker exited without a result.")
                status = json.loads(status_path.read_text(encoding="utf-8"))
                if not status["ok"]:
                    raise RuntimeError(status["error"])
                return BytesIO(Path(directory, "result.xlsx").read_bytes())
            finally:
                await job.stop()
                self.active.pop(job_id, None)

    async def shutdown(self):
        for job_id in list(self.active):
            await self.cancel(job_id)


pubmed_jobs = PubmedJobs()
