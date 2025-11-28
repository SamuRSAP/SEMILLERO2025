from openai import OpenAI
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import os


client = OpenAI(api_key="Censurada el Api_Key por privacidad") #Api_key del modelo Gpt

#Rutas
ruta_pdf = r"RUTA DEL PDF A PROCESAR"
pytesseract.pytesseract.tesseract_cmd = r"RUTA DELK ARCHIVO TESSERACT"
poppler_path = r"RUTA DEL ARCHIVO POPPLER"

#Carpeta temporal donde se guardan las imagenes procesadas
carpeta_imagenes = "imagen_de_modelo"
os.makedirs(carpeta_imagenes, exist_ok=True)

paginas = convert_from_path(ruta_pdf, dpi=300, poppler_path=poppler_path)

#En caso de que la imagen esta borrosa o presenta algun incovenientese aplica contraste
def aplicar_contraste(img):
    return ImageEnhance.Contrast(img).enhance(2.0)

bloque_size = 3

for i in range(0, len(paginas), bloque_size):
    bloque_paginas = paginas[i:i+bloque_size]
    texto_bloque = ""
    
    for j, pagina in enumerate(bloque_paginas):
        nombre_archivo = os.path.join(carpeta_imagenes, f"pagina_{i+j+1}.png")
        pagina.save(nombre_archivo)
        img_mejorada = aplicar_contraste(pagina)
        texto = pytesseract.image_to_string(img_mejorada, lang="spa")
        texto_bloque += f"\n=== Página {i+j+1} ===\n{texto}"
        
        #Prompt para las instrucciones al modelo de GPT
    
    prompt = (
        "Eres un asistente experto en documentos médicos. Analiza el siguiente texto y extrae la información priorizando los campos principales. "
        "Para el nombre de la persona, selecciona el primer nombre completo que aparezca y que esté asociado al paciente, persona o titular del documento, "
        "usando pistas como 'Paciente', 'Se certifica que', 'Nombre'. No confundas con nombres de médicos, técnicos o profesionales.\n\n"
        "Campos principales (obligatorios):\n"
        "- Nombre de la persona o nombre que aparezca: primer nombre completo detectado o relacionado con el paciente.\n"
        "- Documento: número de identificación o numero de identidad\n"
        "- Fecha del documento: fecha cerca de 'Documento'\n"
        "- Fecha de inicio / Fecha de fin: periodo de incapacidad, puede estar separada por recuadros\n"
        "- Diagnóstico (DX): palabras o frases después de 'Diagnóstico','Codigo CIE', 'CIE'  o 'DX', tambien puede ser una pequeña combinacion que empieza por una letra seguida de numeros, ejemplo: A00.\n"
        "- Días de incapacidad: número de días mencionado en el texto\n\n"
        "Instrucciones de razonamiento:\n"
        "1. Prioriza el primer nombre complato que parezca del paciente o persona.\n"
        "2. Prioriza fechas cercanas a palabras clave.\n"
        "Ejemplo:\n"
        "Resultado:\n"
        "Nombre de la persona: Juan Jorge Pérez Sánchez\n"
        "Documento: 348575834\n"
        "Fecha de inicio: 2-nov.-2023\n"
        "Fecha de fin: 7-nov.-2023\n"
        "Diagnóstico (DX): k909 UNILATERAL O NO ESPECIFICADA, SIN OBSTRUCCIÓN\n"
        "Fecha del documento: 2-nov.-2023\n"
        "Días de incapacidad: 6\n"
        f"{texto_bloque}"
    )

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en extraer información de documentos médicos capaz de identificar toda la infomación que se te pide."},
            {"role": "user", "content": prompt}
        ]
    )
    
    #Se imprimen los resultados
    print("\n=== RESULTADOS {}-{} ===".format(i+1, i+len(bloque_paginas)))
    print(response.choices[0].message.content)
