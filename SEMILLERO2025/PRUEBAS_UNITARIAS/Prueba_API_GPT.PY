from openai import OpenAI

client = OpenAI(api_key="Censurada el Api_Key por privacidad") #Api_key del modelo Gpt

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Eres un asistente útil."},
        {"role": "user", "content": "Hola, ¿funciona mi API?"}
    ]
)

print(response.choices[0].message.content)


## respuesta esperada


"""Hola, para verificar si tu API está funcionando, podrías seguir estos pasos básicos:

1. **Prueba de Conexión:** Usa herramientas como `curl`, Postman, o un simple navegador web para hacer una solicitud a la API. Por ejemplo, si tu API tiene un endpoint en `http://tudominio.com/api/ejemplo`, intenta acceder a esa URL.

2. **Revisión de Respuesta HTTP:** Verifica el código de estado HTTP que recibes. Un código 200 indica éxito, mientras que códigos como 404 (no encontrado) o 500 (error del servidor) indican problemas.

3. **Revisa los Logs del Servidor:** Si tienes acceso a los registros del servidor, revísalos para identificar si hay errores cuando se reciben solicitudes a la API.

4. **Pruebas Automatizadas:** Si has escrito pruebas para tu API, ejecute esas pruebas para verificar que todas las funcionalidades clave están operativas.

5. **Documentación de la API:** Verifica que estás haciendo las solicitudes correctamente de acuerdo a la documentación de la API, incluyendo los métodos HTTP (GET, POST, etc.), headers necesarios y el formato de los datos.

6. **Verificación de Ambiente:** Asegúrate de que tu API esté ejecutándose en el ambiente correcto, ya sea localmente, en un servidor de pruebas o en producción.

Si después de estos pasos sigues teniendo problemas, podrías proporcionar más detalles sobre el error que estás recibiendo y estaré encantado de intentar ayudarte más."""