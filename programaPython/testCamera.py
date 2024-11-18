import cv2
import numpy as np
import urllib3
import time

def stream_esp32_cam():
    # Configurar urllib3
    http = urllib3.PoolManager()
    url = 'http://192.168.100.14:81/stream'
    
    print(f"Conectando a: {url}")
    
    # Crear ventana
    cv2.namedWindow("ESP32-CAM Stream", cv2.WINDOW_AUTOSIZE)
    
    try:
        # Realizar la petición con stream=True para manejar el stream MJPEG
        response = http.request('GET', url, preload_content=False)
        
        # Búfer para almacenar los bytes de la imagen
        bytes_array = bytes()
        
        while True:
            # Leer chunk por chunk
            chunk = response.read(1024)
            if not chunk:
                break
                
            # Agregar el chunk al búfer
            bytes_array += chunk
            
            # Buscar el inicio y fin de un frame JPEG
            a = bytes_array.find(b'\xff\xd8')  # JPEG Start
            b = bytes_array.find(b'\xff\xd9')  # JPEG End
            
            if a != -1 and b != -1:
                # Extraer el frame JPEG
                jpg = bytes_array[a:b+2]
                # Limpiar el búfer
                bytes_array = bytes_array[b+2:]
                
                # Decodificar la imagen
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # Mostrar el frame
                    cv2.imshow("ESP32-CAM Stream", frame)
                    
                    # Esperar por la tecla 'q' para salir (1ms de delay)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Error al decodificar el frame")
                    time.sleep(0.1)  # Pequeña pausa para evitar CPU alto
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nSugerencias de solución:")
        print("1. Verifica que la ESP32-CAM sigue conectada")
        print("2. Intenta refrescar el stream en el navegador")
        print("3. Reinicia la ESP32-CAM si el problema persiste")
    
    finally:
        # Limpiar
        try:
            response.release()
        except:
            pass
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Primero asegurarse de que urllib3 está instalado
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