from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter
import os
import shutil
import uvicorn

app = FastAPI(title="Lowaconvert API")

# --- PROTECTION ANTI-ERREUR 403 (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Autorise ton site web à appeler l'API
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    pdf_path = f"temp_{file.filename}"
    docx_path = pdf_path.replace(".pdf", ".docx")

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        return FileResponse(docx_path, filename=os.path.basename(docx_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Nettoyage optionnel des fichiers temporaires ici
        pass

@app.get("/")
def read_root():
    return {"status": "Lowaconvert API est opérationnelle sur Railway"}

if __name__ == "__main__":
    # Railway définit le port dynamiquement via une variable d'environnement
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
  
