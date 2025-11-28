import pytesseract
from pdf2image import convert_from_path
from PIL import Image


#Rutas
pytesseract.pytesseract.tesseract_cmd = r"RUTA DELK ARCHIVO TESSERACT"

ruta_pdf = r"RUTA DEL PDF A PROCESAR"

#Convierte los pdf en imaagenes legibles para su analisis OCR
paginas = convert_from_path(
    ruta_pdf,
    dpi=300,
    poppler_path = r"RUTA DEL ARCHIVO POPPLER"
)


#Extracción OCR
texto_total = ""
for i, pagina in enumerate(paginas):
    texto = pytesseract.image_to_string(pagina, lang="spa")
    texto_total += f"\n=== Página {i+1} ===\n" + texto
    
    #Resultados de extracción

print("=== TEXTO EXTRAÍDO DEL PDF ===")
print(texto_total)

with open("texto_extraido.txt", "w", encoding="utf-8") as f:
    f.write(texto_total)
