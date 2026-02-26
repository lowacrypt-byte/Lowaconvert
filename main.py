import os
import shutil
import subprocess
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI(title="Lowaconvert Premium API")

# Configuration CORS pour accepter ton site web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def check():
    return {"status": "online", "engine": "LibreOffice + pdf2docx"}

# --- ROUTE : PDF VERS WORD ---
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Fichier PDF requis")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".pdf", ".docx")
    
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        
        return FileResponse(output_path, filename=os.path.basename(output_path))
    except Exception as e:
        return {"error": str(e)}

# --- ROUTE : WORD VERS PDF (Utilise LibreOffice via Nixpacks) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx') and not file.filename.lower().endswith('.doc'):
        raise HTTPException(status_code=400, detail="Fichier Word (.docx) requis")
    
    input_path = f"temp_{file.filename}"
    
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Commande système pour convertir via LibreOffice
        # --outdir . signifie qu'il enregistre le PDF dans le dossier courant
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf", 
            input_path, "--outdir", "."
        ], check=True)
        
        # Le nom généré par LibreOffice remplace simplement l'extension
        output_path = input_path.rsplit('.', 1)[0] + ".pdf"
        
        return FileResponse(output_path, filename=os.path.basename(output_path))
    except Exception as e:
        # Renvoie l'erreur au format JSON plutôt que de faire planter le téléchargement
        return {"error": f"Erreur LibreOffice : {str(e)}"}

if __name__ == "__main__":
    # Railway définit le port automatiquement via la variable d'environnement PORT
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
