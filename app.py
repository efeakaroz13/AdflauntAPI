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
import math 
import redis
from flask_socketio import SocketIO
import operator
from cryptography.fernet import Fernet 
import datetime
from kbook import Booker
from datetime import date,timedelta
import cv2
from stripe_auth import stripeSecret

commisionRates = open("commisionRate.txt","r").read()
commisionRate = float(commisionRates.split(",")[0])
printFee = float(commisionRates.split(",")[1])



r = redis.Redis()

twcl = Client(SID,authToken)
key = b'wlKSloOfyKju_DMzYvCygRI6X9KR5w9Ugp4BZ5wa7Dw='
fernet = Fernet(key)

client = pymongo.MongoClient()
db = client['Adflaunt']
users = db['Users']
reports =  db["Reports"]
bugs = db["Bugs"]
listings = db["Listings"]
chats = db["Chats"]
favorites = db["Favorites"]
admin = db["Admin"]
app = Flask(__name__)
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png", "heic"]
alphabet = ["a","b","c","d", "e", "f", "g", "h", "i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
app.config["SECRET"]="123"

socketio = SocketIO(app,cors_allowed_origins="*",async_mode='gevent')

sids = []


maploader = open("loader.txt","r").read()


def calcPercentage(number,per):
    return number*(per/100)


def login_internal(email,phoneNumber,password):
    sq = {"password":password}

    if password == None:
        return False
    if email != None:
        sq["email"] = email
    if phoneNumber != None:
        sq["phoneNumber"] = phoneNumber

    try:
        user = users.find(sq)[0]
        return user
    except:
        return False

def encrypt(text):
    return fernet.encrypt(text.encode()).decode()
def decrypt(text):
    return fernet.decrypt(text.encode()).decode()




@socketio.on('join')
def joinChat(data):

    email = data["email"]
    password = data["password"]
    phoneNumber = data["phoneNumber"]
    chatID = data["ChatID"]
    user = False
    if email !=None:
        allResults = users.find({"email":email,"password":password})
        for a in allResults:
            user = a 
            break 

    if phoneNumber !=None:
        allResults = users.find({"phoneNumber":phoneNumber,"password":password})
        for a in allResults:
            user = a 
            break 
    if user == False:
        return {"SCC":False,"err":"Could not login"}
    try:
        chat = chats.find({"_id":chatID})[0]
    except:
        return {"SCC":False,"err":"Chat Not Found"}

    chat["messages"].reverse()
    if len(chat["messages"])>30:

        chat["messages"] = chat["messages"][:30]



    sid = IDCREATOR_internal(20)

    sessionData = {"SCC":True,"SID":sid,"chat":chat,"chatID":chatID,"user":user} 
    sids.append(sessionData)

    return sessionData

@socketio.on('leave')
def leaveRoom(data):
    sid = data["SID"]
    for s in sids:
        if s["SID"] == sid:
            cin = sids.index(s)
            sids.pop(cin)
            return {"SCC":True,"msg":"Disconnected"}


@socketio.on('send_msg')
def socketiosendmsg(data):

    sid = data["SID"]
    content = data["content"]
    image = data["image"]

    for s in sids:
        if s["SID"] == sid:
            sender = s['user']['_id']
            
            chatData = chats.find({'_id':s["chatID"]})[0]
            members = chatData["members"]
            receiver = ""
            for m in members:
                if m != sender:
                    receiver = m["user"]
            msgData = {
                "content":content,
                "image":image,
                "sender":sender,
                "receiver":receiver,
                "at":time.time(),
                "_id":IDCREATOR_internal(25)
            }
            chatData["messages"].append(msgData)
            
            chats.update_one({"_id":s["chatID"]},{"$set":{"messages":chatData["messages"]}})
            msgData["chatID"] = chatData["_id"]

            socketio.emit("receive",msgData)



            return {"SCC":True,"msgData":msgData}
    return {"SCC":False,"err":"Could not find session"}
    


@app.route("/tests/chat")
def testChat():
    return render_template("testchat.html")


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


class Messaging:
    @app.route("/api/create/chat",methods=["POST"])
    def createChat():
        email = request.form.get("email")
        password = request.form.get("password")

        if password == None:
            return {"SCC":False,"err":"password cannot be none"}
        phoneNumber = request.form.get("phoneNumber")
        user = False
        if email !=None:
            allResults = users.find({"email":email,"password":password})
            for a in allResults:
                user = a 
                break 

        if phoneNumber !=None:
            allResults = users.find({"phoneNumber":phoneNumber,"password":password})
            for a in allResults:
                user = a 
                break 
        if user == False:
            return {"SCC":False,"err":"Could not login"},401


        reciever = request.form.get("reciever")
        if reciever == None:
            return {"SCC":False,"err":"reciever is required"}
        try:
            recieverUser = users.find({"_id":reciever})[0]
        except:
            return {"SCC":False,"err":"Could not find reciever"}


        allChats = chats.find({})
        for a in allChats:
            members = a["members"]
            recieverHere = False
            senderHere = False
            for m in members:

                if m["user"] == recieverUser["_id"]:
                    recieverHere = True 
                if m["user"] == user["_id"]:
                    senderHere = True 

            if recieverHere == True and senderHere == True:
                del a["messages"]
                return a





        chatID = IDCREATOR_internal(30)
        chatData = {
            "members":[{"user":user["_id"],"profilePicture":user["profileImage"]},{"user":recieverUser["_id"],"profilePicture":recieverUser["profileImage"]}],
            "createdAt":time.time(),
            "messages":[],
            "_id":chatID
        }
        chats.insert_one(chatData)
        chatData["SCC"] = True
        try:
            u1inbox = user["inbox"]
        except:
            u1inbox = []
        try:
            u2inbox = recieverUser["inbox"]
        except:
            u2inbox = []

        u1inbox.append(chatID)
        u2inbox.append(chatID)

        users.update_one({"_id":user["_id"]},{"$set":{"inbox":u1inbox}})
        users.update_one({"_id":recieverUser["_id"]},{"$set":{"inbox":u2inbox}})
        return chatData


    @app.route("/api/get/inbox",methods=["POST"])
    def getInbox():
        email = request.form.get("email")
        password= request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        output = []
        if user == False:
            return {"SCC":False,"err":"Login was not successfull"}
        try:
            inbox = user["inbox"]
            for i in inbox:
                try:
                    chatD = chats.find({"_id":i})[0]

                except:
                    cindex = inbox.index(i)
                    inbox.pop(i)
                    continue

                messages = chatD["messages"]
                try:
                    lastMessage = messages[-1]
                except:
                    lastMessage = ""
                members = chatD["members"]
                opposition = {}
                for m in members:

                    if m["user"] != user["_id"]:

                        opposition = users.find({"_id":m["user"]})[0]
                        del opposition["password"]

                mdata = {"lastMessage":lastMessage,"them":opposition,"chatID":chatD["_id"],"lastMessageTime":lastMessage['at']}
                output.append(mdata)




            users.update_one({"_id":user["_id"]},{"$set":{"inbox":inbox}})
            output= sorted(output, key=operator.itemgetter('lastMessageTime'))
            return {"SCC":True,"output":output}
        except Exception as e:
            return {"SCC":True,"output":[],"reason":"no chat.","e":str(e)}

    @app.route("/api/get/chat/<chatID>/<page>",methods=["POST"])
    def getchat(page,chatID):
        data2page = 30

        email  =request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Could not login"}
        try:
            UINBOX = user["inbox"]
            if chatID not in UINBOX:
                return {"SCC":False,"err":"Could not find chat in inbox"}
        except:
            return {"SCC":False,"err":"Could not find chat in inbox"}
        try:
            page = int(page)
        except:
            return {"SCC":False,"err":"Can't resolve page as an integer. Please enter a valid number"}



        try:
            chatData = chats.find({"_id":chatID})[0]
        except:
            return {"SCC":False,"err":"Could not find chat in the database. This error can be on our hand."}
        messages = chatData["messages"]
        messages.reverse()
        startFrom = data2page*page 
        messages = messages[startFrom:]
        messages = messages[:data2page]
        chatData["messages"] = messages
        chatData["page"] = page 
        chatData["dataPerPage"] = data2page
        chatData["cindex"] = f"{data2page*page} - {data2page*(page+1)}"
        chatData["SCC"] = True
        return chatData





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
            thirdParty = request.form.get("thirdParty")

            if phoneNumber != None:
                phoneNumber = phoneNumber.replace("+","").replace("(","").replace(")","").replace(" ","")

            if phoneNumber != None and phoneNumber != "":
                allResults = users.find({"phoneNumber":phoneNumber})
                for a in allResults:
                    scc=False 
                    return{"SCC":False,"err":"This user exists!"}
            
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
                "idVerified":False,
                "thirdParty":thirdParty
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
    @app.route("/api/userCheck",methods=["POST"])
    def userCheckAPI():
        email = request.form.get("email")
        phoneNumber = request.form.get("phoneNumber")
        output = {"phoneNumberExists":False,"emailExists":False,"SCC":True}
        statusCode=200
        if email == None and phoneNumber == None:
            return {"SCC":False,"err":"You need to specify email or phoneNumber"}
        if phoneNumber != None:
            phoneNumber = phoneNumber.replace("+","").replace("(","").replace(")","").replace(" ","")
            allResults = users.find({"phoneNumber":phoneNumber})
            for a in allResults:
                output["phoneNumberExists"] = True
                output["SCC"] = False 
                statusCode = 409
        if email != None:
            allResults = users.find({"email":email})
            for a in allResults:
                output["emailExists"] = True 
                output["SCC"] = False
                statusCode = 409

        return output,statusCode

    @app.route("/api/getuser/byid")
    def getUserById():
        id_user = request.args.get("id")
        if id_user == None:
            return {"SCC":False,"err":"you will need id argument for this route."}

        allResults = users.find({"password":id_user})
        for a in allResults:
            return a
        return {"SCC":False,"err":"User not found"},404




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
            udata["phoneNumber"] = new_phoneNumber

        
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
            fullName = request.form.get("fullName")
            dateOfBirth = request.form.get("dateOfBirth")


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
        

        typeOfAd = request.form.get("typeOfAd")#Number 0-1-2
        """
        0-outdoor
        1-indoor
        2-vehicle

        """
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
        city = request.form.get("city")
        country = request.form.get("country")
        state= request.form.get("state")


        if typeOfAd == None or images == None or lat==None or long==None or title==None or price==None or revision_limit==None or digital==None or sqfeet==None or location==None or square_footage==None or type_of_listing==None or check_in==None or check_out==None or population==None or discountAvailable==None or description==None or extras==None or requirements==None:
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



        if typeOfAd == "0":
            typeOfAd = "Outdoor"
        elif typeOfAd == "1":
            typeOfAd = "Indoor"
        elif typeOfAd == "2":
            typeOfAd = "Vehicle"
        else:
            return {"SCC":False,"err":"typeOfAd Should be one of those: 0,1,2"}

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
            "user":user['_id'],
            "typeOfAdd":typeOfAd,
            "city":city,
            "state":state,
            "country":country
        }
        db["Listings"].insert_one(data)
        for t in tags:
            db[t].insert_one(data)
        db[typeOfAd].insert_one(data)

        data["SCC"]=True
        
        
        
        return data

    @app.route("/api/get/listings",methods=["GET"])
    def get_listings():
        data = {}
        output = []
        lat = request.args.get("lat")
        long = request.args.get("long")
        mode = request.args.get("mode")
        distanceAsKm = request.args.get("km")
        q = request.args.get("q")
        sessionName = request.args.get("session")
        page = request.args.get("page")


        if sessionName == None:

            sessionName = IDCREATOR_internal(20)

            if distanceAsKm == None:
                distanceAsKm = 300 

            try:
                distanceAsKm = float(distanceAsKm)
            except:
                distanceAsKm = 300
            

            if mode == None:
                return {"SCC":False,"err":"You need to specify mode to use this endpoint"}

            if mode == "near":
                if lat==None or long == None:
                    return {"SCC":False,"err":"We need lat and long to use near function."}
                try:
                    lat = float(lat)
                    long = float(long)
                except:
                    return {"SCC":False,"err":"Lat and long as float"}
                for l in listings.find({}):
                    lat_listing = l["lat"]
                    long_listing = l["long"]
                    listingLocation = [lat_listing,long_listing]
                    originalLocation = [lat,long]

                    distance = math.dist(originalLocation,listingLocation)*111
                    l["distance"] = distance
                    if distance<distanceAsKm:
                        output.append(l)
                output= sorted(output, key=operator.itemgetter('distance'))
                
            if mode == "search":
                if q==None:
                    return {"SCC":False,"err":"for search mode, you need to send query(q)"}

                for l in listings.find({}):
                    title = l["title"].lower()
                    description = l["description"].lower()
                    priority = 0
                    city = l["city"]
                    if city == None:
                        city = ""
                    city = city.lower()

                    state = l["state"]
                    if state == None:
                        state=""
                    state = state.lower()

                    splitter = q.lower().split(" ")
                    for s in splitter:
                        if s in title:
                            priority += 0.05


                        if s in description:
                            priority += 0.04


                        if s in state:
                            priority += 0.03

                        if s in city:
                            priority += 0.03
                    if priority>0:
                        l["priority"] = priority

                        output.append(l)
                output = sorted(output,key=operator.itemgetter('priority'))








            sdata = {"output":output,"q":q,"mode":mode}
            r.mset({f"{sessionName}":json.dumps(sdata)})

        else:
            if mode == "search":
                try:
                    cdata = json.loads(r.get(sessionName))
                    output = cdata["output"]
                    try:
                        page = int(page)
                    except:
                        return {"SCC":False,"err": "Send 'page' as INTEGER"} 
                    try:
                        if len(output) - (page*10-10)>10:

                            output = output[(page*10-10):]

                            output = output[:10]
                        elif len(output) - (page*10-10)<10 and len(output) - (page*10-10)>0:

                            output = output[(page*10-10):]
                        else:
                            return {"SCC":False,"output":[]}


                        return {"SCC":True,"output":output,"session":sessionName}
                    except:
                        return {"SCC":False,"err":"over pagination"}
                except:
                    return {"SCC":False,"err":"Session ID invalid"} 

            if mode == "near":
                try:
                    cdata = json.loads(r.get(sessionName))
                    output = cdata["output"]
                    try:
                        page = int(page)
                    except:
                        return {"SCC":False,"err": "Send 'page' as INTEGER"} 
                    try:
                        if len(output) - (page*10-10)>10:

                            output = output[(page*10-10):]

                            output = output[:10]
                        elif len(output) - (page*10-10)<10 and len(output) - (page*10-10)>0:

                            output = output[(page*10-10):]
                        else:
                            return {"SCC":False,"output":[]}


                        return {"SCC":True,"output":output,"session":sessionName}
                    except:
                        return {"SCC":False,"err":"over pagination"}
                except:
                    return {"SCC":False,"err":"Session ID invalid"}





        dataCount = len(output)

        if len(output)>10:
            output = output[:10]
                
        
        data=  {"SCC":True,"output":output,"session":sessionName,"dataCount":dataCount}
        return data


    @app.route("/api/home/listings",methods=["GET"])
    def homeListings():
        #Just takes coordinates
        lat = request.args.get("lat")
        long = request.args.get("long")
        if lat==None or long ==None:
            return {"SCC":False,"err":"lat and long can not be none."}
        output = []
        for l in listings.find({}):
            lat_listing = l["lat"]
            long_listing = l["long"]
            listingLocation = [lat_listing,long_listing]
            originalLocation = [lat,long]

            distance = math.dist(originalLocation,listingLocation)*111
            l["distance"] = distance

            output.append(l)

        output= sorted(output, key=operator.itemgetter('distance'))
        return {"SCC":True,"output":output}
    @app.route("/api/listing/<listingID>")
    def listingIndividual(listingID):
        try:
            listingData = listings.find({"_id":listingID})[0]
            userID = listingData["user"]
            userData = users.find({"_id":userID})[0]
            listingData["user"] = userData
            listingData["SCC"] = True 

            return listingData
        except:
            return {"SCC":False,"err":"Could not find listing"}

