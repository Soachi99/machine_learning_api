import os, io
import re
from google.cloud import vision


# Token para usar los servicios de google vision en el OCR
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"ServiceAccountToken.json"
client = vision.ImageAnnotatorClient()

# Función para filtrar y organizar los datos extraidos por el OCR de la parte frontal de la cedula
def orderDataFront(Data):
    # Inicialización de un diccionario para organizar los datos
    orderData = {}
    orderData["Apellidos"] = None
    orderData["Nombres"] = None
    orderData["Numero de Cedula"] = None

    # Inicialización de variables que almacenaran la posición de patrones en la información
    # que nos ayudan para poder organizar los datos
    pos_name = None     
    pos_num = None 
    pos_lastname = None  

    # Lista de palabras que se deben filtrar en los datos extraidos
    words_to_filter = ["Rep","Co","Icade","Abia","Ica","Mr","Om","Olbn","De","Sa","Mero",
        "Número","Numero","Numro","Numer","Republica De","Colomba","Ica D","Ica De","Mbia","Repu",
        "Republica","Republica De Colombia","Colombiay","Colonema","Bedublic T", "Rnpablicade",
        "Republ", "Coll", "Rlica", "Numeho", "Dos", '', "Colombia", "Eribica", "Coloa", "Codo", "Republic De",
        "Colo", "Firma", "Colon", "Public", "Olom", "Ombia", "Epublica De", "Epublica", "Nublica", "Olonb", 
        "Coldabia", "Acional", "Nacional", "Auca De Da", "Republica Ce", "Mb", "Rnpablicad", "Ta", "Olo", 
        "Olo K", "Republicade", "Colgmbia", "Col", "C Rublica De", "Cobombia", "Colombla", "Replblica De",
        "Lica De", "Repubee", "Repubea", "Repilicad", "Colombl", "Hacional", "Repueli", "Colommen", "Colomgia",
        "Epublica De Colma", "Replibu", "Re", "Sia", "Rublic", "Pepublic", "Coloeia", "Nůmero"
    ]

    ## Busca el numero de la cedula en los datos y quita los puntos
    for i in range(len(Data)):
        orderData["Numero de Cedula"] = "".join(re.findall(r"\d", Data[i]))
        if len(orderData["Numero de Cedula"]) > 5:
            # Posición del numero de cedula en los datos extraidos
            pos_num = i
            break

    ## Posición de la palabra "Nombre" en la cedula.
    for i in range(len(Data)):
        if (
            "br" in Data[i]            
            or Data[i] == "Nomares" 
            or Data[i] == "Nombhes"
        ):
            pos_name = i
            break
    

    ## Si lee un numero y un nombre, realiza la operación de lectura y orden.
    if pos_name != None and pos_num != None:    
        # Corta los datos desde la posici´pm del numero de cedula hasta la posición del nombre     
        new_data = Data[pos_num + 1 : pos_name]
        
        # Proceso de filtro de palabras no deseadas o basura
        for word in words_to_filter:
            try:
                new_data.remove(word)
            except:
                continue

        # Determina la posición de la palabra "apellido" en los datos 
        for i in range(len(new_data)):
            if (
                "Apel" in new_data[i]    
                or "apel" in Data[i]        
                or new_data[i] == "Apellidos"             
            ):
                pos_lastname = i
                break

        # Según los cortes y filtros realizados, el apellido siempre quedara como primera posición
        # y el nombre luego de la plabra apellido, o en su defecto al final de la lista de datos
        if(len(new_data)>0):
            orderData["Apellidos"] = new_data[0]
            try:
                orderData["Nombres"] = new_data[pos_lastname + 1]
            except:
                orderData["Nombres"] = new_data[-1]
        else:
            return False

    ## Si determina la posición del numero, pero no la posición del nombre, realiza la operación de lectura y orden por la posición del apellido.
    if pos_num != None and pos_name == None:
        # Determina la posición de la palabra "apellido" en los datos 
        for i in range(len(Data)):
            if (
                "Apel" in Data[i] 
                or "apel" in Data[i]         
                or Data[i] == "Apellidos"                            
            ):
                pos_lastname = i
                break
        
        # Intenta cortar los datos si encontro la palabra apellido en los datos
        try:
            new_data = Data[pos_num +1 : pos_lastname+2]  
        except:
            new_data = Data[pos_num +1 :]
        
        # Proceso de filtro de palabras no deseadas o basura
        for word in words_to_filter:
            try:
                new_data.remove(word)
            except:
                continue
        # Según los cortes y filtros realizados, el apellido siempre quedara como primera posición
        # y el nombre al final de la lista de datos
        if(len(new_data)>0):
            orderData["Apellidos"] = new_data[0]
            orderData["Nombres"] = new_data[-1]
        else:
            return False

    ## Retorna un False si no hayo en la cedula el numero o un nombre.
    if pos_num == None and pos_name == None:
        return False;

    ## Retorna un False si no hizo la lectura de los datos.
    if (
        orderData["Apellidos"] == None 
        or orderData["Nombres"] == None 
        or orderData["Numero de Cedula"] == None
    ):
        return False;
    
    # Retorna los datos organizados
    return orderData


