import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI(title="Lowaconvert Official API")

# 1. ACTIVATION DU CORS (Indispensable pour lier ton site à Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise ton interface web à appeler l'API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ROUTE DE VÉRIFICATION (Affiche si le serveur est en ligne)
@app.get("/")
async def health_check():
    return {
        "status": "online",
        "service": "Lowaconvert API",
        "message": "Le moteur est prêt pour la conversion"
    }

# 3. CONVERSION PDF VERS WORD
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    # Vérification stricte du format
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Veuillez envoyer un fichier PDF uniquement.")

    # Chemins temporaires pour Railway
    input_path = f"temp_{file.filename}"
    output_path = input_path.replace(".pdf", ".docx")

    try:
        # Sauvegarde du fichier reçu
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Exécution de la conversion
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        
        # Envoi du fichier converti au navigateur
        return FileResponse(
            output_path, 
            filename=os.path.basename(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return {"error": f"Erreur lors de la conversion : {str(e)}"}
    finally:
        # Nettoyage (optionnel sur Railway qui réinitialise les instances)
        if os.path.exists(input_path):
            pass 

# 4. CONFIGURATION DU PORT POUR RAILWAY
if __name__ == "__main__":
    # Railway utilise la variable d'environnement PORT, par défaut 8000 ou 8080
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)

