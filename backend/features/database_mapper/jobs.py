"""Run matching in a disposable process so it can be stopped safely."""
import asyncio
import json
import multiprocessing
import tempfile
import time
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pandas as pd
from python_calamine import CalamineWorkbook


class JobCancelled(Exception): pass
class JobConflict(Exception): pass
class JobFailed(Exception):
    def __init__(self, detail, status=500): self.detail, self.status = detail, status


def _table(raw, name):
    if name.lower().endswith(".csv"):
        return pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False, na_filter=False)
    return pd.read_excel(BytesIO(raw), engine="calamine", dtype=str, keep_default_na=False, na_filter=False)


def _worker(args, directory):
    try:
        from .matcher import CANDIDATE_LIMIT, duplicated_rows, match_frames, matching_strategy
        source, target = _table(args["source"], args["source_name"]), _table(args["target"], args["target_name"])
        pairs = args["pairs"]
        if not pairs or any(p.get("source") not in source.columns or p.get("target") not in target.columns for p in pairs):
            raise JobFailed("The selected mapping fields are not valid.", 400)
        source_columns, target_columns = [p["source"] for p in pairs], [p["target"] for p in pairs]
        if not duplicated_rows(source, source_columns).empty or not duplicated_rows(target, target_columns).empty:
            raise JobFailed("The selected mapping-field combinations contain duplicate values.", 409)
        matches = match_frames(source, target, pairs)
        result = {"source_rows": len(source), "target_rows": len(target), "column_pairs": pairs,
                  "matching_strategy": matching_strategy(len(source), len(target)),
                  "possible_comparisons": len(source) * len(target),
                  "comparisons_performed": sum(item["candidates_considered"] for item in matches),
                  "candidate_limit": CANDIDATE_LIMIT if matching_strategy(len(source), len(target)) == "indexed" else None,
                  "matches": matches}
        Path(directory, "result.json").write_text(json.dumps(result), encoding="utf-8")
        status = {"ok": True}
    except JobFailed as exc:
        status = {"ok": False, "error": exc.detail, "status": exc.status}
    except Exception as exc:
        status = {"ok": False, "error": str(exc), "status": 500}
    Path(directory, "status.json").write_text(json.dumps(status), encoding="utf-8")


class MapperJobs:
    def __init__(self):
        self.active, self.cancelled = {}, {}
        self.context = multiprocessing.get_context("spawn")
    def _id(self, job_id): return str(UUID(job_id))
    async def cancel(self, job_id):
        job_id = self._id(job_id); self.cancelled[job_id] = time.monotonic() + 3600
        process = self.active.get(job_id)
        if process and process.is_alive():
            process.terminate(); await asyncio.to_thread(process.join, 2)
            if process.is_alive(): process.kill(); await asyncio.to_thread(process.join, 2)
        return {"status": "stopped", "job_id": job_id}
    async def run(self, args, job_id, request):
        job_id = self._id(job_id)
        if job_id in self.cancelled: raise JobCancelled("Matching stopped.")
        if job_id in self.active: raise JobConflict("This matching job is already running.")
        with tempfile.TemporaryDirectory(prefix="mapper-job-") as directory:
            process = self.context.Process(target=_worker, args=(args, directory), daemon=True)
            process.start(); self.active[job_id] = process
            try:
                while process.is_alive():
                    if job_id in self.cancelled or await request.is_disconnected():
                        await self.cancel(job_id); raise JobCancelled("Matching stopped.")
                    await asyncio.sleep(.1)
                if job_id in self.cancelled: raise JobCancelled("Matching stopped.")
                status = json.loads(Path(directory, "status.json").read_text(encoding="utf-8"))
                if not status["ok"]: raise JobFailed(status["error"], status.get("status", 500))
                return json.loads(Path(directory, "result.json").read_text(encoding="utf-8"))
            finally:
                self.active.pop(job_id, None)
    async def shutdown(self):
        for job_id in list(self.active): await self.cancel(job_id)


mapper_jobs = MapperJobs()