def orderDataBack(Data):
    # Inicialización diccionario para alamacenar los datos organizados de la parte trasera de la cédula
    backData = {}    
    backData["G.S.RH"] = None
    backData["Sexo"] = None
    backData["Fecha de Nacimiento"] = None
    backData["Fecha de Expedicion"] = None

    # Lista de Grupos sanguineos
    RH = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

    # Buscamos en los datos un patron de numeros con 3 unidades de longitud
    # lo que correspondera a la estatura
    for i in range(len(Data)):
        backData["Estatura"] = "".join(re.findall(r"\d", Data[i]))
        if len(backData["Estatura"]) == 3:
            Data.pop(i)
            break
    backData["Estatura"] = str(float(backData["Estatura"]) / 100)  

    # Buscamos en los datos un patron de que siga la siguiente forma "19-MAY-2019"
    # para almacenarlos como las fechas de nacimiento y expedición 
    matches = []
    for i in range(len(Data)):
        matches.append(re.search(r"\d{2}-\w{3}-\d{4}", Data[i]))
    matches = list(filter(None, matches))

    # Según los patrones encontrados, la primera fecha siempre corresponde a la
    # fecha de nacimiento y la segunda a la fecha de expedición del documento,
    # siguiendo esta logica, se almacenan los datos de las fechas en el diccionario
    count = 0
    for match in matches:
        if count == 0:
            backData["Fecha de Nacimiento"] = match.group(0)
        else:
            backData["Fecha de Expedicion"] = match.group(0)
        count += 1

    # Evaluamos si hay algun RH de los listados anteriormente en los datos, si lo hay, 
    # guardamos el RH en el diccionario
    for i in range(len(Data)):
        for j in range(len(RH)):
            if RH[j] == Data[i]:
                backData["G.S.RH"] = Data[i]

        # Recorriendo de igual forma los datos, evaluamos si hay un dato con la letra F o M
        # lo cual corresponde al sexo de la persona y se guarda en el diccionario
        if Data[i] == "F" or Data[i] == "M":
            backData["Sexo"] = Data[i]

        # A partir del patron de parentesis "(" y ")", se halla el lugar de nacimiento de la 
        # persona y se guarda en el diccionario
        if "(" in Data[i] or ")" in Data[i]:
            backData["Lugar de Nacimiento"] = Data[i - 1] + " " + Data[i]

    # A partir de la fecha de expedición, se realiza un corte del texto donde fue encontrada,
    # ya que el texto siguiente a la fecha es el lugar de expedición de la cedula,
    # se guarda en el diccionario despues del corte
    if backData["Fecha de Expedicion"] != None:
        for i in range(len(Data)):
            if backData["Fecha de Expedicion"] in Data[i]:
                aux_text = Data[i]
                backData["Lugar de Expedicion"] = aux_text[12:]
    else:
        backData["Lugar de Expedicion"] = None

    ## Retorna un False si no hizo la lectura de los datos.
    if (backData["Fecha de Nacimiento"] == None or backData["Fecha de Expedicion"] == None):
        return False;

    return backData


def OCR_front(image):
    # OCR de la imagen frontal de la cedula
    response = client.text_detection(
        image=image, image_context={"language_hints": ["es"]}
    )    
    # Respuesta del OCR y separación de los datos
    text = response.full_text_annotation.text
    data = text.split(sep="\n")    
    data = [each_string.title() for each_string in data]
    # Orden y filtro de los datos
    frontData = orderDataFront(data)
    return frontData


def OCR_back(image):
    # OCR de la imagen posterior de la cedula
    response = client.text_detection(
        image=image, image_context={"language_hints": ["es"]}
    )
    # Respuesta del OCR y separación de los datos
    text = response.full_text_annotation.text
    data = text.split(sep="\n")
    data = [each_string.upper() for each_string in data]
    # Orden y filtro de los datos
    BackData = orderDataBack(data[:13])
    return BackData


def scan(id_client):
    # Inicializamos dos variables bool para poder retornar los datos según 
    # la posición de la cedula que se envió 
    isFront = False
    isBack = False

    # Ruta donde se alamcenan las imagenes
    data_path = "./static"

    # Entramos a la ruta y realizamos el OCR de las imagenes correspondientes
    # luego de la detección de la parte frontal y posterior de la cedula           
    for file_name in os.listdir(data_path):

        # Si el nombre de la imagen es "cedula_frontal_prueba.jpg"m se realiza 
        # el OCR de la imagen según las funciones para organizar datos 
        # en la parte delantera
        if file_name == f"cedula_frontal_{id_client}.jpg":
            # Contenido de la imagen (Se debe enviar así al OCR de Google Visión)
            with io.open(os.path.join(data_path, file_name), "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            result_front = OCR_front(image)
            if result_front == False:
                isFront = False
            else:
                isFront = True
        
        # Si el nombre de la imagen es "cedula_posterior_prueba.jpg"m se realiza 
        # el OCR de la imagen según las funciones para organizar datos 
        # en la parte trasera
        if file_name == f"cedula_posterior_{id_client}.jpg":
                # Contenido de la imagen (Se debe enviar así al OCR de Google Visión)
            with io.open(os.path.join(data_path, file_name), "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            result_back = OCR_back(image)
            if result_back == False:
                isBack = False
            else:
                isBack = True
                    
    if isFront == True and isBack == False:
        Data = {
            "Datos Cedula Parte Frontal": result_front,
            "success": True,           
        }
    if isFront == False and isBack == True:        
        Data = {            
            "Datos Cedula Parte Posterior": result_back,
            "success": True, 
        }
    if isFront == True and isBack == True: 
        Data = {
            "Datos Cedula Parte Frontal": result_front,
            "Datos Cedula Parte Posterior": result_back,
            "success": True, 
        }
    if isFront == False and isBack == False:
        Data = {            
            "success": False,
        }

    return Data
