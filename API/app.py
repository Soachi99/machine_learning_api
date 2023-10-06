import os
import io
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import CedulaDetection
import base64
import logging
import cv2
import numpy as np
import base64
from qreader import QReader
import json

save_path = 'static'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = save_path
imageList = []
CORS(app, resources={r"*": {"origins": "*"}})


@app.route('/')
def upload_files():
    return render_template('form.html')

@app.route('/enhance', methods=['POST'])
def enhance():
    response = {}
    data = request.json;
    selfie = data.get('selfie');

    header, data_selfie = selfie.split(',', 1)

    image_data = base64.b64decode(data_selfie)


    np_array = np.frombuffer(image_data, np.uint8)
    im=cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
    #cv2.imshow("original", im)

    im_enhance = cv2.detailEnhance(im, sigma_s=6, sigma_r=0.4)

    #cv2.imshow("result", im_enhance)

    retval, buffer = cv2.imencode('.jpg', im_enhance)
    jpg_as_text = base64.b64encode(buffer)
   
    #concatenar data:image/jpeg;base64,
    response = {"image": str(jpg_as_text)}
   
    return jsonify(response)

@app.route('/uploader', methods=['POST'])
def uploader():
    if request.method == "POST":

        id_client = request.form.get('id')
        document = request.form.get('side')
        logging.warning(document)
        savephoto()
        data_hist = checkHistogram()
        Data = {}

        if data_hist['success'] == True:
            try:
                isFront, isBack = CedulaDetection.detect(id_client)

                if isFront != False or isBack != False:

                    Data["success"] = True

                    # image_64_front, image_64_back, image_64_code = images_64_encode(
                    #     id_client)
                    # if image_64_back != None:
                    #     Data["Imagen Cedula Posterior"] = str(
                    #         image_64_back)
                    # if image_64_front != None:
                    #     Data["Imagen Cedula Frontal"] = str(image_64_front)
                    # if image_64_code != None:
                    #     Data["Imagen Codigo"] = str(image_64_code)

                    if isFront == True and isBack == True:
                        try:
                            os.remove(
                                save_path + f'/cedula_frontal_{id_client}.jpg')
                            os.remove(
                                save_path + f'/cedula_posterior_{id_client}.jpg')
                            os.remove(save_path + f'/codigo_{id_client}.jpg')
                        except:
                            print("No existe imagen")

                    if isFront == False and isBack == True:
                        try:
                            os.remove(save_path + f'/codigo_{id_client}.jpg')
                            os.remove(
                                save_path + f'/cedula_posterior_{id_client}.jpg')
                        except:
                            print("No existe imagen")

                return jsonify(Data)
            except:
                Data = {
                    "success": False, "mensaje": "No se puede validar la cédula correctamente, tome la foto de nuevo"}
                logging.warning("No se puede procesar la cédula correctamente")
                return jsonify(Data)

        else:
            return jsonify(data_hist)


@app.route('/checkselfie', methods=['POST'])
def checkphoto():
    id_client = request.form.get('id')
    savephotoselfie()
    data = checkHistogram(id_client)

    if data["success"] == True:
        data = {}
        data = checkEyesOpen(id_client)
        try:
            os.remove(save_path + f'/Selfie_{id_client}.jpg')
        except:
            print("No existe imagen")

    return jsonify(data)

@app.route('/readqr', methods=['POST'])
def readqr():
    response = {}
    data = request.json;
    image = data.get('image');

    header, data_image = image.split(',', 1)

    image_data = base64.b64decode(data_image)   

    np_array = np.frombuffer(image_data, np.uint8)
    im=cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)    

    original = im.copy()     
    
    qreader = QReader(model_size='l', reencode_to= 'utf-8')
    
    try:
        decode_info = qreader.detect_and_decode(image= original)    
        
        if(decode_info[0] != None):
            print(decode_info[0])
            response["error"] = False
            response["decode"] = replaceEspecialCharacters(decode_info[0])
            response["message"] = "Exito"
        else:
            raise Exception("Sin información")
    except:
        response["error"] = True
        response["decode"] = ""
        response["message"] = "No se pudo leer el QR, intenta de nuevo"

    response = json.dumps(response, ensure_ascii= False)   

    response = json.loads(response)
    
    return jsonify(response)

