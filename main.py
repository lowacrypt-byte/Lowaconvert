import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Moteurs de conversion
from pdf2docx import Converter
from spire.doc import Document, FileFormat

app = FastAPI(title="Lowaconvert Premium API")

# --- PROTECTION CORS : Règle l'erreur 'Connexion refusée' ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les sources (Frontend)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise POST, GET, etc.
    allow_headers=["*"],  # Autorise tous les en-têtes
)

@app.get("/")
async def health():
    return {"status": "online", "message": "Moteur Lowaconvert prêt"}

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
        
        return FileResponse(output_path, filename=f"lowaconvert_{os.path.basename(output_path)}")
    except Exception as e:
        return {"error": f"Erreur PDF-to-Word: {str(e)}"}

# --- ROUTE : WORD VERS PDF (Haute Fidélité) ---
@app.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Format Word requis")
    
    input_path = f"temp_{file.filename}"
    output_path = input_path.rsplit('.', 1)[0] + ".pdf"
    
    try:
        # Sauvegarde temporaire
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Rendu fidèle avec Spire.Doc (évite l'erreur libreoffice)
        doc = Document()
        doc.LoadFromFile(input_path)
        doc.SaveToFile(output_path, FileFormat.PDF)
        doc.Close()
        
        return FileResponse(output_path, filename=f"lowaconvert_{os.path.basename(output_path)}")
            
    except Exception as e:
        # Retourne l'erreur au Frontend pour affichage propre
        return {"error": f"Erreur système conversion : {str(e)}"}
    finally:
        # Nettoyage automatique des fichiers temporaires
        if os.path.exists(input_path): os.remove(input_path)

if __name__ == "__main__":
    # Port dynamique Railway
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
