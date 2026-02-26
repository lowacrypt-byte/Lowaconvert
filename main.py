import os
import shutil
import subprocess
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI(title="Lowaconvert Premium API")

# --- CONFIGURATION CORS (Indispensable pour lier ton site) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Autorise toutes les requêtes venant de ton interface
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Serveur Lowaconvert Actif avec moteur LibreOffice (soffice)"}

# --- ROUTE 1 : PDF VERS WORD (Moteur pdf2docx) ---
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
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
        return {"error": f"Erreur PDF->Word: {str(e)}"}

# --- ROUTE 2 : WORD VERS PDF (Moteur soffice / LibreOffice) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    # Vérification de l'extension
    if not (file.filename.lower().endswith('.docx') or file.filename.lower().endswith('.doc')):
        raise HTTPException(status_code=400, detail="Veuillez envoyer un fichier Word (.docx ou .doc)")

    input_path = f"temp_{file.filename}"
    
    try:
        # 1. Sauvegarde du fichier sur le serveur Railway
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Utilisation de 'soffice' (la commande standard Linux)
        # --headless : Pas d'interface graphique
        # --convert-to pdf : Le format cible
        # --outdir . : Enregistre dans le dossier actuel
        subprocess.run([
            "soffice", "--headless", "--convert-to", "pdf", 
            input_path, "--outdir", "."
        ], check=True)
        
        # 3. Définir le chemin du fichier généré
        output_path = input_path.rsplit('.', 1)[0] + ".pdf"
        
        # 4. Vérifier si le fichier a bien été créé avant de l'envoyer
        if os.path.exists(output_path):
            return FileResponse(output_path, filename=os.path.basename(output_path))
        else:
            return {"error": "Le fichier PDF n'a pas pu être généré par le moteur soffice."}

    except Exception as e:
        # Retourne l'erreur exacte pour le débogage
        return {"error": f"Erreur de conversion Word : {str(e)}"}

if __name__ == "__main__":
    # Utilisation du port dynamique imposé par Railway
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
