import cv2
import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import base64
import io
import json
import re
import pygame
import paho.mqtt.client as mqtt
import time
from openai import OpenAI

# Declarar 'cap' como global
cap = None

# URL de la cámara IP
url = "http://192.168.1.33:4747/video"

# MQTT
mqtt_broker = "161.132.40.127"
mqtt_port = 1883
username = "adminmqtt"
password = "calero2020"
topic1 = "1/foco"

pygame.mixer.init()


def on_message(client, userdata, message):
    global automatico, foco_value, foto
    payload = message.payload.decode('utf-8')
    if message.topic == topic1:
        foco_value = payload
    
# Función para inicializar la captura de video
def initialize_camera():
    global cap
    if cap is None:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
            return False
    return True

# Función para capturar la imagen y enviarla a la API
def capture_and_send_image():
    global cap
    if cap is None or not cap.isOpened():
        if not initialize_camera():
            return

    # Capturar un frame
    ret, frame = cap.read()

    if not ret:
        messagebox.showerror("Error", "No se pudo capturar la imagen.")
        return
    
    # Convertir la imagen a base64
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    modelo="openai"
    description="-"

    if modelo=="aimlapi":

      # Enviar la imagen a la API
        api_url = "https://api.aimlapi.com/chat/completions"  # Cambia la URL según tu API
        payload = {
            "model": "gpt-4o",  # Cambia el modelo según la API
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe lo que ves en la imagen , analiza si puede ser un ladron , para esto deberas considerar personas que tengan cubiero el rostro con una pasamontaña o bufanda cubriendo su boca , o que usen antifaces, o cubran parte de su rostro con alguna prenda  y confirmalo en una etiqueta ('si','no'), asi misMo cuenta la cantidad de personas y agregalo a la etiqueta , responde solo en formato json con esta estructura {descripcion='',confidencia='',esladron='',cantidadpersonas=''}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                    ]
                }
            ],
            "max_tokens": 300
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": ""  # Reemplaza con tu clave de API
        }

        # Realizar la solicitud a la API
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 201:
            result = response.json()
            description = result.get("choices", [{}])[0].get("message", {}).get("content", "Sin descripción")
            
            
            print(description)
        else:
            messagebox.showerror("Error", f"Error al usar la API: {response.status_code} - {response.text}")
    
    elif modelo=="openai":

        client = OpenAI(api_key="")

        response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe lo que ves en la imagen, analiza si puede ser un ladrón. Para esto deberás considerar personas que tengan cubierto el rostro con una pasamontaña, bufanda cubriendo su boca, o que usen antifaces, o cubran parte de su rostro con alguna prenda. Confirmalo en una etiqueta ('si', 'no'). Asimismo, cuenta la cantidad de personas y agrégalo a la etiqueta. Responde solo en formato JSON con esta estructura {descripcion='', confidencia='', esladron='', cantidadpersonas=''}."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        },
                    },
                ],
            }
        ],
    )

    # Procesar la respuesta
    if response:
        #print(response.choices[0])
        result = response.choices[0].message.content  # Accede al contenido del mensaje
        description=result
        print("##")
        print(description)
    else:
        print("No se obtuvo una respuesta de la API.")

    if description!="":
        try:
            # Intentar analizar el JSON de la respuesta
            cleaned_text = description.replace("`", "")
            cleaned_text = cleaned_text.replace("json", "")
            cleaned_text = cleaned_text.replace("`", "")

            messagebox.showinfo("Descripción limpia", cleaned_text)

            # Parsear el JSON limpiado
            result_json = json.loads(cleaned_text)
            
            esladron = result_json.get("esladron", "no")  # Valor por defecto: "no"

            if esladron == "si":
                print("¡Ladrón detectado!")
                sonidoalerta()
                
            else:
                print("No hay amenaza.")
                messagebox.showinfo("Estado", "No hay amenaza.")
            
            cantidadpersonas = result_json.get("cantidadpersonas", "0")  # Valor por defecto: "no"
            if cantidadpersonas=="0":
              enviar_mqtt(topic1, '0')
            else:
              enviar_mqtt(topic1, '1')  

        except json.JSONDecodeError:
            print("La respuesta no es un JSON válido:", description)
            messagebox.showerror("Error", "La respuesta de la API no es válida.")

    

# enviar mqtt
def enviar_mqtt(topic, mensaje):
    result = client.publish(topic, mensaje)
    status = result.rc
    if status == 0:
        print(f"Mensaje '{mensaje}' enviado al tópico '{topic}'")
    else:
        print(f"Error al enviar mensaje al tópico '{topic}'")

def sonidoalerta():
        # Generar un pitido cargando un archivo de sonido, por ejemplo
    pygame.mixer.Sound.play(pygame.mixer.Sound('alarma.mp3'))

    # Para que no termine el programa antes de oír el sonido
    pygame.time.delay(1000)

# Función para actualizar la imagen en tiempo real
def update_frame():
    global cap
    if cap is None or not cap.isOpened():
        if not initialize_camera():
            return

    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "No se pudo capturar el frame")
        return

    # Convertir la imagen de OpenCV a formato compatible con Tkinter
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    img_tk = ImageTk.PhotoImage(img)

    # Actualizar la imagen mostrada en la ventana
    panel.config(image=img_tk)
    panel.image = img_tk

    # Llamar a esta función cada 10 ms para actualizar el video
    panel.after(10, update_frame)

# Función para liberar los recursos
def release_camera():
    global cap
    if cap is not None:
        cap.release()

# Crear la ventana de la interfaz gráfica
window = tk.Tk()
window.title("Captura de Imagen y Envío a API")

# Crear un panel para mostrar el video
panel = tk.Label(window)
panel.pack()

# Crear el botón para capturar y enviar la imagen
capture_button = tk.Button(window, text="Capturar Imagen", command=capture_and_send_image)
capture_button.pack(pady=20)

client = mqtt.Client()
client.username_pw_set(username, password)
client.connect(mqtt_broker, mqtt_port, 60)
client.subscribe([(topic1, 0)])
client.on_message = on_message
client.loop_start()

# Iniciar la captura de video
if initialize_camera():
    update_frame()

# Ejecutar la interfaz gráfica
window.protocol("WM_DELETE_WINDOW", lambda: (release_camera(), window.destroy()))
window.mainloop()