## PANAMEAÑ

def replaceEspecialCharacters(text):
    replacements_dict = {
    'ﾍ': 'I',
    'ﾓ': 'O',
    'ﾑ': 'Ñ',      
    'ﾃ': 'A',   
    'ﾁ': 'A',
    '羨': 'Ñ',
    '−': '|'
    }

    text = text.translate(str.maketrans(replacements_dict))

    return text.replace('AÑ', 'NA').replace('Ñ', 'N')

def checkEyesOpen(id_client):
    data = {}
    selfie = cv2.imread(save_path + f"/Selfie_{id_client}.jpg")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')

    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')

    face = face_cascade.detectMultiScale(
        selfie, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(face) > 0:
        eyes = eye_cascade.detectMultiScale(
            selfie, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))

        if (len(eyes) >= 2):
            logging.warning(
                "Ojos detectados correctamente")
            data["success"] = True

        else:
            logging.warning(
                "Ojos cerrados o no se detecta ojos en la foto")
            data["mensaje"] = "Tus ojos no están abiertos en la foto, intenta nuevamente."
            data["success"] = False

    else:
        logging.warning(
            "No se detecto rostro")
        data["mensaje"] = "No se detecta el rostro de la persona, intenta nuevamente."
        data["success"] = False

    # for (ex, ey, ew, eh) in eyes:
    #     cv2.rectangle(selfie, (ex, ey), (ex+ew, ey+eh), (0, 255, 255), 2)

    # cv2.imshow('Eyes Detection', selfie)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return data


def checkHistogram(id_client):
    data = {}

    img_check = cv2.imread(save_path + f"/Selfie_{id_client}.jpg", 0)
    hist = cv2.calcHist([img_check], [0], None, [256], [0, 256])

    underExposer = hist[0:25]
    overExposer = hist[225:256]

    count_underExpose = 0
    for i in range(len(underExposer)):
        if underExposer[i] >= 100000:
            count_underExpose += 1

    if count_underExpose >= 20:
        logging.warning(
            "La imagen cuenta con poca iluminación, sitúese en un sitio más iluminado para tomar la foto")
        data["mensaje"] = "La imagen cuenta con poca iluminación, sitúese en un sitio más iluminado para tomar la foto"
        data["success"] = False

    count_overExpose = 0
    for i in range(len(overExposer)):
        if overExposer[i] >= 30000:
            count_overExpose += 1

    if count_overExpose >= 15:
        logging.warning(
            "La imagen cuenta con mucha iluminación, sitúese en un sitio menos iluminado para tomar la foto")
        data["mensaje"] = "La imagen cuenta con mucha iluminación, sitúese en un sitio menos iluminado para tomar la foto"
        data["success"] = False

    if count_overExpose < 15 and count_underExpose < 10:
        logging.warning("Exito, buena foto")
        data["mensaje"] = "Buena imagen"
        data["success"] = True

    return data


def savephoto():
    count = 0

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    files = request.files.getlist("files[]")
    for file in files:
        if count == 0:
            file.filename = "Front.jpg"
        if file.filename == '':
            break
        if count >= 1:
            file.filename = "Back.jpg"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        count += 1


def savephotoselfie():
    id_client = request.form.get('id')
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    files = request.files.getlist("files[]")
    for file in files:
        file.filename = f"Selfie_{id_client}.jpg"

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))


def images_64_encode(id_client):
    image_64_front = None
    image_64_back = None
    image_64_code = None

    files = os.listdir(save_path)

    if f"cedula_frontal_{id_client}.jpg" in files:
        with open(save_path + f'/cedula_frontal_{id_client}.jpg', "rb") as image_front:
            image_64_front = base64.b64encode(image_front.read())

    if f"cedula_posterior_{id_client}.jpg" in files:
        with io.open(save_path + f'/cedula_posterior_{id_client}.jpg', "rb") as image_back:
            image_64_back = base64.b64encode(image_back.read())

    if f"codigo_{id_client}.jpg" in files:
        with io.open(save_path + f'/codigo_{id_client}.jpg', "rb") as image_code:
            image_64_code = base64.b64encode(image_code.read())

    return image_64_front, image_64_back, image_64_code


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=4000)
