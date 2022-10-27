import tensorflow as tf
import numpy as np
import os
import cv2

# Ruta para guardar las imagenes a procesar en el OCR
save_path = './static/'
# Ruta para cargar el modelo de ML
model_path = 'cedula_detection.tflite'

# Inicialización de la lista que almacenara las clases detectadas
classes = []

# Carga las clases que tiene el modelo de detección de objetos
f = open('cedula_detection.txt', "r")
for text in f:
    classes.append(text.strip())

# Colores aleatorios para los cuadros que pinta el detector
# de objetos según la clase detectada
COLORS = np.random.randint(0, 255, size=(len(classes), 3), dtype=np.uint8)

# Pre-procesamiento de la imagen


def preprocess_image(image_path, input_size):
    img = tf.io.read_file(image_path)
    img = tf.io.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.uint8)
    original_image = img
    resized_img = tf.image.resize(img, input_size)
    resized_img = resized_img[tf.newaxis, :]
    return resized_img, original_image

# Definición de las dimensiones de entrada del modelo
# Y la imagen a procesar en el modelo


def set_input_tensor(interpreter, image):
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image

# Definición de las dimensiones de salida del modelo


def get_output_tensor(interpreter, index):
    output_details = interpreter.get_output_details()[index]
    tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
    return tensor

# Detector de objetos en la imagen y  almacenamiento de resultados


def detect_objects(interpreter, image, threshold):
    set_input_tensor(interpreter, image)
    interpreter.invoke()

    scores = get_output_tensor(interpreter, 2)
    boxes = get_output_tensor(interpreter, 0)
    count = int(get_output_tensor(interpreter, 3))
    classes = get_output_tensor(interpreter, 1)

    results = []
    for i in range(count):
        if scores[i] >= threshold:
            result = {
                'bounding_box': boxes[i],
                'class_id': classes[i],
                'score': scores[i]
            }
            results.append(result)

    return results

# Función que da el inicio al proceso de detección de objetos


def run_odt_and_draw_results(image_path, interpreter, id_client, threshold=0.5):
    classes_detected = []
    Front_detected = False
    Back_detected = False

    _, input_height, input_width, _ = interpreter.get_input_details()[
        0]['shape']

    # Preprocesamiento de imagen
    preprocessed_image, original_image = preprocess_image(
        image_path,
        (input_height, input_width)
    )

    # Resultados
    results = detect_objects(
        interpreter, preprocessed_image, threshold=threshold)
    original_image_np = original_image.numpy().astype(np.uint8)

    # Procesamiento de los resultados
    for obj in results:
        ymin, xmin, ymax, xmax = obj['bounding_box']
        xmin = int(xmin * original_image_np.shape[1])
        xmax = int(xmax * original_image_np.shape[1])
        ymin = int(ymin * original_image_np.shape[0])
        ymax = int(ymax * original_image_np.shape[0])

        class_id = int(obj['class_id']) + 1

        classes_detected.append(class_id)

        # Clases detectadas, si detecto en la imagen la clase 4 (CEDULA)
        if 2 in classes_detected:
            Front_detected = True
            save_detection(image_path, class_id, xmin,
                           xmax, ymin, ymax, id_client)
        # Clases detectadas, si detecto en la imagen la clase 6 (ATRAS)

        if 3 and 1 in classes_detected:
            Back_detected = True
            save_detection(image_path, class_id, xmin,
                           xmax, ymin, ymax, id_client)

        # Recorte de cada clase en la imagen y almacenamiento

    ############################# MUESTRA EN LA IMAGEN LOS OBJETOS DETECTADOS #################################

    #   color = [int(c) for c in COLORS[class_id]]
    #   cv2.rectangle(original_image_np, (xmin, ymin), (xmax, ymax), color, 2)

    #   y = ymin - 15 if ymin - 15 > 15 else ymin + 15
    #   label = "{}: {:.0f}%".format(classes[class_id], obj['score'] * 100)
    #   cv2.putText(original_image_np, label, (xmin, y),
    #       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # cv2.imshow("results", original_image_np)

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return Front_detected, Back_detected

# Función para recortar las partes detectadas por el modelo y almacenarlas


def save_detection(image_path, class_id, xmin, xmax, ymin, ymax, id_client):

    # Imagen auxiliar
    aux_image = cv2.imread(image_path)

    if (classes[class_id] == "CODIGO"):
        try:
            code = aux_image[ymin-20:ymax+20, xmin-20:xmax+20]
        except:
            code = aux_image[ymin:ymax, xmin:xmax]
        code = cv2.detailEnhance(code, sigma_s=25, sigma_r=0.8)
        cv2.imwrite(save_path + f'/codigo_{id_client}.jpg', code)

    if(classes[class_id] == "CEDULA"):
        try:
            front = aux_image[ymin-25:ymax+25, xmin-20:xmax+20]
        except:
            front = aux_image[ymin:ymax, xmin:xmax]
        front = cv2.detailEnhance(front, sigma_s=5, sigma_r=0.1)
        cv2.imwrite(save_path + f'/cedula_frontal_{id_client}.jpg', front)

    if (classes[class_id] == "ATRAS"):
        try:
            back = aux_image[ymin-25:ymax+25, xmin-20:xmax+20]
        except:
            back = aux_image[ymin:ymax, xmin:xmax]
        back = cv2.detailEnhance(back, sigma_s=5, sigma_r=0.1)
        cv2.imwrite(save_path + f'/cedula_posterior_{id_client}.jpg', back)


def detect(id_client):
    # Carga el modelo y realiza su interpretación (Definición de tensors de entrada y salida)
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    Front = False
    Back = False

    # Procesamiento de las imagenes que llegan al API
    for file_name in os.listdir(save_path):

        if file_name == "Front.jpg" or file_name == "Back.jpg":

            input_image = save_path + "/" + file_name

            # Detección de objetos
            Front_detected, Back_detected = run_odt_and_draw_results(
                input_image,
                interpreter,
                id_client,
                threshold=0.1
            )

    # Luego del proceso de detección, se verifica las imagenes que se recortaron y si efectivamente se detecto
    # cada objeto en la imagen.
    files = os.listdir(save_path)

    if f"cedula_frontal_{id_client}.jpg" in files and Front_detected == True:
        Front = True

    if f"cedula_posterior_{id_client}.jpg" in files and Back_detected == True:
        Back = True

    if f"cedula_posterior_{id_client}.jpg" in files and f"cedula_frontal_{id_client}.jpg" in files and Back_detected == True:
        Front = True
        Back = True

    return Front, Back
