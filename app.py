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
from twillioAuth import authToken,SID,phoneNumber_tw
from twilio.rest import Client 

twcl = Client(SID,authToken)


client = pymongo.MongoClient()
db = client['Adflaunt']
users = db['Users']
reports =  db["Reports"]
bugs = db["Bugs"]
listings = db["Listings"]

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
                "ipraw":ipraw,
                "idVerified":False
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
            output = output[0]
            del output["password"]
            return output
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


class Verification:
    @app.route("/api/verify/sms")
    def sms_verification():
        #NOTE : THIS SHIT JUST SUPPORTS US NUMBERS AS I UNDERSTOOD. DONT USE IT ELSEWHERE
        phoneNumber = request.args.get("phoneNumber")
        code_verify = random.randint(1,1000000)
        try:
            message = twcl.messages.create(
                body=f"Adflaunt Verification Code:{code_verify}",
                from_=phoneNumber_tw,
                to=phoneNumber
            )
        except Exception as e:
            print(e)
            return {"SCC":False,"err":str(e)}
        return {"SCC":True,"m.body":message.body}

    
class ReportingSystem:
    @app.route("/api/report/<userID>",methods=["POST"])
    def apireport(userID):
        email  = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        querydata = {}
        if email == None and phoneNumber == None:
            return {"SCC":False,"err":"You need to specify email or phoneNumber"}
        if email != None:
            querydata["email"] = email
        if phoneNumber != None:
            querydata["password"] = password 
        try:
            user = users.find(querydata)[0]
        except:
            return {"SCC":False,"err":"Could not authenticate"}
        title =  request.form.get("title")
        description = request.form.get("description")
        timeitreported= time.time()
        try:
            user_ = users.find({"_id":userID})[0]
        except:
            return {"SCC":False,"err":"Could not find the user"}
        if userID == user["_id"]:
            return {"SCC":False,"err":"Users can't report themselves."}
        data = {
            "_id":IDCREATOR_internal(20),
            "title":title,
            "description":description,
            "timereported":timeitreported,
            "reporter":user["_id"],
            "suspect":userID
        }
        reports.insert_one(data)
        data["SCC"] = True
        return data

    @app.route("/api/report/bugs",methods=["POST","GET"])
    def reportBugs():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            title = request.form.get("title")
            description = request.form.get("description")
            bugImage = request.form.get("bugImage")
            #Bug image should be a static filename
            phoneNumber = request.form.get("phoneNumber")
            data = {
                "reportedAt":time.time(),
                "email":email,
                "title":title,
                "description":description,
                "bugImage":bugImage,
                "phoneNumber":phoneNumber,
                "_id":IDCREATOR_internal(20)
            }

            
            querydata = {}
            if email == None and phoneNumber == None:
                return {"SCC":False,"err":"You need to specify email or phoneNumber"}
            if email != None:
                querydata["email"] = email
            if phoneNumber != None:
                querydata["password"] = password 
            try:
                user = users.find(querydata)[0]
            except:
                return {"SCC":False,"err":"Could not authenticate"}
            uid = user["_id"]
            data["userID"] = uid 
            bugs.insert_one(data)
            data["SCC"]=True 

            return data
        if request.method == "GET":
            return {"SCC":False,"err":"This endpoint does not support get requests yet."}

class IDVerification:
    @app.route("/api/verify/ID",methods=["POST"])
    def IDVERIFY():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            phoneNumber = request.form.get("phoneNumber")
            if password == None:
                return {"SCC":False,"err":"password can't be null."}
            query_cr = {"password":password}
            if email != None:
                query_cr["email"] = email 
            if phoneNumber != None:
                query_cr["phoneNumber"] = phoneNumber
            if email == None and phoneNumber == None:
                return {"SCC":False,"err":"Email or phonenumber is required for authentication"}
            
            try:
                user = users.find(query_cr)[0]
            except:
                return {"SCC":False,"err":"Could not authenticate"}
            
            UID = user["_id"]
            photoOfId = request.form.get("photoOfId")
            if photoOfId == None:
                return {"SCC":False,"err":"You need to specify photoOfId as a static filename"}
            
            users.update_one({"_id":UID},{"$set":{"photoOfId":photoOfId,"idVerified":True}}) 
            user["photoOfId"] = photoOfId
            user["idVerified"] = True
            user["SCC"]= True
            return user
        

