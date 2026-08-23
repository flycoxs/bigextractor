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

# Montar carpeta de outputs
app.mount("/outputs", StaticFiles(directory=str(BASE_OUTPUT)), name="outputs")

# Montar carpeta de static files
STATIC_DIR = Path('/app/static')
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get('/', response_class=HTMLResponse)
async def homepage():
    try:
        html_path = Path('/app/static/index.html')
        if html_path.exists():
            html = html_path.read_text()
            return HTMLResponse(content=html)
    except Exception as e:
        print(f"Error loading index.html: {e}")
    
    # Fallback HTML si no existe el archivo
    return HTMLResponse(content="""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>BigExtractor - Video MVP</title>
      </head>
      <body>
        <h1>Generar video de 30s</h1>
        <form id="form">
          <label>Imagen (jpg/png): <input type="file" id="image" name="image" accept="image/*" /></label><br/>
          <label>Audio (mp3/wav): <input type="file" id="audio" name="audio" accept="audio/*" /></label><br/>
          <button type="submit">Crear video</button>
        </form>
        <div id="status"></div>

        <script>
          const form = document.getElementById('form');
          const status = document.getElementById('status');
          form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = new FormData();
            const image = document.getElementById('image').files[0];
            const audio = document.getElementById('audio').files[0];
            if (image) data.append('image', image);
            if (audio) data.append('audio', audio);
            status.innerText = 'Encolando...';
            const res = await fetch('/create-video', { method: 'POST', body: data });
            const j = await res.json();
            const jobId = j.job_id;
            status.innerText = `Job creado: ${jobId}`;
            // Polling
            const check = async () => {
              const sj = await fetch(`/jobs/${jobId}`);
              const s = await sj.json();
              status.innerText = JSON.stringify(s);
              if (s.status === 'finished' && s.download_url) {
                status.innerHTML = `Listo: <a href="${s.download_url}" target="_blank">Descargar</a>`;
              } else if (s.status === 'failed') {
                status.innerText = 'Error: ' + (s.error || 'unknown');
              } else {
                setTimeout(check, 2000);
              }
            }
            setTimeout(check, 2000);
          });
        </script>
      </body>
    </html>
    """)

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
    except Exception as e:
        return JSONResponse({'error': f'job not found: {str(e)}'}, status_code=404)

    if job.is_finished:
        output_dir = BASE_OUTPUT / job_id
        video_path = output_dir / (job_id + '.mp4')
        
        if video_path.exists():
            return JSONResponse({'status': 'finished', 'download_url': f'/outputs/{job_id}/{job_id}.mp4'})
        else:
            if output_dir.exists():
                files = list(output_dir.glob('*.mp4'))
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

@app.get('/health')
async def health():
    return JSONResponse({'status': 'ok'})