class Favorites:
    @app.route("/api/addto/favorites",methods=["POST","DELETE"])
    def addFavorites():

        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Login Failed."}

        UID = user["_id"]
        listingID = request.form.get("listingID")
        if request.method == "POST":

            if listingID == None:
                return {"SCC":False,"err":"listingID form data is required to add that listing to favorites."}
            try:
                favDATA = favorites.find({"_id":UID})[0]
            except:
                favDATA = {
                    "forUser":UID,
                    "favorites":[],
                    "_id":UID

                }
                favorites.insert_one(favDATA)


            try:
                listingDATA = listings.find({"_id":listingID})[0]
            except:
                return {"SCC":False,"err":"Could not find listing."}

            favDATA["favorites"].append(listingDATA)
            favorites.update_one({"_id":UID},{"$set":favDATA})

            return {"SCC":True,"favDATA":favDATA}
        if request.method == "DELETE":
            try:
                favDATA = favorites.find({"_id":UID})[0]
            except:
                return {"SCC":False,"err":"You don't have any favorites"}
            AllFavorites = favDATA["favorites"]
            
            for f in AllFavorites:
                
                if f["_id"] == listingID:

                    cindex = AllFavorites.index(f)

            
                    AllFavorites.pop(cindex)

                    favorites.update_one({"_id":UID},{"$set":{"favorites":AllFavorites}})
                    return {"SCC":True,"deleted":listingID}

            return {"SCC":False,"err":"Could not find listing in your favorites"}







 


    @app.route("/api/get/favorites",methods=["POST"])
    def getFavorites():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Login Failed."}
        try:

            FAVDATA = favorites.find({"_id":user["_id"]})[0]
        except:
            FAVDATA = {
                "forUser":UID,
                "favorites":[],
                "_id":UID
            }
        FAVDATA["SCC"]=True 

        return FAVDATA


