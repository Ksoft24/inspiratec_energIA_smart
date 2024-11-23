import cv2
import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import base64
import io

# Declarar 'cap' como global
cap = None

# URL de la cámara IP
url = "http://192.168.1.43:4747/video"

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

    # Enviar la imagen a la API
    api_url = "https://api.aimlapi.com/chat/completions"  # Cambia la URL según tu API
    payload = {
        "model": "gpt-4o",  # Cambia el modelo según la API
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe lo que ves en la imagen , analiza si puede ser un ladron y confirmalo en una etiqueta ('si','no') , responde solo en formato json con esta estructura {descripcion='',confidencia='',esladron=''}"},
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
        messagebox.showinfo("Descripción", description)
    else:
        messagebox.showerror("Error", f"Error al usar la API: {response.status_code} - {response.text}")

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

# Iniciar la captura de video
if initialize_camera():
    update_frame()

# Ejecutar la interfaz gráfica
window.protocol("WM_DELETE_WINDOW", lambda: (release_camera(), window.destroy()))
window.mainloop()