class Listings:
    @app.route("/api/create/listing",methods=["POST"])
    def createlisting():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        if password == None:
            return {"SCC":False,"err":"password can't be null."}
        query_cr = {"password":password}
        if email != None:
            query_cr["email"] = email 
        if phoneNumber != None:
            query_cr["phoneNumber"] = phoneNumber
        if email == None and phoneNumber == None:
            return {"SCC":False,"err":"Email or phonenumber is required for authentication"}
        
        try:
            user = users.find(query_cr)[0]
        except:
            return {"SCC":False,"err":"Could not authenticate"}
        if user['idVerified'] == False:
            return {"SCC":False,"err":"ID NOT VERIFIED."}
        
        lat = request.form.get("lat")#number, float
        long = request.form.get("long")#number, float
        images = request.form.get("images")
        title = request.form.get("title")
        price = request.form.get("price")#number integer
        location = request.form.get("location")
        revision_limit = request.form.get("revision_limit")#number integer
        digital = request.form.get("digital") #Boolean - 1 for true, 0 for false
        sqfeet = request.form.get("sqfeet") #number integer
        square_footage = request.form.get("square_footage")#number,int
        type_of_listing = request.form.get("type") # number - between 1-6
        check_in = request.form.get("check_in")#Date
        check_out = request.form.get("check_out") #Date
        population = request.form.get("population") #number
        discountAvailable = request.form.get("discountAvailable")# Number between 1-4
        """ 
        Discount available:
        yes
        no
        long-term
        partial
        """
        tags = request.form.get("tags")
        extras = request.form.get("extras")#fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
        requirements = request.form.get("requirements")#fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
        description = request.form.get("description")#STR
        bookingNote = request.form.get("bookingNote")#STR OPT
        bookingOffset = request.form.get("bookingOffset") #INT OPT
        "Set how many days are required prior to the booking date"
        bookingWindow = request.form.get("bookingWindow") #INT OPT
        "Set how many days in advance a booking can be made."
        minimumBookingDuration = request.form.get("minimumBookingDuration")
        BookingImportURL = request.form.get("BookingImportURL")


        if images == None or lat==None or long==None or title==None or price==None or revision_limit==None or digital==None or sqfeet==None or location==None or square_footage==None or type_of_listing==None or check_in==None or check_out==None or population==None or discountAvailable==None or description==None or extras==None or requirements:
            return {"SCC":False,"err":"some parameters are required"}
        
        lat = float(lat)
        long = float(long)

        images = images.split("|-|")
        extras = json.loads(extras)
        requirements = json.loads(requirements)
        try:
            bookingOffset = int(bookingOffset)
        except:
            bookingOffset = 0
        try:
            bookingWindow = int(bookingWindow)
        except:
            bookingWindow = 0

        try:
            minimumBookingDuration = int(minimumBookingDuration)
        except:
            minimumBookingDuration = 0

        try:

            population = int(population)
        except:
            return {"SCC":False,"err":"Population should be an integer"}
        try:
            price = int(price)
        except:
            return {"SCC":False,"err":"Price should be an integer"}
        
        try:
            tags = ''.join([i if ord(i) < 128 else ' ' for i in tags])
            #may give some errors
            tags = tags.split("|-|")
        except:
            tags = []
        

        if digital == "0":
            digital = False

        if digital == "1":
            digital = True



        if type_of_listing == "1":
            type_of_listing = "1.5' X 2' Yard Sign"
        
        if type_of_listing == "2":
            type_of_listing = "10' Banner"
        
        if type_of_listing == "3":
            type_of_listing = "2'x 3' Floor Sign"

        if type_of_listing == "4":
            type_of_listing = "2'x 3' Poster"

        
        if type_of_listing == "5":
            type_of_listing = "20'+ Bill Board"

        if type_of_listing == "6":
            type_of_listing = "1.5' X 2' Digital Signage"

        if discountAvailable == "1":
            discountAvailable = "Yes"

        if discountAvailable == "2":
            discountAvailable = "No"

        if discountAvailable == "3":
            discountAvailable = "Long-Term"
        if discountAvailable == "4":
            discountAvailable = "Partial"
        

        data = {
            "title":title,
            "price":price,
            "lat":lat,
            "long":long,
            "images":images,
            "location":location,
            "revision_limit":revision_limit,
            "digital":digital,
            "sqfeet":sqfeet,
            "square_footage":square_footage,
            "type":type_of_listing,
            "check_in":check_in,
            "check_out":check_out,
            "population":population,
            "tags":tags,
            "extras":extras,
            "requirements":requirements,
            "description":description,
            "bookingNote":bookingNote,
            "bookingOffset":bookingOffset,
            "bookingWindow":bookingWindow,
            "minimumBookingDuration":minimumBookingDuration,
            "BookingImportURL":BookingImportURL,
            "_id":IDCREATOR_internal(40),
            "user":user['_id']
        }
        db["Listings"].insert_one(data)
        for t in tags:
            db[t].insert_one(data)

        data["SCC"]=True
        
        
        
        return data

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")