class Admin:
    @app.route("/admin")
    def admin_main():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username":username,"password":password})[0]
        except Exception as e:


            return redirect("/admin/login")
        return render_template("adminIndex.html",adminData=adminData)

    @app.route("/admin/login",methods=["POST","GET"])
    def adminLogin():
        if request.method == "GET":
            return render_template("adminLogin.html")
        if request.method =="POST":

            expire_date = datetime.datetime.now()
            expire_date = expire_date + datetime.timedelta(days=2)
            username = request.form.get("username")
            password = request.form.get("password")
            try:
                admin.find({"username":username,"password":password})[0]
            except:
                return render_template("adminLogin.html",err="Email or password is not correct.")

            response = make_response(redirect("/admin"))
            response.set_cookie("username",encrypt(username),expires=expire_date)
            response.set_cookie("password",encrypt(password),expires=expire_date)

            return response 



    @app.route("/admin/users")
    def adminViewUsers():
        allUsers = users.find({})
        output = []
        for a in allUsers:
            output.append(a)


        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username":username,"password":password})[0]
        except Exception as e:


            return redirect("/admin/login")


        return render_template("adminUser.html",users=output,adminData=adminData)




    @app.route("/admin/user/<userID>")
    def viewUserIndependently(userID):
        userListings = listings.find({"user":userID})
        userListingsArray = []
        for ul in userListings:
            userListingsArray.append(ul)
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username":username,"password":password})[0]
        except Exception as e:


            return redirect("/admin/login")


        try:
            userdata = users.find({"_id":userID})[0]
            userInbox = userdata["inbox"]
            returnInbox = []
            for u in userInbox:
                try:
                    inboxData = chats.find({"_id":u})[0]
                except:
                    continue
                members_inbox = inboxData["members"]
                opposite = ""
                for m in members_inbox:
                    m = m["user"]
                    if m != u:
                        opposite = m

                try:
                    lastMessage = inboxData["messages"][-1]
                except:
                    lastMessage = None
                oppositionData = users.find({"_id":opposite})[0]
                idata = {
                    "lastMessage":lastMessage,
                    "oppositionData":oppositionData,
                    "chatID":u 
                }
                returnInbox.append(idata)
            return render_template("userView.html",data=userdata,maploader=maploader,userListings=userListingsArray,inbox=returnInbox,ctime = time.ctime)
        except Exception as e:

            return render_template("user404.html",error=e)

        
    @app.route("/admin/map")
    def adminMap():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username":username,"password":password})[0]
        except Exception as e:


            return redirect("/admin/login")


        countryDict = {}
        for u in users.find({}):
            try:
                IPDATA = u["IPDATA"]
            except:
                continue

            countryCode = IPDATA["countryCode"]
            try:
                countryDict[countryCode]
            except:
                countryDict[countryCode] = []


            countryDict[countryCode].append(u["_id"])
        return render_template("adminMap.html",countryDict=json.dumps(countryDict,indent=4),maploader=maploader)


    @app.route("/admin/booking")
    def adminBooking():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username":username,"password":password})[0]
        except Exception as e:


            return redirect("/admin/login")

        bookings = db["Bookings"]
        allBookings = bookings.find({})
        approvalData = {}
        for b in allBookings:
            if len(b["waitingForApproval"])>0:
                approvalData[b["_id"]] = b["waitingForApproval"]


        listingData = {}
        for ad in list(approvalData.keys()):
            listingData[ad] = listings.find_one({"_id":ad})


        return render_template("orderApprovalAdmin.html",
            approvalData=approvalData,
            listingData=listingData,
            printFee=printFee,
            commisionRate=commisionRate,
            calcPercentage=calcPercentage
            )


