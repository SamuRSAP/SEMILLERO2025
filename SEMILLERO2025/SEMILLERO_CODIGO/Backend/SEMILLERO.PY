import imaplib
import email
import re
import io
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rapidfuzz import fuzz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from openai import OpenAI
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageEnhance

#Información para conectar el correo al script
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "semi25llero@gmail.com"
PASSWORD = "Contraseña de aplicación"


#Se conecta a los servicos de google
CLIENT_SECRET_FILE = "client_secret_user.json"
SCOPES = ['https://www.googleapis.com/auth/drive.file',  
          'https://www.googleapis.com/auth/spreadsheets']

CARPETA_ID_DRIVE = "ID DE DRIVE"
CARPETA_TEMP = r"ruta carpeta temporal"

#Api de GPT
OPENAI_API_KEY = "Api_Key"

os.makedirs(CARPETA_TEMP, exist_ok=True)
pytesseract.pytesseract.tesseract_cmd = r"RUTA TESSERACT"
client = OpenAI(api_key=OPENAI_API_KEY)

#Funcion para guardar en sheets
def guardar_en_sheets(resultado):

    SPREADSHEET_ID = "ID de sheets"
    RANGE_NAME = 'Hoja 1!B3:H'
  

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("sheets_service_account.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()


    campos_fechas = {
        "Fecha de documento",
        "Fecha de inicio",
        "Fecha de fin"
    }

    orden_campos = [
        "Nombre de la persona",
        "Documento",
        "Fecha de documento", 
        "Fecha de inicio",
        "Fecha de fin",
        "Diagnóstico (DX)",
        "Días de incapacidad"
    ]
    valores = []
    for campo in orden_campos:
        valor = resultado.get(campo, "")
        if campo in campos_fechas and valor:
            valor = f"'{valor}"  
        valores.append([campo, valor])

    valores.append(["\u200B", "\u200B"])
    valores.append(["\u200B", "\u200B"])    

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": valores}
    ).execute()

#Manda correo
def enviar_correo_notificacion(resultado):
    """Envía correo con los datos extraídos después de guardar en Sheets"""
    remitente = "semi25llero@gmail.com"
    contraseña = "Contraseña de aplicación"
    destinatarios = ["escuelau1984@gmail.com", "samkarol03@gmail.com"]
    
    #Crear mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = ", ".join(destinatarios)
    mensaje['Bcc'] = "samkarol03@gmail.com"
    mensaje['Subject'] = f"Excusa Medica - {resultado.get('Nombre de la persona', 'N/A')}"  
    
    #Cuerpo del correo
    cuerpo = f"""El/La estudiante {resultado.get('Nombre de la persona', 'N/A')} con documento {resultado.get('Documento', 'N/A')} estuvo incapacitado por {resultado.get('Días de incapacidad', 'N/A')} dias, a causa de {resultado.get('Diagnóstico (DX)', 'N/A')}.

Cordialmente"""
    
    mensaje.attach(MIMEText(cuerpo, 'plain'))
    
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remitente, contraseña)
        servidor.sendmail(remitente, destinatarios, mensaje.as_string())
        servidor.quit()
        print(f"Correo enviado a {', '.join(destinatarios)}")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

