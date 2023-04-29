import json
from flask import Flask, render_template, request, redirect, make_response
import cv2
import requests
import time
import random
from werkzeug.utils import secure_filename

data = json.loads(open("data.json", "r").read())
app = Flask(__name__)
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png", "heic"]
alphabet = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("docs.html")

class Auth:
    @app.route("/login",methods=["POST"])
    def login():
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            if data["short_auth"][email] != password:
                return {"SCC":False,"err":"Password is not correct."}

        except:
            return {
                "SCC":False,
                "err":"This user does not exist."
            }
        
        allkeys = list(data["Users"].keys())
        for a in allkeys:
            d = data["Users"][a]
            if d["email"] == email:
                return d 
        
        return {"SCC":False,"err":"There is an error with our side"}




    @app.route("/register", methods=["POST"])
    def registrer():
        email = request.form.get("email")
        password = request.form.get("password")
        ip_ = request.form.get("ip")
        dateBirth = request.form.get("dateBirth")
        try:
            file = request.files["file"]
            if file and allowed_file(file.filename):
                originalFile = secure_filename(file.filename)
                ext = originalFile.split(".")[1]
                ext = originalFile.split(".")[-1]

                filename = ""
                for i in range(10):
                    ca = random.choice(alphabet)
                    filename = filename + ca
                    addNorNot = random.randint(0, 1)
                    if addNorNot == 1:
                        filename = filename + str(random.randint(12, 120))

                try:
                    file.save("static/" + filename + "." + ext)

                    filename = filename + "." + ext

                except Exception as e:
                    filename = ""
        except Exception as e:
            print(e)
            filename = ""
        if ip_ != None:
            try:
                ipdata=json.loads(requests.get("http://ip-api.com/json/"+str(ip_)).content)
            except:
                ipdata={}
        else:
            ipdata = {}
        UID = ""
        for i in range(12):
            c = random.choice(alphabet)
            UID = UID+c 
            randomch = random.randint(0,2)
            if randomch == 1:
                UID = UID+str(random.randint(0,9))
        

        locdata = {
            "email":email,
            "password":password,
            "ip":ip_,
            "ip_data":ipdata,
            "image":filename,
            "dateOfBirth":dateBirth,
            "registerDate":time.time(),
            "UID":UID

        }
        data["Users"][UID] = locdata
        data["short_auth"][email]=password 
        open("data.json","w").write(json.dumps(data,indent=4))
        return locdata
    
if __name__ == "__main__":
    app.run(debug=True)