class Booking():
    @app.route("/api/book",methods=["POST"])
    def book_it():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"},401

        listingID = request.form.get("listingID")
        try:
            listingData = listings.find({"_id":listingID})[0]
        except:
            return {"SCC":False,"err":"Could not find listing."}

        pricePerDay = listingData["price"]

        title = request.form.get("title")
        description = request.form.get("description")



        d1 = request.form.get("from")
        d2 = request.form.get("to")
        if d1 == None or d2 == None:
            return {"SCC":False,"err":"'from' and 'to' are not definded, for booking you need to enter those correctly"}
        d1 = d1.split("-")
        d1y = int(d1[0])
        try:
            d1m = int(d1[1])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        
        try:
            d1d = int(d1[2])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        d1 = date(d1y,d1m,d1d)

        d2 = d2.split("-")
        d2y= int(d2[0])
        try:
            d2m = int(d2[1])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        try:
            d2d=int(d2[2])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        d2 = date(d2y,d2m,d2d)
        d = d2-d1
        daysWantToBook = []
        for i in range(d.days + 1):
            day = d1 + timedelta(days=i)
            #print(day)
            day = day.strftime("%Y-%m-%d")
            daysWantToBook.append(day)

        price = pricePerDay*len(daysWantToBook)

        orderData = {
            "title":title,
            "description":description,
            "daysWantToBook":daysWantToBook,
            "pricePerDay":pricePerDay,
            "price":price,


        }
        d1 = request.form.get("from")
        d2 = request.form.get("to")

        try:
            output = Booker.book(listingID,d1,d2,orderData)
            return output
        except Exception as e:
            return {"SCC":False,"err":str(e)}
        return {"SCC":True}

    @app.route("/api/booking/calendar/<listingID>")
    def calendarAPI(listingID):
        bookings = db["Bookings"]
        try:
            booking_data = bookings.find({"_id":listingID})[0]
            datesList = []
            activeOrders=  booking_data["activeOrders"]
            waitingForApproval=  booking_data["waitingForApproval"]
            doneOrders=  booking_data["doneOrders"]

            for a in activeOrders:
                daysWantToBook = a["daysWantToBook"]
                for d in daysWantToBook:
                    datesList.append(d)

            for a in waitingForApproval:
                daysWantToBook = a["daysWantToBook"]
                for d in daysWantToBook:
                    datesList.append(d)

            for a in activeOrders:
                daysWantToBook = a["daysWantToBook"]
                for d in doneOrders:
                    datesList.append(d)

            return {"SCC":True,"output":datesList,"printFee":printFee}


        except:
            return {"SCC":False,"err":"That id was invalid."}

    @app.route("/api/stripe/createPayment/<listingID>",methods=["POST"])
    def createPaymentStripe(listingID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"},401


        try:
            listingData = listings.find({"_id":listingID})[0]
        except:
            return {"SCC":False,"err":"Could not find listing."}

        pricePerDay = listingData["price"]



        d1 = request.form.get("from")
        d2 = request.form.get("to")
        if d1 == None or d2 == None:
            return {"SCC":False,"err":"'from' and 'to' are not definded, for booking you need to enter those correctly"}
        d1 = d1.split("-")
        d1y = int(d1[0])
        try:
            d1m = int(d1[1])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        
        try:
            d1d = int(d1[2])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        d1 = date(d1y,d1m,d1d)

        d2 = d2.split("-")
        d2y= int(d2[0])
        try:
            d2m = int(d2[1])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        try:
            d2d=int(d2[2])
        except:
            return {"SCC":False ,"err": "Date format is invalid"}
        d2 = date(d2y,d2m,d2d)
        d = d2-d1
        daysWantToBook = []
        for i in range(d.days + 1):
            day = d1 + timedelta(days=i)
            #print(day)
            day = day.strftime("%Y-%m-%d")
            daysWantToBook.append(day)

        price = pricePerDay*len(daysWantToBook)
        price = price+printFee

        data = {
            "amount":str(price),
            "currency":"USD"
        }
        headers = {
            "Authorization":f"Bearer {stripeSecret}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        page =requests.post('https://api.stripe.com/v1/payment_intents',headers=headers,data=data)
        page = json.loads(page.content) 
        logger_payment = open("payments.log","a")
        logger_payment.write(f"{time.time()} - {price} - USD\n")
        logger_payment.close()
        return page       


class Scaling:
    @app.route("/static/<filename>/s<scale>")
    def staticScaler(filename,scale):
        try:
            scale = float(scale)
            try:
                img = cv2.imread('static/{}'.format(filename), cv2.IMREAD_UNCHANGED)
            except:
                return {"SCC":False,"err":"file not found or could not be opened by cv2"}

            scale_percent = scale 

            width = int(img.shape[1] * scale_percent / 100)
            height = int(img.shape[0] * scale_percent / 100)
            dim = (width, height)
            resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
            retval, buffer = cv2.imencode('.png', resized)
            response = make_response(buffer.tobytes())
            response.headers['Content-Type'] = 'image/png'
            return response

        except:
            return {"SCC":False,"err":"Scale should be a valid number like: s50 -> it means 50%"}


if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")