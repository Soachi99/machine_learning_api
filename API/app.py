import os
import io
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import OCR_cedula
import CedulaDetection
import base64
import logging
import cv2

save_path = 'static'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = save_path
imageList = []
CORS(app, resources={r"*": {"origins": "*"}})

@app.route('/')
def upload_files():    
    return render_template('form.html')

@app.route('/uploader', methods = ['POST'])
def uploader():    
    if request.method == "POST":    
        
        id_client = request.form.get('id') 
        savephoto()
        data_hist = checkHistogram()

        if data_hist['success'] == True:
            try:
                isFront, isBack  = CedulaDetection.detect(id_client)                           
                if isFront != False or isBack != False: 
                    
                    Data = OCR_cedula.scan(id_client)
                    if Data["success"] == False:
                        Data = {"success": False, "mensaje": "Error en el reconocimiento de caracteres, la imagen está muy borrosa o de difícil lectura"}
                        logging.warning("Imagen borrosa o de dificil lectura") 
                    else:
                        aux_data = Data
                        logging.warning(f"id:{id_client}, {aux_data}")                   
                        image_64_front, image_64_back = images_64_encode(id_client)                
                        if image_64_back != None:
                            Data["Imagen Cedula Posterior"] = str(image_64_back)
                        if image_64_front != None:
                            Data["Imagen Cedula Frontal"] = str(image_64_front)
                        

                    if isFront == True and isBack == True:
                        try:
                            os.remove(save_path + f'/cedula_frontal_{id_client}.jpg')
                            os.remove(save_path + f'/cedula_posterior_{id_client}.jpg')
                        except:
                            print("No existe imagen")

                    if isFront == False and isBack == True:
                        try:                        
                            os.remove(save_path + f'/cedula_posterior_{id_client}.jpg')
                        except:
                            print("No existe imagen")
                    

                if isFront == False and isBack == False:  
                    Data = {"success": False, "mensaje": "No se detectó una cédula en la imagen"}
                    logging.warning("No se detectó cédula")  

                return jsonify(Data)
            except:
                Data = {"success": False, "mensaje": "No se detectó una cédula en la imagen"}
                logging.warning("No se detectó cédula")  
                return jsonify(Data)
        else:            
            return jsonify(data_hist)

@app.route('/checkselfie', methods = ['POST'])
def checkphoto():         
    savephoto()
    data = checkHistogram()  

    if data["success"] == True: 
        selfie = cv2.imread(save_path + "/Front.jpg")
        h, w , c = selfie.shape
        aux_selfie = selfie[200:h-170, 40:w-40]
        aux_selfie = cv2.detailEnhance(aux_selfie, sigma_s=2, sigma_r=0.10) 
        cv2.imwrite(save_path + '/selfie.jpg', aux_selfie)

        with open(save_path + '/selfie.jpg', "rb") as image_selfie:            
            image_64_selfie = base64.b64encode(image_selfie.read())
            data["selfie"] = str(image_64_selfie)

        try:                        
            os.remove(save_path + '/selfie.jpg')
        except:
            print("No existe imagen")
    
    return jsonify(data)


def checkHistogram():
    data = {}  

    img_check = cv2.imread(save_path + "/Front.jpg", 0)    
    hist = cv2.calcHist([img_check], [0], None, [256], [0, 256])  

    underExposer = hist[0:25]
    overExposer = hist[225:256]

    count_underExpose = 0
    for i in range(len(underExposer)):
        if underExposer[i] >= 10000:
            count_underExpose += 1

    if count_underExpose >= 10: 
        logging.warning("La imagen cuenta con poca iluminación, sitúese en un sitio más iluminado para tomar la foto")  
        data["mensaje"] = "La imagen cuenta con poca iluminación, sitúese en un sitio más iluminado para tomar la foto"
        data["success"] = False

    count_overExpose = 0
    for i in range(len(overExposer)):
        if overExposer[i] >= 7500:
            count_overExpose += 1

    if count_overExpose >= 15:  
        logging.warning("La imagen cuenta con mucha iluminación, sitúese en un sitio menos iluminado para tomar la foto") 
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


def images_64_encode(id_client):
    image_64_front = None
    image_64_back = None

    files = os.listdir(save_path) 

    if f"cedula_frontal_{id_client}.jpg" in files:
        with open(save_path + f'/cedula_frontal_{id_client}.jpg', "rb") as image_front:
            image_64_front = base64.b64encode(image_front.read())

    if f"cedula_posterior_{id_client}.jpg" in files:
        with io.open(save_path + f'/cedula_posterior_{id_client}.jpg', "rb") as image_back:
            image_64_back = base64.b64encode(image_back.read())
     
    return image_64_front, image_64_back

if __name__ == '__main__':    
    app.run(debug = False, host="0.0.0.0", port=4000)


