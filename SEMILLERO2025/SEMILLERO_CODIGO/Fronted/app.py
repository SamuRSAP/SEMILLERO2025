import streamlit as st
from database import Database
import sys
import io
import platform
import psutil
import datetime
from contextlib import redirect_stdout
import SEMILLERO
import json
        

#Configuración de la página
st.set_page_config(
    page_title="Sistema de Incapacidades ",
    page_icon= r"ruta de la imagen",
    layout="wide"
)

#LLama a la base de datos
db = Database()

#Inicializa la sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'ejecutando' not in st.session_state:
    st.session_state.ejecutando = False
if 'color_fondo' not in st.session_state:
    st.session_state.color_fondo = None
if 'color_texto' not in st.session_state:
    st.session_state.color_texto = None

def login_page():
    """Página de inicio de sesión"""
    st.markdown("<h2 style='text-align: center;'>💻 Sistema de Incapacidades Médicas 📄</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            flex-grow: 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col2:
        tab1, tab2, tab3 = st.tabs(["Iniciar Sesión", "Registrarse", "Cambiar Contraseña"])
        
        # TAB 1: LOGIN
        with tab1:
            st.markdown("<h4 style='text-align: center;'>Iniciar Sesión</h4>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuario", key="login_user")
                password = st.text_input("Contraseña", type="password", key="login_pass")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
                if submit:
                    if username and password:
                        if db.verificar_usuario(username, password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success("¡Inicio de sesión exitoso!")
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos")
                    else:
                        st.warning("Por favor completa todos los campos")
            
            st.info("💡 ¿Olvidaste tu contraseña? Ve a la pestaña 'Cambiar Contraseña'")
        
        # TAB 2: REGISTRO
        with tab2:
            st.markdown("<h4 style='text-align: center;'>Crear Nueva Cuenta</h4>", unsafe_allow_html=True)
            
            with st.form("register_form"):
                new_username = st.text_input("Usuario", key="reg_user")
                new_email = st.text_input("Email (opcional)", key="reg_email")
                new_password = st.text_input("Contraseña", type="password", key="reg_pass")
                new_password_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_pass_confirm")
                submit_register = st.form_submit_button("Registrarse", use_container_width=True)
                
                if submit_register:
                    if not new_username or not new_password:
                        st.warning("Usuario y contraseña son obligatorios")
                    elif new_password != new_password_confirm:
                        st.error("Las contraseñas no coinciden")
                    elif len(new_password) < 4:
                        st.error("La contraseña debe tener al menos 4 caracteres")
                    else:
                        success, message = db.crear_usuario(new_username, new_password, new_email)
                        if success:
                            st.success(message)
                            st.info("Ahora puedes iniciar sesión")
                        else:
                            st.error(message)
        
        # TAB 3: CAMBIAR CONTRASEÑA
        with tab3:
            st.markdown("<h4 style='text-align: center;'>🔐 Cambiar Contraseña</h4>", unsafe_allow_html=True)
            st.info("Ingresa tu usuario y tu nueva contraseña")
            
            with st.form("cambiar_password_form"):
                username_cambio = st.text_input("Usuario", key="cambio_user")
                nueva_password = st.text_input("Nueva Contraseña", type="password", key="nueva_pass")
                confirmar_password = st.text_input("Confirmar Nueva Contraseña", type="password", key="confirmar_pass")
                submit_cambio = st.form_submit_button("Cambiar Contraseña", use_container_width=True)
                
                if submit_cambio:
                    if not username_cambio or not nueva_password or not confirmar_password:
                        st.warning("⚠️ Por favor completa todos los campos")
                    elif nueva_password != confirmar_password:
                        st.error("❌ Las contraseñas no coinciden")
                    elif len(nueva_password) < 4:
                        st.error("❌ La contraseña debe tener al menos 4 caracteres")
                    else:
                        # Verificar que el usuario existe
                        if db.usuario_existe(username_cambio):
                            if db.cambiar_contrasena(username_cambio, nueva_password):
                                st.success("✅ Contraseña cambiada exitosamente")
                                st.info("Ahora puedes iniciar sesión con tu nueva contraseña")
                            else:
                                st.error("❌ Error al cambiar la contraseña")
                        else:
                            st.error("❌ El usuario no existe")

def procesar_pdf(uploaded_file):
    """Procesa el PDF subido por el usuario"""
    try:
        pdf_bytes = uploaded_file.read()
        uploaded_file.seek(0)  
        
        service = SEMILLERO.conectar_drive_usuario()
        
        output = io.StringIO()
        with redirect_stdout(output):
            #Sube a Drive
            SEMILLERO.subir_pdf_a_drive(uploaded_file.name, pdf_bytes, SEMILLERO.CARPETA_ID_DRIVE, service)
            
            #Procesa con GPT
            SEMILLERO.procesar_pdf_con_gpt(pdf_bytes)
        
        return True, output.getvalue()
    except Exception as e:
        return False, str(e)

def main_app():
    """Aplicación principal después del login"""
    
    if 'color_fondo' not in st.session_state or st.session_state.color_fondo is None:
        try:
            with open('colores_usuarios.json', 'r') as f:
                colores_guardados = json.load(f)
                if st.session_state.username in colores_guardados:
                    st.session_state.color_fondo = colores_guardados[st.session_state.username]["fondo"]
                    st.session_state.color_texto = colores_guardados[st.session_state.username]["texto"]
                else:
                    st.session_state.color_fondo = "#212121"
                    st.session_state.color_texto = "#FFFFFF"
        except:
            st.session_state.color_fondo = "#212121"
            st.session_state.color_texto = "#FFFFFF"
    
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        st.markdown("---")
        
        st.subheader("Navegación")
        menu = st.radio(
            "Selecciona una opción:",
            ["🏠 Inicio", "▶️ Procesar Incapacidad", "📊 Historial", "👤 Info del Usuario", "⚙️ Personalización"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.color_fondo = None
            st.session_state.color_texto = None
            st.rerun()
    
    #PÁGINA: INICIO
    if menu == "🏠 Inicio":
        st.title("📄 Sistema de Gestión de Incapacidades")
        st.markdown("---")
        
        st.info("👋 Bienvenido al sistema automatizado de procesamiento de incapacidades médicas")
        
        st.markdown("---")
        
        st.subheader("¿Qué hace este sistema?")
        st.markdown("""
        1. 📤 **Subes un PDF** de incapacidad médica
        2. 📄 **Extrae datos** automáticamente con GPT-4
        3. ☁️ **Sube a la Nube de Google** el archivo
        4. 📊 **Guarda en la bade de datos de Google** la información
        5. ✉️ **Envía correo** de notificación automático
        """)
    
    #PÁGINA: PROCESAR INCAPACIDAD
    elif menu == "▶️ Procesar Incapacidad":
        st.title("▶️ Procesar Incapacidad Médica")
        st.markdown("---")
        
        st.info("📤 Sube un archivo PDF de incapacidad médica para procesarlo automáticamente")
        
        #Sube el archivo
        uploaded_file = st.file_uploader(
            "Selecciona el PDF de incapacidad",
            type=['pdf'],
            help="Arrastra aquí o haz clic para seleccionar un PDF"
        )
        
        if uploaded_file is not None:
            #Muestra info del archivo
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.success(f"✅ Archivo cargado: **{uploaded_file.name}**")
            with col_info2:
                st.info(f"📊 Tamaño: {uploaded_file.size / 1024:.2f} KB")
            
            st.markdown("---")
            
            #Botón para procesar
            if st.button("🎇 PROCESAR INCAPACIDAD", type="primary", use_container_width=True):
                st.session_state.ejecutando = True
                
                with st.spinner("🔄 Procesando PDF... Esto puede tomar unos minutos"):
                    success, output = procesar_pdf(uploaded_file)
                
                st.session_state.ejecutando = False
                
                try:
                    if success:
                        #Guarda en historial
                        db.guardar_ejecucion(
                            usuario=st.session_state.username,
                            correos_proc=0,
                            pdfs_proc=1,
                            correos_env=1,
                            estado="Completado",
                            detalles=f"PDF procesado: {uploaded_file.name}"
                        )
                        
                        #Guarda el resultado 
                        st.session_state.ultimo_resultado = {
                            'success': True,
                            'filename': uploaded_file.name,
                            'output': output
                        }
                        
                        st.balloons()
                        st.rerun()
                        
                    else:
                
                        db.guardar_ejecucion(
                            usuario=st.session_state.username,
                            correos_proc=0,
                            pdfs_proc=0,
                            correos_env=0,
                            estado="Error",
                            detalles=output[:500]
                        )
                        
                        st.session_state.ultimo_resultado = {
                            'success': False,
                            'filename': uploaded_file.name,
                            'output': output
                        }
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error al guardar en historial: {str(e)}")
        else:
            st.warning("⚠️ Por favor sube un archivo PDF para continuar")
        
        if 'ultimo_resultado' in st.session_state and st.session_state.ultimo_resultado:
            resultado = st.session_state.ultimo_resultado
            
            st.markdown("---")
            
            col_close1, col_close2, col_close3 = st.columns([3, 1, 3])
            with col_close2:
                if st.button("❌ Cerrar", key="cerrar_resultado", help="Cerrar resultado"):
                    st.session_state.ultimo_resultado = None
                    st.rerun()
            
            if resultado['success']:
                st.success("✅ Incapacidad procesada exitosamente")
                st.info(f"✓ Archivo procesado: {resultado['filename']}")
                
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    st.metric("📄 PDF Procesado", "✓", delta="Completado")
                with col_r2:
                    st.metric("☁️ Subido a la Nube", "✓", delta="OK")
                with col_r3:
                    st.metric("📊 Guardado en Base de Datos", "✓", delta="OK")
                
                st.markdown("---")
                st.subheader("👤 Información del Usuario")
                
                nombre_user, doc_user = db.obtener_info_usuario(st.session_state.username)
                
                if nombre_user and doc_user:
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric("Nombre", nombre_user)
                    with col_info2:
                        st.metric("Documento", doc_user)
                else:
                    st.warning("⚠️ No has completado tu información. Ve a 'Info del Usuario' para agregarla.")
                
                st.markdown("---")
                
                with st.expander("📋 Ver detalles del proceso"):
                    st.code(resultado['output'])
                
                st.markdown("---")
                st.subheader("✏️ Editar Información Extraída")
                
                nombre_user, doc_user = db.obtener_info_usuario(st.session_state.username)
                
                output_lines = resultado['output'].split('\n')
                
                fecha_inicio = ""
                fecha_fin = ""
                diagnostico = ""
                fecha_doc = ""
                dias_incap = ""
                correo = ""
                
                for line in output_lines:
                    if "Fecha de inicio:" in line:
                        fecha_inicio = line.split(":")[-1].strip()
                    elif "Fecha de fin:" in line:
                        fecha_fin = line.split(":")[-1].strip()
                    elif "Diagnóstico (DX):" in line:
                        diagnostico = line.split(":")[-1].strip()
                    elif "Fecha del documento:" in line:
                        fecha_doc = line.split(":")[-1].strip()
                    elif "Días de incapacidad:" in line:
                        dias_incap = line.split(":")[-1].strip()
                    elif "Correo enviado a" in line:
                        correo = line.split(":")[-1].strip()

                with st.form("editar_info_form"):
                    st.write("**Nombre de la persona o paciente:**", nombre_user or "No disponible")
                    st.write("**Documento:**", doc_user or "No disponible")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fecha_inicio_edit = st.text_input("Fecha de inicio", value=fecha_inicio, key="fecha_inicio_edit")
                        diagnostico_edit = st.text_input("Diagnóstico (DX)", value=diagnostico, key="diagnostico_edit")
                        dias_incap_edit = st.text_input("Días de incapacidad", value=dias_incap, key="dias_incap_edit")
                    
                    with col2:
                        fecha_fin_edit = st.text_input("Fecha de fin", value=fecha_fin, key="fecha_fin_edit")
                        fecha_doc_edit = st.text_input("Fecha del documento", value=fecha_doc, key="fecha_doc_edit")
                    
                    submit_edicion = st.form_submit_button("💾 Guardar Cambios y Enviar Correo", use_container_width=True)
                    
                    if submit_edicion:
  
                        datos_finales = {
                            'Nombre de la persona': nombre_user,
                            'Documento': doc_user,
                            'Fecha de documento': fecha_doc_edit,
                            'Fecha de inicio': fecha_inicio_edit,
                            'Fecha de fin': fecha_fin_edit,
                            'Diagnóstico (DX)': diagnostico_edit,
                            'Días de incapacidad': dias_incap_edit
                        }
                        
                        try:
                            #Guarda en Google Sheets
                            SEMILLERO.guardar_en_sheets(datos_finales)
                            
                            #Envia correo
                            SEMILLERO.enviar_correo_notificacion(datos_finales)
                            
                            st.success("✅ Datos guardados en Base de Datos y correo enviado correctamente")
                            st.info(f"📧 Correo enviado y guardado para: {nombre_user} - Doc: {doc_user}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            
                                            
                st.markdown("---")
                col_close_bottom1, col_close_bottom2, col_close_bottom3 = st.columns([3, 1, 3])
                with col_close_bottom2:
                    if st.button("❌ Cerrar", key="cerrar_resultado_bottom", type="secondary", use_container_width=True):
                        st.session_state.ultimo_resultado = None
                        st.rerun()

            else:
                st.error("❌ Error al procesar el PDF")
                with st.expander("Ver error completo"):
                    st.code(resultado['output'])
        
        st.markdown("---")
        st.subheader("📝 Proceso Automático")
        st.markdown("""
        El sistema realizará los siguientes pasos:
        - 🔍 Lectura del PDF 
        - 🤖 Análisis con GPT-4 para extraer datos médicos
        - ☁️ Subida automática a la Nube
        - 📊 Registro en Base de Datos
        - ✉️ Envío de correo de notificación
        """)
    
    #PÁGINA: HISTORIAL
    elif menu == "📊 Historial":
        st.title("📊 Historial de Ejecuciones")
        st.markdown("---")
        
        if st.button("🔄 Actualizar historial"):
            st.rerun()
        
        historial = db.obtener_historial(usuario=st.session_state.username, limite=100)
        
        if historial and len(historial) > 0:
            st.success(f"Se encontraron {len(historial)} ejecuciones registradas")
            
            import pandas as pd

            df = pd.DataFrame(historial)
            df.columns = ['ID', 'Fecha', 'Usuario', 
                          'PDFs Proc.', 'Correos Env.', 'Estado', 'Detalles']
            
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader("📈 Estadísticas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_pdfs = df['PDFs Proc.'].sum()
                st.metric("Total PDFs Procesados", int(total_pdfs))
            
            with col2:
                total_enviados = df['Correos Env.'].sum()
                st.metric("Total Correos Enviados", int(total_enviados))
            
            with col3:
                exitosos = len(df[df['Estado'] == 'Completado'])
                st.metric("Ejecuciones Exitosas", exitosos)
            
            with col4:
                errores = len(df[df['Estado'] == 'Error'])
                st.metric("Errores", errores)
            
        else:
            st.info("📭 No hay ejecuciones registradas aún. Procesa una incapacidad para ver el historial.")
        
    #PÁGINA: INFORMACIÓN DEL USUARIO
    elif menu == "👤 Info del Usuario":
        st.title("👤 Información del Usuario")
        st.markdown("---")

        st.info("📝 Completa tu información personal para usar en el procesamiento de documentos")

        nombre_guardado, doc_guardado = db.obtener_info_usuario(st.session_state.username)

        with st.form("info_usuario_form"):
            nombre = st.text_input("Nombre Completo", value=nombre_guardado or "", placeholder="Ej: Juan Pérez García")
            documento = st.text_input("Número de Documento", value=doc_guardado or "", placeholder="Ej: 1234567890")
            
            submit = st.form_submit_button("💾 Guardar Información", use_container_width=True)
            
            if submit:
                if nombre and documento:
                    db.guardar_info_usuario(st.session_state.username, nombre, documento)
                    st.success("✅ Información guardada exitosamente")
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor completa todos los campos")
        
        if nombre_guardado and doc_guardado:
            st.markdown("---")
            st.subheader("📋 Información Actual")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Nombre", nombre_guardado)
            with col2:
                st.metric("Documento", doc_guardado)

    
    #PÁGINA: CONFIGURACIÓN
    elif menu == "⚙️ Personalización":
        st.title("⚙️ Personalización del Sistema")
        st.markdown("---")

        st.info("🖌️ Cambia el color de fondo de la aplicación")

        #Opciones de color
        colores = {
            "Gris oscuro": "#212121",
            "Negro": "#000000",
            "Vino Tinto": "#571212",
            "Amarillo Oscuro": "#575012",
            "Verde Oscuro": "#11400B",
            "Azul Oscuro": "#0B2B40",
            "Morado": "#180B40",
            "Rosado Oscuro": "#400B38",
        }

        #Selector y botón
        color_seleccionado = st.selectbox("🎨 Elige un color de fondo:", list(colores.keys()))
        aplicar = st.button("Aplicar color", type="primary", use_container_width=True)

        def es_color_oscuro(hex_color):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            brillo = (r * 299 + g * 587 + b * 114) / 1000
            return brillo < 128

        #Aplicar color al hacer clic
        if aplicar:
            color_hex = colores[color_seleccionado]
            st.session_state.color_fondo = color_hex

            if es_color_oscuro(color_hex):
                st.session_state.color_texto = "#FFFFFF"
            else:
                st.session_state.color_texto = "#000000"
            
            color_data = {
                st.session_state.username: {
                    "fondo": st.session_state.color_fondo,
                    "texto": st.session_state.color_texto
                }
            }
            
            try:
                with open('colores_usuarios.json', 'r') as f:
                    todos_colores = json.load(f)
            except:
                todos_colores = {}
            
            todos_colores.update(color_data)
            
            with open('colores_usuarios.json', 'w') as f:
                json.dump(todos_colores, f)
            
            st.success(f"👍 Color de fondo cambiado a {color_seleccionado}")

    if st.session_state.color_fondo and st.session_state.color_texto:
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-color: {st.session_state.color_fondo} !important;
                    color: {st.session_state.color_texto} !important;
                }}
                .sidebar {{
                    background-color: {st.session_state.color_fondo} !important;
                    color: {st.session_state.color_texto} !important;
                }}
                .stRadio [aria-selected="true"] {{
                    color: {st.session_state.color_texto} !important;
                }}
                .stMarkdown, .stText, .stTitle, h1, h2, h3, h4, h5, h6, p, span {{
                    color: {st.session_state.color_texto} !important;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

#Logica principal
if st.session_state.logged_in:
    main_app()
else:
    login_page()