#Se conecta y sube doc al drive
def conectar_drive_usuario():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def subir_pdf_a_drive(nombre_archivo, datos_pdf, carpeta_id, service):
    file_metadata = {'name': nombre_archivo, 'parents': [carpeta_id]}
    media = MediaIoBaseUpload(io.BytesIO(datos_pdf), mimetype='application/pdf', resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    #print(f"Subido a Drive: {nombre_archivo}")

#Funciones auxiliares de GPT
def aplicar_contraste(img):
    return ImageEnhance.Contrast(img).enhance(2.0)

def procesar_pdf_con_gpt(pdf_bytes):
    paginas = convert_from_bytes(pdf_bytes, dpi=300)
    bloque_size = 3
    carpeta_imagenes = os.path.join(CARPETA_TEMP, "imagenes")
    os.makedirs(carpeta_imagenes, exist_ok=True)

    for i in range(0, len(paginas), bloque_size):
        bloque_paginas = paginas[i:i+bloque_size]
        texto_bloque = ""

        for j, pagina in enumerate(bloque_paginas):
            nombre_archivo = os.path.join(carpeta_imagenes, f"pagina_{i+j+1}.png")
            pagina.save(nombre_archivo)
            img_mejorada = aplicar_contraste(pagina)
            texto = pytesseract.image_to_string(img_mejorada, lang="spa")
            texto_bloque += f"\n=== Página {i+j+1} ===\n{texto}"
#Prompt para GPT 
        prompt = (
        "Eres un asistente experto en documentos médicos. Analiza el siguiente texto y extrae la información priorizando los campos principales. "
        "Para el nombre de la persona, selecciona el primer nombre completo que aparezca y que esté asociado al paciente, persona o titular del documento, "
        "usando pistas como 'Paciente', 'Se certifica que', 'Nombre'. No confundas con nombres de médicos, técnicos o profesionales.\n\n"
        "Campos principales (obligatorios Y cada item debe ser en orden tal cual te lo pido):\n"
        "- Nombre de la persona, nombre del paciente, nombre del pdf podria ser si no se encuentra o nombre que aparezca: primer nombre completo detectado o relacionado con el paciente.\n"
        "- Documento o Cédula: (número de identificación, puede incluir “CC”, “TI” u otro prefijo): número de identificación o numero de identidad\n"
        "- Fecha del documento: fecha cerca de 'Documento'\n"
        "- Fecha de inicio / Fecha de fin: periodo de incapacidad, puede estar separada por recuadros, o empezar con las palabras 'desde' y 'hasta, '\n"
        "- Diagnóstico (DX): palabras o frases después de 'Diagnóstico','Codigo CIE', 'CIE'  o 'DX', tambien puede ser una pequeña combinacion que empieza por una letra seguida de numeros, ejemplo: A00.\n"
        "- Días de incapacidad: número de días mencionado en el texto o duración de la incapacidad\n\n"
        "Instrucciones de razonamiento:\n"
        "1. Prioriza el primer nombre completo que aparezca del paciente o persona.\n"
        "2. Prioriza fechas cercanas a palabras clave.\n"
        "Ejemplo:\n"
        "Resultado:\n"
        "Nombre de la persona o paciente: Juan Jorge Pérez Sánchez\n"
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
                {"role": "system", "content": "Eres un asistente experto en extraer información de documentos médicos."},
                {"role": "user", "content": prompt}
            ]
        )

        print("\n=== RESULTADOS {}-{} ===".format(i+1, i+len(bloque_paginas)))
        print(response.choices[0].message.content)

        resultado_texto = response.choices[0].message.content

        def extraer_valor(campo):
            patron = rf"{re.escape(campo)}(?:\s*\([^)]*\))?\s*[:: ]\s*(.*)"
            m = re.search(patron, resultado_texto, re.IGNORECASE)
            valor = m.group(1).strip() if m else ""
    
    #Limpiar prefijos no deseados del nombre
            if campo == "Nombre de la persona":
                valor = re.sub(r'^(el estudiante|o paciente|paciente|estudiante):\s*', '', valor, flags=re.IGNORECASE).strip()
    
            return valor

#DESPUÉS (guarda Y envía correo):
    resultado_datos = {
    "Nombre de la persona": extraer_valor("Nombre de la persona"),
    "Documento": extraer_valor("Documento"),
    "Fecha de documento": extraer_valor("Fecha del documento"),
    "Fecha de inicio": extraer_valor("Fecha de inicio"),
    "Fecha de fin": extraer_valor("Fecha de fin"),
    "Diagnóstico (DX)": extraer_valor("Diagnóstico"),
    "Días de incapacidad": extraer_valor("Días de incapacidad")
}
    #guardar_en_sheets(resultado_datos)
    # enviar_correo_notificacion(resultado_datos) 

        #Limpiar imágenes temporales
    for f in os.listdir(carpeta_imagenes):
            os.remove(os.path.join(carpeta_imagenes, f))
    
def buscar_incapacidad():
    service = conectar_drive_usuario()
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")

    #Buscar solo correos no leídos
    result, data = mail.search(None, 'UNSEEN')
    encontrados = 0  

    if result == "OK":
        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            #Procesa PDFs directamente
            encontrados += 1
            if msg.is_multipart():
                for part in msg.walk():
                    filename = part.get_filename()
                    if filename and filename.endswith(".pdf"):
                        pdf_data = part.get_payload(decode=True)
                        subir_pdf_a_drive(filename, pdf_data, CARPETA_ID_DRIVE, service)
                        procesar_pdf_con_gpt(pdf_data)

            #Marca correo como leído para no procesarlo otra vez
            mail.store(num, '+FLAGS', '\\Seen')

    mail.logout()
    print(f"\nSe procesaron {encontrados} correo(s) con PDFs.")


if __name__ == "__main__":
    buscar_incapacidad()

