import os
import uuid
import shlex
import subprocess
from pathlib import Path

BASE_OUTPUT = Path('/app/outputs')
BASE_UPLOAD = Path('/app/uploads')
BASE_OUTPUT.mkdir(parents=True, exist_ok=True)
BASE_UPLOAD.mkdir(parents=True, exist_ok=True)


def run_command(cmd):
    print('Ejecutando:', cmd)
    process = subprocess.run(cmd, shell=True, capture_output=True)
    print('stdout:', process.stdout.decode(errors='ignore'))
    print('stderr:', process.stderr.decode(errors='ignore'))
    return process.returncode


def create_video(job_id: str, image_path: str = None, audio_path: str = None, output_name: str = None):
    """
    Genera un video MP4 de 30 segundos (SIN AUDIO).
    - Si hay imagen: la fija durante 30s sin audio.
    - Si no hay imagen: fondo negro sin audio.
    """
    out_dir = BASE_OUTPUT / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (output_name or f"{job_id}.mp4")

    duration = 30

    if image_path:
        # Solo imagen, sin audio
        cmd = f"ffmpeg -y -loop 1 -i {shlex.quote(str(image_path))} -c:v libx264 -t {duration} -pix_fmt yuv420p {shlex.quote(str(out_file))}"
    else:
        # Video negro sin audio
        cmd = f"ffmpeg -y -f lavfi -i color=size=1280x720:rate=25:color=black -t {duration} -pix_fmt yuv420p {shlex.quote(str(out_file))}"

    rc = run_command(cmd)
    if rc != 0:
        raise RuntimeError('ffmpeg falló para job ' + job_id)

    return str(out_file)
