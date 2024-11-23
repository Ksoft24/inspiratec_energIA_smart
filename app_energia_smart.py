import cv2

# URL de la cámara IP
url = "http://192.168.1.43:4747/video"

# Iniciar la captura de video
cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo acceder a la cámara.")
        break

    # Mostrar el video en tiempo real
    cv2.imshow("Cámara IP", frame)

    # Presionar 'q' para salir
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
