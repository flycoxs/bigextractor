from flask import Flask, request, jsonify, send_file
from pathlib import Path
from video_worker import create_video
import uuid
import os

app = Flask(__name__)

UPLOAD_FOLDER = Path('/app/uploads')
OUTPUT_FOLDER = Path('/app/outputs')

# Crear carpetas si no existen
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Configuración
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def allowed_file(filename):
    """Verifica que el archivo sea una imagen permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200


@app.route('/upload-and-create', methods=['POST'])
def upload_and_create():
    """
    Recibe una imagen, la guarda y crea un video de 30s
    
    Uso:
    curl -X POST -F "image=@/path/to/image.jpg" http://localhost:5000/upload-and-create
    """
    try:
        # Validar que hay archivo
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validar tipo de archivo
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Allowed: jpg, jpeg, png, gif, bmp"}), 400
        
        # Generar ID único para el job
        job_id = str(uuid.uuid4())
        image_ext = Path(file.filename).suffix or '.jpg'
        image_path = UPLOAD_FOLDER / f"{job_id}{image_ext}"
        
        # Guardar imagen
        print(f"[{job_id}] Guardando imagen en: {image_path}")
        file.save(image_path)
        
        # Verificar que se guardó
        if not image_path.exists():
            return jsonify({"error": "Failed to save image"}), 500
        
        print(f"[{job_id}] Imagen guardada. Creando video...")
        
        # Crear video
        video_path = create_video(job_id=job_id, image_path=str(image_path))
        
        print(f"[{job_id}] Video creado exitosamente")
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "image_saved": str(image_path),
            "video_created": video_path,
            "download_url": f"/download/{job_id}"
        }), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    """Descarga el video generado"""
    try:
        video_path = OUTPUT_FOLDER / job_id / f"{job_id}.mp4"
        
        if not video_path.exists():
            return jsonify({"error": "Video not found"}), 404
        
        return send_file(video_path, mimetype='video/mp4', as_attachment=True, download_name=f"{job_id}.mp4")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/video-info/<job_id>', methods=['GET'])
def video_info(job_id):
    """Obtiene información del video"""
    try:
        video_path = OUTPUT_FOLDER / job_id / f"{job_id}.mp4"
        image_path = list(UPLOAD_FOLDER.glob(f"{job_id}.*"))
        
        if not video_path.exists():
            return jsonify({"error": "Video not found"}), 404
        
        video_size = video_path.stat().st_size
        image_info = None
        
        if image_path:
            image_info = {
                "path": str(image_path[0]),
                "size": image_path[0].stat().st_size
            }
        
        return jsonify({
            "job_id": job_id,
            "video_path": str(video_path),
            "video_size_bytes": video_size,
            "video_size_mb": round(video_size / (1024 * 1024), 2),
            "image": image_info
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🎬 Servidor de creación de videos iniciado")
    print("📁 Carpeta de uploads: " + str(UPLOAD_FOLDER))
    print("📁 Carpeta de outputs: " + str(OUTPUT_FOLDER))
    print("🌐 Acceso en: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
