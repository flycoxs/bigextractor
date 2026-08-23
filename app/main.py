from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from redis import Redis
from rq import Queue
import uuid
import os
from pathlib import Path
from typing import Optional
import shutil

app = FastAPI(title='BigExtractor Video MVP')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
redis_conn = Redis.from_url(REDIS_URL)
q = Queue(connection=redis_conn)

BASE_UPLOAD = Path('/app/uploads')
BASE_OUTPUT = Path('/app/outputs')
BASE_UPLOAD.mkdir(parents=True, exist_ok=True)
BASE_OUTPUT.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(BASE_OUTPUT)), name="outputs")

@app.get('/', response_class=HTMLResponse)
async def homepage():
    html = Path('static/index.html').read_text()
    return HTMLResponse(content=html)

@app.post('/create-video')
async def create_video(image: Optional[UploadFile] = File(None), audio: Optional[UploadFile] = File(None)):
    job_id = str(uuid.uuid4())
    job_dir = BASE_UPLOAD / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    image_path = None
    audio_path = None

    if image:
        image_path = job_dir / image.filename
        with image_path.open('wb') as f:
            shutil.copyfileobj(image.file, f)
    if audio:
        audio_path = job_dir / audio.filename
        with audio_path.open('wb') as f:
            shutil.copyfileobj(audio.file, f)

    # Encolar job: la función registrada será video_worker.create_video
    job = q.enqueue('video_worker.create_video', job_id, str(image_path) if image_path else None, str(audio_path) if audio_path else None, job_id + '.mp4')

    return JSONResponse({'job_id': job.get_id(), 'status': 'queued'})

@app.get('/jobs/{job_id}')
async def get_job(job_id: str):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return JSONResponse({'error': 'job not found'}, status_code=404)

    if job.is_finished:
        candidate = BASE_OUTPUT / job.args[0] / (job_id + '.mp4') if job.args else BASE_OUTPUT / job_id / (job_id + '.mp4')
        candidate = BASE_OUTPUT / job_id / (job_id + '.mp4')
        if candidate.exists():
            return JSONResponse({'status': 'finished', 'download_url': f'/outputs/{job_id}/{job_id}.mp4'})
        else:
            folder = BASE_OUTPUT / job_id
            if folder.exists():
                files = list(folder.glob('*.mp4'))
                if files:
                    name = files[0].name
                    return JSONResponse({'status': 'finished', 'download_url': f'/outputs/{job_id}/{name}'})
            return JSONResponse({'status': 'finished', 'download_url': None})
    elif job.is_queued:
        return JSONResponse({'status': 'queued'})
    elif job.is_failed:
        return JSONResponse({'status': 'failed', 'error': str(job.exc_info)})
    else:
        return JSONResponse({'status': 'started'})
