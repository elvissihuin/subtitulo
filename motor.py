import whisper
import uuid
import subprocess
import os
from deep_translator import GoogleTranslator

# =========================
# DESCARGAR VIDEO
# =========================

def descargar_video(url, video_path):

    subprocess.run([
        "python",
        "-m",
        "yt_dlp",
        "-o",
        video_path,
        url
    ])

    return video_path

# =========================
# GENERAR SUBTÍTULOS
# =========================

def generar_subtitulos(video):

    model = whisper.load_model("base")

    resultado = model.transcribe(video)

    return resultado

# =========================
# TIEMPO SRT
# =========================

def tiempo(t):

    horas = int(t // 3600)

    minutos = int((t % 3600) // 60)

    segundos = int(t % 60)

    milisegundos = int(
        (t - int(t)) * 1000
    )

    return f"{horas:02}:{minutos:02}:{segundos:02},{milisegundos:03}"

# =========================
# GUARDAR SRT
# =========================

def guardar_srt(resultado, carpeta_id):
    srt = ""
    for i, segmento in enumerate(resultado["segments"], start=1):
        srt += f"{i}\n"
        srt += f"{tiempo(segmento['start'])} --> {tiempo(segmento['end'])}\n"
        srt += f"{segmento['text'].strip()}\n\n"

    with open(f"outputs/{carpeta_id}/subtitulos.srt", "w", encoding="utf-8") as f:
        f.write(srt)

# =========================
# TRADUCIR
# =========================

def traducir_srt(destino, carpeta_id):
    with open(f"outputs/{carpeta_id}/subtitulos.srt", "r", encoding="utf-8") as f:
        lineas = f.readlines()

    resultado = []
    texto_completo = ""

    for linea in lineas:
        if linea.strip().isdigit() or "-->" in linea or linea.strip() == "":
            resultado.append(linea)
        else:
            try:
                traducido = GoogleTranslator(source='auto', target=destino).translate(linea.strip())
                resultado.append(traducido + "\n")
                texto_completo += traducido + " "
            except:
                resultado.append(linea)
                texto_completo += linea.strip() + " "

    with open(f"outputs/{carpeta_id}/subtitulos_traducidos.srt", "w", encoding="utf-8") as f:
        f.writelines(resultado)

    with open(f"outputs/{carpeta_id}/texto_traducido.txt", "w", encoding="utf-8") as f:
        f.write(texto_completo)

# =========================
# PROCESAR TODO
# =========================

def procesar(url, traducir="es", subtitulos="Sí"):
    carpeta_id = str(uuid.uuid4())  # Generar UUID único
    os.makedirs(f"outputs/{carpeta_id}", exist_ok=True)  # Crear carpeta única

    video_path = f"outputs/{carpeta_id}/video.%(ext)s"  # Ruta para el video
    video = descargar_video(url, video_path)

    if not video:
        return None  # Devolver None en caso de error

    # Encontrar el archivo de video descargado y renombrarlo
    for archivo in os.listdir(f"outputs/{carpeta_id}"):
        if archivo.startswith("video."):
            ext = archivo.split('.')[-1]
            nuevo_nombre = f"video_original.{ext}"
            os.rename(f"outputs/{carpeta_id}/{archivo}", f"outputs/{carpeta_id}/{nuevo_nombre}")
            video = f"outputs/{carpeta_id}/{nuevo_nombre}"
            break
    else:
        return None

    if subtitulos == "Sí":
        resultado = generar_subtitulos(video)
        guardar_srt(resultado, carpeta_id)  # Pasar carpeta_id
        if traducir != "No":
            traducir_srt(traducir, carpeta_id)  # Pasar carpeta_id

    return carpeta_id  # Devolver el UUID de la carpeta