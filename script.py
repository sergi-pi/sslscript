import os
import time
import pymysql.cursors
import config

ips = [] #lista de ips para el archivo
ports = [443, 8843] #lista de puertos, ampliable para escalabilidad
queryData = [] #lista para los datos de la query por cada ip

#lee el archivo con la lista de ips y los añade a una lista local ips
def leerArchivo():
    with open("fichero.txt") as f:
        for line in f:
            if line is not None:
                ips.append(line.split()[0])
    ejecutarComandos()


#Ejecuta los comando en el shell de ubuntu, filtrando sólo los parámetros y creando archivos txt con el output filtrado
def ejecutarComandos():
    for port in ports:
        for ip in ips:
            os.system("sudo testssl --fast --quiet -p --openssl-timeout 5 --color 0 "
                      +ip+":"+str(port)+" | grep -E 'SSLv2|SSLv3|TLS 1' > logs/"+ip+"_"+str(port)+".txt")
    leerOutputs()

#De la carpeta logs lee todos los archivos, añade a la lista la ip, el puerto y los booleanos para los protocolos
def leerOutputs():
    for file in os.listdir('logs'):
        with open("logs/"+file) as f:
            queryData.append(os.path.basename(f.name).split("_")[0])
            queryData.append(os.path.basename(f.name).split("_")[1][:-4])
            protocols = []
            if os.stat(f.name).st_size == 0:
                for i in range(6):
                    protocols.append(False)
                queryData.append(protocols)
            else:
                for line in f:
                    if line[11:15].strip() == "not":
                        protocols.append(False)
                    else:
                        protocols.append(True)
                queryData.append(protocols)
    guardarOutputs(queryData)


#Insert a la base de datos
def guardarOutputs(queryData):
    db = connectDB()
    db.select_db("ssldb")
    sublist = subList(queryData, 3) #función para crear una lista de listas por cada ip

    for query in sublist:
        db.cursor().execute("INSERT INTO ips (ip, puerto, SSLv2, SSLV3, `TLSv1.0`, `TLSv1.1`, `TLSv1.2`, `TLSv1.3`, fecha) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s)"%(str(query[0]), str(query[1]), int(query[2][0]), int(query[2][1]), int(query[2][2]), int(query[2][3]), int(query[2][4]), int(query[2][5]), int(time.time())))

    db.commit()
    db.close()

#Crea una lista con sublistas de n campos de la lista principal
def subList(list, n):
    for i in range(0, len(list), n):
        yield list[i:i + n]

#Conexión básica a la BD
def connectDB():
    db = pymysql.connect(host=config.HOST,
                         user=config.USR,
                         password=config.PWD)
    return db

#Crea la estructura de la base datos, la BD si no existe y la Tabla si no existe
def createStructure():
    db = connectDB()
    db.cursor().execute("CREATE USER IF NOT EXISTS 'fpuser'@'localhost' IDENTIFIED BY 'xxxxx';")
    db.cursor().execute("CREATE DATABASE IF NOT EXISTS ssldb")
    db.select_db("ssldb")
    db.cursor().execute("CREATE TABLE IF NOT EXISTS ips ("
                        "indice int NOT NULL AUTO_INCREMENT,"
                        "ip VARCHAR(30) NOT NULL,"
                        "puerto VARCHAR(10) NOT NULL,"
                        "SSLv2 bool,"
                        "SSLv3 bool,"
                        "`TLSv1.0` bool,"
                        "`TLSv1.1` bool,"
                        "`TLSv1.2` bool,"
                        "`TLSv1.3` bool,"
                        "fecha int(11),"
                        "PRIMARY KEY (indice))")

    db.cursor().close()
    db.close()


createStructure()
leerArchivo()