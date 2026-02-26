from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter
import os
import shutil
import uvicorn

app = FastAPI(title="Lowaconvert Private API")

# --- CONFIGURATION CORS POUR ACCEPTER TOUTES LES ORIGINES ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise ton site web à communiquer avec l'API
    allow_credentials=True,
    allow_methods=["*"],  # Autorise POST, GET, etc.
    allow_headers=["*"],  # Autorise tous les en-têtes
)

@app.get("/")
async def root():
    return {"message": "Le moteur Lowaconvert est opérationnel sur Railway !"}

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    # Vérification de l'extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    temp_pdf = f"temp_{file.filename}"
    output_docx = temp_pdf.replace(".pdf", ".docx")

    try:
        # Sauvegarde temporaire du PDF
        with open(temp_pdf, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Conversion réelle via la bibliothèque pdf2docx
        cv = Converter(temp_pdf)
        cv.convert(output_docx)
        cv.close()
        
        return FileResponse(
            output_docx, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(output_docx)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    # Note : word-to-pdf nécessite souvent LibreOffice installé sur le serveur.
    # Cette route est prête pour l'envoi de fichier.
    return {"message": "Route word-to-pdf configurée. Prête pour déploiement avancé."}

if __name__ == "__main__":
    # Railway utilise la variable d'environnement PORT (souvent 8000 ou 8080)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
