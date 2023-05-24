""" 
Author:Efe Akaröz
1st of may, monday 2023
"""
import json
from flask import Flask, render_template, request, redirect, make_response,abort
import cv2
import requests
import time
import random
from werkzeug.utils import secure_filename
import pymongo
import os
from bson import ObjectId



client = pymongo.MongoClient()
db = client['Adflaunt']
users = db['Users']



app = Flask(__name__)
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png", "heic"]
alphabet = ["a","b","c","d", "e", "f", "g", "h", "i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]





def IDCREATOR_internal(len_):
    output = ""
    for i in range(len_):
        c = random.choice(alphabet)
        output = output+c
        if random.randint(1,3) == 2:
            output = output+str(random.randint(0,9))
    return output




def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("docs.html")


class Auth:
    @app.route('/api/register',methods=["POST"])
    def register():
        if request.method=="POST":
            email = request.form.get("email")
            allResults = users.find({"email":email})
            scc = True 
            for a in allResults:
                scc=False 
                return{"SCC":False,"err":"This user exists!"}
            password = request.form.get("password")
            dateOfBirth = request.form.get("dateOfBirth")
            IPDATA = json.loads(request.form.get("IPDATA"))
            try:
                ipraw = IPDATA["query"]
            except:
                return {"SCC":"False","err":"IPDATA invalid"}
            #IPDATA = request.form.get("IPDATA")
            fullName = request.form.get("fullName")
            profileImage = request.form.get("profileImage")
            phoneNumber = request.form.get("phoneNumber")
            if phoneNumber != None:
                phoneNumber = phoneNumber.replace("+","").replace("(","").replace(")","").replace(" ","")

            data = {
                "_id":IDCREATOR_internal(23),
                "email":email,
                "password":password,
                "dateOfBirth":dateOfBirth,
                "IPDATA":IPDATA,
                "fullName":fullName,
                "profileImage":profileImage,
                "phoneNumber":phoneNumber,
                "lastTimeLoggedIn":0,
                "ipraw":ipraw
            }

            result = users.insert_one(data)
            data["SCC"]=True
            



            return data
    @app.route("/api/login",methods=["POST"])
    def login():
        try:
            ip = request.environ['REMOTE_ADDR']

        except:
            ip = request.environ['HTTP_X_FORWARDED_FOR']

        email = request.form.get("email")
        password = request.form.get("password")
        phonenumber = request.form.get("phonenumber")
        if email == None and phonenumber == None:
            return {"SCC":False,"err":"You need to specify at least a phone number or a email"}
        if password == None:
            return {"SCC":False,"err":"you need to  specify a password to login"}
        
        if email != None:
            allResults = users.find({"email":email,"password":password})

        if phonenumber != None:
            allResults = users.find({"phoneNumber":phonenumber,"password":password})
        
        output = {
            "SCC":False,
            "err":"Credentials are not correct."
        }
        for a in allResults:
            output = a
            users.update_one({'_id':output["_id"]},{"$set":{"lastTimeLoggedIn":time.time()}})

        output["SCC"]=True

        return output


class Upload:
    @app.route("/api/upload", methods=["POST"])
    def uploadIt():
        logger = open("file.log", "a")
        if request.method == "POST":
            try:
                ip = request.environ['REMOTE_ADDR'].split(",")[0]
                # ip=request.remote_addr
            except:
                ip = request.environ['HTTP_X_FORWARDED_FOR'].split(",")[0]
            try:
                file = request.files['file']
            except:
                return {"err":"Please specify 'file'."}
            if file and allowed_file(file.filename):
                originalFile = secure_filename(file.filename)
                ext = originalFile.split(".")[1]
                ext = originalFile.split(".")[-1]

                filename = ""
                for i in range(10):
                    ca = random.choice(alphabet)
                    filename = filename+ca
                    addNorNot = random.randint(0, 1)
                    if addNorNot == 1:
                        filename = filename + str(random.randint(12, 120))

                try:
                    file.save("static/"+filename+"."+ext)
                    logger.write(f"UPLOAD {ip} | "+originalFile+" @" +
                                str(time.time())+" as "+filename+"."+ext+"\n")
                    return {"file": filename+"."+ext, "time": time.time(), "ctime": time.ctime(time.time())}

                except Exception as e:
                    return {"err": str(e)}
            else:
                return {"err":"File type is not allowed in this server","allowedFileTypes":ALLOWED_EXTENSIONS,"maxSize":"10MB"}
        logger.close()




class Profile:
    @app.route("/api/getprofile/<userID>")
    def getProfileWithUserId(userID):
        output = users.find({"_id":userID})
        try:
            return str(output) 
        except:
            pass
        
        return {"SCC":False,"err":"Could not find user."}
    @app.route("/api/updateprofile",methods=["POST"])
    def updateProfile():

        #Notes:
        #Email password and phone number is required for this field
        #Updating the login credentials is in the other part
        email = request.form.get("email")
        password = request.form.get("password")
        dateOfBirth = request.form.get("dateOfBirth")
        try:
            IPDATA = json.loads(request.form.get("IPDATA"))
            try:
                ipraw = IPDATA["query"]
            except:
                ipraw = None
        except:
            IPDATA = None
            ipraw = None
        #IPDATA = request.form.get("IPDATA")
        fullName = request.form.get("fullName")
        profileImage = request.form.get("profileImage")
        phoneNumber = request.form.get("phoneNumber")
        if phoneNumber != None:
            phoneNumber = phoneNumber.replace("+","").replace("(","").replace(")","").replace(" ","")
        #Login phase
        allResults = users.find({"email":email,"password":password,"phoneNumber":phoneNumber})
        try:
            r = allResults[0]
        except:
            return {"SCC":False,"err":"Could not login"}
        rid = r["_id"]

        updateData = {}

        if dateOfBirth != None and dateOfBirth!= r["dateOfBirth"]:
            updateData["dateOfBirth"] = dateOfBirth
        
        if fullName != None and fullName != r["fullName"]:
            updateData["fullName"]=fullName
        if profileImage != None and profileImage != r["profileImage"]:
            updateData["profileImage"] = profileImage
        
        if phoneNumber != None and phoneNumber != r["phoneNumber"]:
            updateData["phoneNumber"] = phoneNumber
        if ipraw != None and ipraw != r["ipraw"]:
            updateData["ipraw"] = ipraw 
        if IPDATA != None and IPDATA != r["IPDATA"]:
            updateData["IPDATA"] = IPDATA 
        
    



        users.update_one({'_id':rid},{"$set":updateData})
        outputdata =allResults = users.find({"email":email,"password":password,"phoneNumber":phoneNumber})[0]
        outputdata["SCC"]=True
         

        return outputdata

    @app.route("/api/update_login_credentials",methods=["POST"])
    def update_login_credentials():
        #How it works?
        #So you send whatevery you want to update and also authenticate, 
        #we are checking if the information matches with the old ones and 
        #replace them with the new ones
        email =  request.form.get("email")
        password = request.form.get("password")
        new_email = request.form.get("new_email")
        new_password = request.form.get("new_password")
        new_phoneNumber = request.form.get("new_phoneNumber")
        phoneNumber = request.form.get("phoneNumber")
        queryData = {"password":password}
        if phoneNumber != None:
            queryData["phoneNumber"] = phoneNumber
        if email != None:
            queryData["email"] = email 
        

        searcher = users.find(queryData)
        try:
            udata = searcher[0]

        except:
            return {"SCC":False,"err":"Check the credentials for authentication"}
        
        if new_email != None:
            udata["email"] = new_email
        if new_password != None:
            udata["password"] = new_password
        if new_phoneNumber != None:
            udata["phoneNumber"] = phoneNumber
        
        users.update_one({"_id":udata["_id"]},{"$set":udata})
        udata["SCC"]= True

        return udata


        return {}
if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")