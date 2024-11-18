import cv2
import numpy as np
import urllib3
import time

def load_yolo():
   # Cargar el modelo YOLO, configuración y labels
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layers_names = net.getLayerNames()
    output_layers = [layers_names[i-1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    return net, classes, colors, output_layers

    #Detectar objetos en el frame usando YOLO
def detect_objects(frame, net, output_layers, classes, colors):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Información que se muestra en la ventana
    class_ids = []
    confidences = []
    boxes = []

    #  detecciones
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Coordenadas del objeto
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectángulo
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    font = cv2.FONT_HERSHEY_PLAIN
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            color = colors[class_ids[i]]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y + 30), font, 2, color, 2)

    return frame

#main
def stream_esp32_cam():
    # Cargar YOLO
    net, classes, colors, output_layers = load_yolo()
    
    # Configurar urllib3 importante usar esta version
    http = urllib3.PoolManager()
    url = 'http://192.168.100.14:81/stream'
    
    print(f"Conectando a: {url}")
    
    # Crear ventana
    cv2.namedWindow("ESP32-CAM Stream con YOLO", cv2.WINDOW_AUTOSIZE)
    
    try:
        response = http.request('GET', url, preload_content=False)
        bytes_array = bytes()
        
        while True:
            chunk = response.read(1024)
            if not chunk:
                break
                
            bytes_array += chunk
            a = bytes_array.find(b'\xff\xd8')
            b = bytes_array.find(b'\xff\xd9')
            
            if a != -1 and b != -1:
                jpg = bytes_array[a:b+2]
                bytes_array = bytes_array[b+2:]
                
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # Aplicar YOLO al frame
                    frame = detect_objects(frame, net, output_layers, classes, colors)
                    
                    # Mostrar el frame
                    cv2.imshow("ESP32-CAM Stream con YOLO", frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Error al decodificar el frame")
                    time.sleep(0.1)
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nSugerencias de solución:")
        print("1. Verifica que la ESP32-CAM sigue conectada")
        print("2. Verifica que los archivos de YOLO están en el directorio correcto")
        print("3. Intenta refrescar el stream en el navegador")
        print("4. Reinicia la ESP32-CAM si el problema persiste")
    
    finally:
        try:
            response.release()
        except:
            pass
        cv2.destroyAllWindows()
# Parte importante, manualamente no logre instalar urllib3, pero si lo hacia desde el codigo si que funciono, 
# ya no es necesario tenrlo, alemnos no en mi pc, pero dejo esta parte, por si se requiere en algun momento
if __name__ == "__main__":
    try:
        import urllib3
    except ImportError:
        print("urllib3 no está instalado. Instalando...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'urllib3'])
        print("urllib3 instalado correctamente")
    
    while True:
        try:
            stream_esp32_cam()
            break
        except KeyboardInterrupt:
            print("\nPrograma terminado por el usuario")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")
            print("Reintentando en 3 segundos...")
            time.sleep(3)