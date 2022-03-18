import os
import io
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import OCR_cedula
import CedulaDetection
import base64
import logging

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
        count = 0    

        if not os.path.exists(save_path):
            os.makedirs(save_path) 
        
        files = request.files.getlist("files[]") 
        id_client = request.form.get('id')                  
        for file in files:                   
            if count == 0:                
                file.filename = "Front.jpg"  
            if file.filename == '':
                break           
            if count >= 1:                
                file.filename = "Back.jpg"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))            
            count += 1   

        try: 
            isFront, isBack  = CedulaDetection.detect(id_client)                           
            if isFront != False or isBack != False: 
                
                Data = OCR_cedula.scan(id_client)
                if Data["success"] == False:
                    Data = {"success": False, "mensaje": "Error en el reconocimiento de caracteres, la imagen esta muy borrosa o de dificil lectura"}
                    logging.warning("Imagen borrosa o de dificil lectura") 
                else:
                    aux_data = Data
                    logging.info(aux_data)
                    print(aux_data)
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
                Data = {"success": False, "mensaje": "No se detecto una cédula en la imagen"}
                logging.warning("No se detecto cédula") 
               
            return jsonify(Data)
        except:
            Data = {"success": False, "mensaje": "No se detecto una cédula en la imagen"}
            logging.warning("No se detecto cédula")  
            return jsonify(Data)

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


