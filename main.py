import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI(title="Lowaconvert PDF-to-Word API")

# --- CONFIGURATION CORS (Pour éviter l'erreur Failed to fetch) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Autorise ton interface Lowaconvert
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health():
    return {"status": "online", "mode": "PDF-to-Word Specialized"}

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    # Vérification de sécurité sur l'extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".pdf", ".docx")
    
    try:
        # 1. Sauvegarde du PDF sur le serveur Railway
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Conversion via pdf2docx
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        
        # 3. Envoi du fichier Word généré
        return FileResponse(
            output_path, 
            filename=f"lowaconvert_{file.filename.replace('.pdf', '.docx')}",
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        # Renvoie l'erreur précise pour le débogage
        return {"error": f"Erreur de conversion : {str(e)}"}
        
    finally:
        # Nettoyage des fichiers temporaires pour économiser l'espace
        if os.path.exists(input_path):
            os.remove(input_path)
        # Note : On ne supprime output_path qu'après l'envoi, ce que FileResponse gère mal nativement.
        # Sur Railway, les fichiers temporaires sont effacés au redémarrage.

if __name__ == "__main__":
    # Port dynamique obligatoire pour Railway
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
