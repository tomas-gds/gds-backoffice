import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.features.pubmed_scraper.jobs import PubmedJobs, JobCancelled, JobConflict


def sleeper(arguments, directory):
    import time
    Path(arguments['marker']).write_text(directory)
    time.sleep(60)


def success(arguments, directory):
    Path(directory, 'result.xlsx').write_bytes(b'workbook')
    Path(directory, 'status.json').write_text(json.dumps({'ok': True}))


def failure(arguments, directory):
    Path(directory, 'status.json').write_text(json.dumps({'ok': False, 'error': 'Fixture failure'}))


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.jobs = PubmedJobs()
        self.files = tempfile.TemporaryDirectory()

    async def asyncTearDown(self):
        await self.jobs.shutdown()
        self.files.cleanup()

    async def wait_started(self, marker):
        for _ in range(100):
            if marker.exists():
                return
            await asyncio.sleep(0.05)
        self.fail('Worker did not start')

    async def test_stop_running_process_and_restart(self):
        job_id = str(uuid4()); marker = Path(self.files.name, 'started')
        task = asyncio.create_task(self.jobs.run({'marker': str(marker)}, job_id, worker=sleeper))
        await self.wait_started(marker)
        process = self.jobs.active[job_id].process
        directory = marker.read_text()
        await self.jobs.cancel(job_id)
        self.assertFalse(process.is_alive())
        with self.assertRaises(JobCancelled):
            await task
        self.assertFalse(Path(directory).exists())
        result = await self.jobs.run({}, worker=success)
        self.assertEqual(result.getvalue(), b'workbook')

    async def test_cancel_before_start(self):
        job_id = str(uuid4())
        await self.jobs.cancel(job_id)
        with self.assertRaises(JobCancelled):
            await self.jobs.run({}, job_id, worker=success)
        self.assertFalse(self.jobs.active)

    async def test_success(self):
        result = await self.jobs.run({}, worker=success)
        self.assertEqual(result.getvalue(), b'workbook')
        self.assertFalse(self.jobs.active)

    async def test_error(self):
        with self.assertRaisesRegex(RuntimeError, 'Fixture failure'):
            await self.jobs.run({}, worker=failure)
        self.assertFalse(self.jobs.active)

    async def test_duplicate_id(self):
        job_id = str(uuid4()); marker = Path(self.files.name, 'started')
        task = asyncio.create_task(self.jobs.run({'marker': str(marker)}, job_id, worker=sleeper))
        await self.wait_started(marker)
        with self.assertRaises(JobConflict):
            await self.jobs.run({}, job_id, worker=success)
        await self.jobs.cancel(job_id)
        with self.assertRaises(JobCancelled):
            await task

    async def test_disconnected_request(self):
        class Disconnected:
            async def is_disconnected(self):
                return True
        with self.assertRaises(JobCancelled):
            await self.jobs.run({'marker': str(Path(self.files.name, 'started'))}, request=Disconnected(), worker=sleeper)
        self.assertFalse(self.jobs.active)

    async def test_request_task_cancelled(self):
        job_id = str(uuid4()); marker = Path(self.files.name, 'started')
        task = asyncio.create_task(self.jobs.run({'marker': str(marker)}, job_id, worker=sleeper))
        await self.wait_started(marker)
        process = self.jobs.active[job_id].process
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(process.is_alive())
        self.assertFalse(self.jobs.active)


if __name__ == '__main__':
    unittest.main()
