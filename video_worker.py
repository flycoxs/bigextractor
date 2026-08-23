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
    Genera un video MP4 de 30 segundos.
    - Si hay imagen: la fija durante 30s.
    - Si hay audio: lo usa (loop si es necesario para alcanzar 30s).
    - Si no hay audio: añade pista silenciosa.
    """
    out_dir = BASE_OUTPUT / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (output_name or f"{job_id}.mp4")

    duration = 30

    if image_path and audio_path:
        # repetir audio si es corto y cortar a -t 30; -stream_loop -1 for input loop applies to video/image input, for audio we can use -stream_loop -1 on image and -shortest
        cmd = f"ffmpeg -y -loop 1 -i {shlex.quote(str(image_path))} -i {shlex.quote(str(audio_path))} -c:v libx264 -c:a aac -b:a 192k -t {duration} -pix_fmt yuv420p -shortest {shlex.quote(str(out_file))}"
    elif image_path and not audio_path:
        # Imagen + audio nulo (anullsrc)
        cmd = f"ffmpeg -y -loop 1 -i {shlex.quote(str(image_path))} -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -c:v libx264 -t {duration} -c:a aac -b:a 128k -pix_fmt yuv420p -shortest {shlex.quote(str(out_file))}"
    elif audio_path and not image_path:
        # Sin imagen: generar fondo negro
        cmd = f"ffmpeg -y -f lavfi -i color=size=1280x720:rate=25:color=black -i {shlex.quote(str(audio_path))} -c:v libx264 -c:a aac -b:a 192k -t {duration} -pix_fmt yuv420p -shortest {shlex.quote(str(out_file))}"
    else:
        # Ningún asset: generar video negro + silencio
        cmd = f"ffmpeg -y -f lavfi -i color=size=1280x720:rate=25:color=black -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -c:v libx264 -c:a aac -t {duration} -pix_fmt yuv420p -shortest {shlex.quote(str(out_file))}"

    rc = run_command(cmd)
    if rc != 0:
        raise RuntimeError('ffmpeg falló para job ' + job_id)

    return str(out_file)
