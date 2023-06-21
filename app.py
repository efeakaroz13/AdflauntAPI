""" 
Author:Efe Akaröz
1st of may, monday 2023
"""
import json
from flask import Flask, render_template, request, redirect, make_response, abort,jsonify
import cv2
import requests
import time
import random
from werkzeug.utils import secure_filename
import pymongo
import os
from bson import ObjectId
from twillioAuth import authToken, SID, phoneNumber_tw
from twilio.rest import Client
import math
import redis
from flask_socketio import SocketIO
import operator
from cryptography.fernet import Fernet
import datetime
from kbook import Booker
from datetime import date, timedelta
import cv2
from stripe_auth import stripeSecret,brevoSecret,firebaseKey
import stripe
import geopy.distance
#import sib_api_v3_sdk
#from sib_api_v3_sdk.rest import ApiException
import smtplib




stripe.api_key = "sk_test_51LkdT2BwxpdnO2PUh2too5t3AfGBGZqkDltuL0GuHIAClpHTVa9IiYN8bKdW7P3eSrKZbWjor9xtp2InwnuZgr8X00sXVNT3ql"


commisionRates = open("commisionRate.txt", "r").read()
commisionRate = float(commisionRates.split(",")[0])
printFee = float(commisionRates.split(",")[1])

r = redis.Redis()

twcl = Client(SID, authToken)
key = b'wlKSloOfyKju_DMzYvCygRI6X9KR5w9Ugp4BZ5wa7Dw='
fernet = Fernet(key)

client = pymongo.MongoClient()
db = client['Adflaunt']
users = db['Users']
reports = db["Reports"]
bugs = db["Bugs"]
listings = db["Listings"]
chats = db["Chats"]
favorites = db["Favorites"]
admin = db["Admin"]
app = Flask(__name__)
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png", "heic", "zip", "psd"]
alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
            "v", "w", "x", "y", "z"]
app.config["SECRET"] = "123"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

sids = []

maploader = open("loader.txt", "r").read()
class Mail:

    def __init__(self):
        self.port = 587
        self.smtp_server_domain_name = "smtp-relay.sendinblue.com"
        self.sender_mail = "Flauntad@gmail.com"
        self.password = "fEMV21a9yP3n7vZN"

    def send(emails, subject, content):
        
        headers = {

            "api-key":brevoSecret,

            "accept":"application/json",
            "content-type":"application/json"
        }
        data={
           "sender":{
              "name":"Adflaunt",
              "email":"Flauntad@gmail.com"
           },
           "to":[],
           "subject":f"{subject}",
           "htmlContent":content
        }
        for e in emails:
            data["to"].append({"email":e,"name":"Kentel Technologies"})
        page = requests.post("https://api.brevo.com/v3/smtp/email",json=data,headers=headers)

        output = json.loads(page.content)
        output["statusCode"] = page.status_code
        
        return output
def sendmail(email, title, content):
    return True




def send_notification(userID,data,title,message):
    data["click_action"] = "FLUTTER_NOTIFICATION_CLICK"
    payload = {
        "to": f"/topics/{userID}",
        "notification": {"title": title, "body": message},
        "data": data
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization':f'key={firebaseKey}',
    }
    output = requests.post("https://fcm.googleapis.com/fcm/send",data=payload,headers=headers)
    return output

def calcPercentage(number, per):
    return number * (per / 100)


def login_internal(email, phoneNumber, password):
    sq = {"password": password}

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



def getListingsOfUser(userID):
    results =  listings.find({"user":userID})
    output = []
    for r in results:
        output.append(r)
    return output



def getBookingData(bookingID):
    bookings = db["Bookings"]
    allBookings = bookings.find({})
    for b in allBookings:
        listingData = listings.find({"_id":b["_id"]})[0]
        activeOrders = b["activeOrders"]
        waitingForApproval = b["waitingForApproval"]
        doneOrders= b["doneOrders"]
        for a in activeOrders:
            if a["bookingID"] == bookingID:
                return {"status":"active","data":a,"listingData":listingData}
        for w in waitingForApproval:
            if w["bookingID"] == bookingID:
                return {"status":"waitingForApproval","data":w,"listingData":listingData}
        for d in doneOrders:
            if d["bookingID"] == bookingID:
                return {"status":"completed","data":d,"listingData":listingData}
    return {"status":"Not found","data":{}}

def dates2Arr(d1,d2):
    if d1 == None:
        return []
    if d2 == None:
        return []
    d1 = d1.split("-")
    d1y = int(d1[0])
    try:
        d1m = int(d1[1])
    except:
        return []

    try:
        d1d = int(d1[2])
    except:
        return []
    d1 = date(d1y, d1m, d1d)

    d2 = d2.split("-")
    d2y = int(d2[0])
    try:
        d2m = int(d2[1])
    except:
        return []
    try:
        d2d = int(d2[2])
    except:
        return []
    d2 = date(d2y, d2m, d2d)
    d = d2 - d1
    daysWantToBook = []
    for i in range(d.days + 1):
        day = d1 + timedelta(days=i)
        # print(day)
        day = day.strftime("%Y-%m-%d")
        daysWantToBook.append(day)
    return daysWantToBook

def returnWidthLength(data):
    try:
        width  = data["width"]
    except:
        width = 0
    try:
        height = data["length"]
    except:
        height = 0
    return {"width":width,"height":height}



@socketio.on('join')
def joinChat(data):
    email = data["email"]
    password = data["password"]
    phoneNumber = data["phoneNumber"]
    chatID = data["ChatID"]
    user = False
    if email != None:
        allResults = users.find({"email": email, "password": password})
        for a in allResults:
            user = a
            break

    if phoneNumber != None:
        allResults = users.find({"phoneNumber": phoneNumber, "password": password})
        for a in allResults:
            user = a
            break
    if user == False:
        return {"SCC": False, "err": "Could not login"}
    try:
        chat = chats.find({"_id": chatID})[0]
    except:
        return {"SCC": False, "err": "Chat Not Found"}

    chat["messages"].reverse()
    if len(chat["messages"]) > 30:
        chat["messages"] = chat["messages"][:30]

    sid = IDCREATOR_internal(20)
    chatMembers = chat["members"]
    opposition = ""
    for c in chatMembers:
        if c["user"] != user["_id"]:
            opposition = c["user"]
            break 
    if opposition == "":
        oppositionData = {}
    else:
        try:
            oppositionData = users.find({"_id":opposition})[0]
        except:
            oppositionData = {}


    sessionData = {"SCC": True, "SID": sid, "chat": chat, "chatID": chatID, "user": user,"opposition":oppositionData}
    sids.append(sessionData)

    return sessionData





@socketio.on('leave')
def leaveRoom(data):
    sid = data["SID"]
    for s in sids:
        if s["SID"] == sid:
            cin = sids.index(s)
            sids.pop(cin)
            return {"SCC": True, "msg": "Disconnected"}


@socketio.on('send_msg')
def socketiosendmsg(data):
    sid = data["SID"]
    content = data["content"]
    image = data["image"]

    for s in sids:
        if s["SID"] == sid:
            sender = s['user']['_id']

            chatData = chats.find({'_id': s["chatID"]})[0]
            members = chatData["members"]
            receiver = ""
            for m in members:
                if m != sender:
                    receiver = m["user"]
            msgData = {
                "content": content,
                "image": image,
                "sender": sender,
                "receiver": receiver,
                "at": time.time(),
                "_id": IDCREATOR_internal(25)
            }
            chatData["messages"].append(msgData)

            chats.update_one({"_id": s["chatID"]}, {"$set": {"messages": chatData["messages"]}})
            msgData["chatID"] = chatData["_id"]

            socketio.emit("receive", msgData)

            return {"SCC": True, "msgData": msgData}
    return {"SCC": False, "err": "Could not find session"}


@app.route("/tests/chat")
def testChat():
    return render_template("testchat.html")


def IDCREATOR_internal(len_):
    output = ""
    for i in range(len_):
        c = random.choice(alphabet)
        output = output + c
        if random.randint(1, 3) == 2:
            output = output + str(random.randint(0, 9))
    return output


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("docs.html")



class Messaging:
    @app.route("/api/create/chat", methods=["POST"])
    def createChat():
        email = request.form.get("email")
        password = request.form.get("password")

        if password == None:
            return {"SCC": False, "err": "password cannot be none"}
        phoneNumber = request.form.get("phoneNumber")
        user = False
        if email != None:
            allResults = users.find({"email": email, "password": password})
            for a in allResults:
                user = a
                break

        if phoneNumber != None:
            allResults = users.find({"phoneNumber": phoneNumber, "password": password})
            for a in allResults:
                user = a
                break
        if user == False:
            return {"SCC": False, "err": "Could not login"}, 401

        reciever = request.form.get("reciever")
        if reciever == None:
            return {"SCC": False, "err": "reciever is required"}
        try:
            recieverUser = users.find({"_id": reciever})[0]
        except:
            return {"SCC": False, "err": "Could not find reciever"}

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
            "members": [{"user": user["_id"], "profilePicture": user["profileImage"]},
                        {"user": recieverUser["_id"], "profilePicture": recieverUser["profileImage"]}],
            "createdAt": time.time(),
            "messages": [],
            "_id": chatID
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

        users.update_one({"_id": user["_id"]}, {"$set": {"inbox": u1inbox}})
        users.update_one({"_id": recieverUser["_id"]}, {"$set": {"inbox": u2inbox}})
        return chatData

    @app.route("/api/get/inbox", methods=["POST"])
    def getInbox():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        output = []
        if user == False:
            return {"SCC": False, "err": "Login was not successfull"}
        try:
            inbox = user["inbox"]
            for i in inbox:
                try:
                    chatD = chats.find({"_id": i})[0]

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
                        opposition = users.find({"_id": m["user"]})[0]
                        del opposition["password"]
                try:

                    mdata = {"lastMessage": lastMessage, "them": opposition, "chatID": chatD["_id"],
                         "lastMessageTime": lastMessage['at']}
                except:
                    mdata = {"lastMessage": lastMessage, "them": opposition, "chatID": chatD["_id"],
                         "lastMessageTime": 0}
                output.append(mdata)

            users.update_one({"_id": user["_id"]}, {"$set": {"inbox": inbox}})
            output = sorted(output, key=operator.itemgetter('lastMessageTime'))
            output.reverse()
            return {"SCC": True, "output": output}
        except Exception as e:
            return {"SCC": True, "output": [], "reason": "no chat.", "e": str(e)}

    @app.route("/api/get/chat/<chatID>/<page>", methods=["POST"])
    def getchat(page, chatID):
        data2page = 30

        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        if user == False:
            return {"SCC": False, "err": "Could not login"}
        try:
            UINBOX = user["inbox"]
            if chatID not in UINBOX:
                return {"SCC": False, "err": "Could not find chat in inbox"}
        except:
            return {"SCC": False, "err": "Could not find chat in inbox"}
        try:
            page = int(page)
        except:
            return {"SCC": False, "err": "Can't resolve page as an integer. Please enter a valid number"}

        try:
            chatData = chats.find({"_id": chatID})[0]
        except:
            return {"SCC": False, "err": "Could not find chat in the database. This error can be on our hand."}
        messages = chatData["messages"]
        messages.reverse()
        startFrom = data2page * page
        messages = messages[startFrom:]
        messages = messages[:data2page]
        chatData["messages"] = messages
        chatData["page"] = page
        chatData["dataPerPage"] = data2page
        chatData["cindex"] = f"{data2page * page} - {data2page * (page + 1)}"
        chatData["SCC"] = True
        return chatData


class Auth:
    @app.route('/api/register', methods=["POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email")
            allResults = users.find({"email": email})
            scc = True
            for a in allResults:
                scc = False
                return {"SCC": False, "err": "This user exists!"}

            password = request.form.get("password")
            dateOfBirth = request.form.get("dateOfBirth")
            IPDATA = json.loads(request.form.get("IPDATA"))
            try:
                ipraw = IPDATA["query"]
            except:
                return {"SCC": "False", "err": "IPDATA invalid"}
            # IPDATA = request.form.get("IPDATA")
            fullName = request.form.get("fullName")
            profileImage = request.form.get("profileImage")
            phoneNumber = request.form.get("phoneNumber")
            thirdParty = request.form.get("thirdParty")

            if phoneNumber != None:
                phoneNumber = phoneNumber.replace("+", "").replace("(", "").replace(")", "").replace(" ", "")

            if phoneNumber != None and phoneNumber != "":
                allResults = users.find({"phoneNumber": phoneNumber})
                for a in allResults:
                    scc = False
                    return {"SCC": False, "err": "This user exists!"}

            data = {
                "_id": IDCREATOR_internal(23),
                "email": email,
                "password": password,
                "dateOfBirth": dateOfBirth,
                "IPDATA": IPDATA,
                "fullName": fullName,
                "profileImage": profileImage,
                "phoneNumber": phoneNumber,
                "lastTimeLoggedIn": 0,
                "ipraw": ipraw,
                "idVerified": False,
                "thirdParty": thirdParty
            }

            result = users.insert_one(data)
            data["SCC"] = True

            return data

    @app.route("/api/login", methods=["POST"])
    def login():
        try:
            ip = request.environ['REMOTE_ADDR']

        except:
            ip = request.environ['HTTP_X_FORWARDED_FOR']

        email = request.form.get("email")
        password = request.form.get("password")
        phonenumber = request.form.get("phonenumber")
        if email == None and phonenumber == None:
            return {"SCC": False, "err": "You need to specify at least a phone number or a email"}
        if password == None:
            return {"SCC": False, "err": "you need to  specify a password to login"}

        if email != None:
            allResults = users.find({"email": email, "password": password})

        if phonenumber != None:
            allResults = users.find({"phoneNumber": phonenumber, "password": password})

        output = {
            "SCC": False,
            "err": "Credentials are not correct."
        }
        notificationID = request.form.get("notificationID")
        latOfUser = request.form.get("lat")
        longOfUser = request.form.get("long")
        
        if latOfUser != None:
            latOfUser = float(latOfUser)
        if longOfUser != None:
            longOfUser = float(longOfUser)


        for a in allResults:
            output = a
            if notificationID == None:
                if latOfUser != None and longOfUser != None:
                    users.update_one({'_id': output["_id"]}, {"$set": {"lat": latOfUser,"long":longOfUser,"lastTimeLoggedIn": time.time()}})
                else:
                    users.update_one({'_id': output["_id"]}, {"$set": {"lastTimeLoggedIn": time.time()}}) 
            else:
                if latOfUser != None and longOfUser != None:

                    users.update_one({'_id': output["_id"]}, {"$set": {"lastTimeLoggedIn": time.time(),"notificationID":notificationID,"lat": latOfUser,"long":longOfUser}})
                else:
                    users.update_one({'_id': output["_id"]}, {"$set": {"lastTimeLoggedIn": time.time(),"notificationID":notificationID}})
            

            output["SCC"] = True
        try:
            del output["orders"]
        except:
            pass


        try:
            del output["inbox"]
        except:
            pass




        return output

    @app.route("/api/userCheck", methods=["POST"])
    def userCheckAPI():
        email = request.form.get("email")
        phoneNumber = request.form.get("phoneNumber")
        output = {"phoneNumberExists": False, "emailExists": False, "SCC": True}
        statusCode = 200
        if email == None and phoneNumber == None:
            return {"SCC": False, "err": "You need to specify email or phoneNumber"}
        if phoneNumber != None:
            phoneNumber = phoneNumber.replace("+", "").replace("(", "").replace(")", "").replace(" ", "")
            allResults = users.find({"phoneNumber": phoneNumber})
            for a in allResults:
                output["phoneNumberExists"] = True
                output["SCC"] = False
                statusCode = 409
        if email != None:
            allResults = users.find({"email": email})
            for a in allResults:
                output["emailExists"] = True
                output["SCC"] = False
                statusCode = 409

        return output, statusCode

    @app.route("/api/getuser/byid")
    def getUserById():
        id_user = request.args.get("id")
        if id_user == None:
            return {"SCC": False, "err": "you will need id argument for this route."}

        allResults = users.find({"password": id_user})
        for a in allResults:
            return a
        return {"SCC": False, "err": "User not found"}, 404

    
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
                return {"err": "Please specify 'file'."}
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
                    logger.write(f"UPLOAD {ip} | " + originalFile + " @" +
                                 str(time.time()) + " as " + filename + "." + ext + "\n")
                    return {"file": filename + "." + ext, "time": time.time(), "ctime": time.ctime(time.time())}

                except Exception as e:
                    return {"err": str(e)}
            else:
                return {"err": "File type is not allowed in this server", "allowedFileTypes": ALLOWED_EXTENSIONS,
                        "maxSize": "10MB"}
        logger.close()


class Profile:
    @app.route("/api/getprofile/<userID>")
    def getProfileWithUserId(userID):
        output = users.find({"_id": userID})
        try:
            output = output[0]
            del output["password"]
            return output
        except:
            pass

        return {"SCC": False, "err": "Could not find user."}

    @app.route("/api/updateprofile", methods=["POST"])
    def updateProfile():

        # Notes:
        # Email password and phone number is required for this field
        # Updating the login credentials is in the other part
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
        # IPDATA = request.form.get("IPDATA")
        fullName = request.form.get("fullName")
        profileImage = request.form.get("profileImage")
        phoneNumber = request.form.get("phoneNumber")
        if phoneNumber != None:
            phoneNumber = phoneNumber.replace("+", "").replace("(", "").replace(")", "").replace(" ", "")
        # Login phase
        allResults = users.find({"email": email, "password": password, "phoneNumber": phoneNumber})
        try:
            r = allResults[0]
        except:
            return {"SCC": False, "err": "Could not login"}
        rid = r["_id"]

        updateData = {}

        if dateOfBirth != None and dateOfBirth != r["dateOfBirth"]:
            updateData["dateOfBirth"] = dateOfBirth

        if fullName != None and fullName != r["fullName"]:
            updateData["fullName"] = fullName
        if profileImage != None and profileImage != r["profileImage"]:
            updateData["profileImage"] = profileImage

        if phoneNumber != None and phoneNumber != r["phoneNumber"]:
            updateData["phoneNumber"] = phoneNumber
        if ipraw != None and ipraw != r["ipraw"]:
            updateData["ipraw"] = ipraw
        if IPDATA != None and IPDATA != r["IPDATA"]:
            updateData["IPDATA"] = IPDATA

        users.update_one({'_id': rid}, {"$set": updateData})
        outputdata = allResults = users.find({"email": email, "password": password, "phoneNumber": phoneNumber})[0]
        outputdata["SCC"] = True

        return outputdata

    @app.route("/api/update_login_credentials", methods=["POST"])
    def update_login_credentials():
        # How it works?
        # So you send whatevery you want to update and also authenticate, 
        # we are checking if the information matches with the old ones and 
        # replace them with the new ones
        email = request.form.get("email")
        password = request.form.get("password")
        new_email = request.form.get("new_email")
        new_password = request.form.get("new_password")
        new_phoneNumber = request.form.get("new_phoneNumber")
        phoneNumber = request.form.get("phoneNumber")
        queryData = {"password": password}
        if phoneNumber != None:
            queryData["phoneNumber"] = phoneNumber
        if email != None:
            queryData["email"] = email

        searcher = users.find(queryData)
        try:
            udata = searcher[0]

        except:
            return {"SCC": False, "err": "Check the credentials for authentication"}

        if new_email != None:
            udata["email"] = new_email
        if new_password != None:
            udata["password"] = new_password
        if new_phoneNumber != None:
            udata["phoneNumber"] = new_phoneNumber

        users.update_one({"_id": udata["_id"]}, {"$set": udata})
        udata["SCC"] = True

        return udata

        return {}


class Verification:
    @app.route("/api/verify/sms")
    def sms_verification():
        # NOTE : THIS SHIT JUST SUPPORTS US NUMBERS AS I UNDERSTOOD. DONT USE IT ELSEWHERE
        phoneNumber = request.args.get("phoneNumber")
        code_verify = random.randint(1, 1000000)
        try:
            message = twcl.messages.create(
                body=f"Adflaunt Verification Code:{code_verify}",
                from_=phoneNumber_tw,
                to=phoneNumber
            )
        except Exception as e:
            print(e)
            return {"SCC": False, "err": str(e)}
        return {"SCC": True, "m.body": message.body}

    @app.route("/api/verify/email")
    def email_verification():
        email = request.args.get("email")
        if email == None:
            return {"SCC":False,"err":"email is required to use this endpoint"}
        try:
            email.split("@")[1]
        except:
            return {"SCC":False,"err":"Email malformatted"}
        emails = [email]
        verificationCode = random.randint(10000,100000)
        verificationCode = str(verificationCode)
        html_ = """
        <!DOCTYPE html> <html> <head> <meta charset="utf-8"> <meta http-equiv="x-ua-compatible" content="ie=edge"> <title>Confirm your email - Adflaunt</title> <meta name="viewport" content="width=device-width, initial-scale=1"> <style type="text/css"> /** * Google webfonts. Recommended to include the .woff version for cross-client compatibility. */ @media screen { @font-face { font-family: "Source Sans Pro"; font-style: normal; font-weight: 400; src: local("Source Sans Pro Regular"), local("SourceSansPro-Regular"), url(https://fonts.gstatic.com/s/sourcesanspro/v10/ODelI1aHBYDBqgeIAH2zlBM0YzuT7MdOe03otPbuUS0.woff) format("woff"); } @font-face { font-family: "Source Sans Pro"; font-style: normal; font-weight: 700; src: local("Source Sans Pro Bold"), local("SourceSansPro-Bold"), url(https://fonts.gstatic.com/s/sourcesanspro/v10/toadOcfmlt9b38dHJxOBGFkQc6VGVFSmCnC_l7QZG60.woff) format("woff"); } } /** * Avoid browser level font resizing. * 1. Windows Mobile * 2. iOS / OSX */ body, table, td, a { -ms-text-size-adjust: 100%; /* 1 */ -webkit-text-size-adjust: 100%; /* 2 */ } /** * Remove extra space added to tables and cells in Outlook. */ table, td { mso-table-rspace: 0pt; mso-table-lspace: 0pt; } /** * Better fluid images in Internet Explorer. */ img { -ms-interpolation-mode: bicubic; } /** * Remove blue links for iOS devices. */ a[x-apple-data-detectors] { font-family: inherit !important; font-size: inherit !important; font-weight: inherit !important; line-height: inherit !important; color: inherit !important; text-decoration: none !important; } /** * Fix centering issues in Android 4.4. */ div[style*="margin: 16px 0;"] { margin: 0 !important; } body { width: 100% !important; height: 100% !important; padding: 0 !important; margin: 0 !important; } /** * Collapse table borders to avoid space between cells. */ table { border-collapse: collapse !important; } a { color: #1a82e2; } img { height: auto; line-height: 100%; text-decoration: none; border: 0; outline: none; } </style> </head> <body style="background-color: #e9ecef;"> <!-- start preheader --> <div class="preheader" style="display: none; max-width: 0; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #fff; opacity: 0;"> A preheader is the short summary text that follows the subject line when an email is viewed in the inbox. </div> <!-- end preheader --> <!-- start body --> <table border="0" cellpadding="0" cellspacing="0" width="100%"> <!-- start logo --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="center" valign="top" style="padding: 36px 24px;"> <a href="" target="_blank" style="display: inline-block;"> <img src="https://adflaunt.com/static/adflaunt.png" alt="Logo" border="0" width="48" style="display: block; width: 48px; max-width: 48px; min-width: 48px;"> </a> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end logo --> <!-- start hero --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="left" bgcolor="#ffffff" style="padding: 36px 24px 0; font-family: 'Source Sans Pro', Helvetica, Arial, sans-serif; border-top: 3px solid #d4dadf;"> <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -1px; line-height: 48px;">Confirm Your Email Address</h1> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end hero --> <!-- start copy block --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <!-- start copy --> <tr> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: 'Source Sans Pro', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px;"> <p style="margin: 0;">Tap the button below to confirm your email address. If you didn't create an account on <a href="">Adflaunt</a>, you can safely delete this email.</p> </td> </tr> <!-- end copy --> <!-- start button --> <tr> <td align="left" bgcolor="#ffffff"> <table border="0" cellpadding="0" cellspacing="0" width="100%"> <tr> <td align="center" bgcolor="#ffffff" style="padding: 12px;"> <table border="0" cellpadding="0" cellspacing="0"> <tr> <td align="center" style="border-radius: 6px;"> <a style="display: inline-block; padding: 16px 36px; font-family: 'Source Sans Pro', Helvetica, Arial, sans-serif; font-size: 26px; color: #000000; text-decoration: none; border-radius: 6px;letter-spacing:20px">"""+verificationCode+"""</a> </td> </tr> </table> </td> </tr> </table> </td> </tr> <!-- end button --> <!-- start copy --> <tr style="position: relative;"> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: 'Source Sans Pro', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px; border-bottom: 3px solid #d4dadf"> <p style="margin: 0;">Adflaunt <svg style="transform: rotate(180deg);" height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> <p style="margin: 0;font-size:10px;position:absolute;right:20px;bottom:25px"> <svg height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> </td> </tr> <!-- end copy --> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end copy block --> <!-- start footer --> <tr> <td align="center" bgcolor="#e9ecef" style="padding: 24px;"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end footer --> </table> <!-- end body --> </body> </html>""" 
        out = Mail.send(emails,"Verify Your Email - Adflaunt",html_)

        return {"SCC":True,"verificationCode":verificationCode}







class ReportingSystem:
    @app.route("/api/report/<userID>", methods=["POST"])
    def apireport(userID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        querydata = {}
        if email == None and phoneNumber == None:
            return {"SCC": False, "err": "You need to specify email or phoneNumber"}
        if email != None:
            querydata["email"] = email
        if phoneNumber != None:
            querydata["password"] = password
        try:
            user = users.find(querydata)[0]
        except:
            return {"SCC": False, "err": "Could not authenticate"}
        title = request.form.get("title")
        description = request.form.get("description")
        timeitreported = time.time()
        try:
            user_ = users.find({"_id": userID})[0]
        except:
            return {"SCC": False, "err": "Could not find the user"}
        if userID == user["_id"]:
            return {"SCC": False, "err": "Users can't report themselves."}
        data = {
            "_id": IDCREATOR_internal(20),
            "title": title,
            "description": description,
            "timereported": timeitreported,
            "reporter": user["_id"],
            "suspect": userID
        }
        reports.insert_one(data)
        data["SCC"] = True
        return data

    @app.route("/api/report/bugs", methods=["POST", "GET"])
    def reportBugs():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            title = request.form.get("title")
            description = request.form.get("description")
            bugImage = request.form.get("bugImage")
            # Bug image should be a static filename
            phoneNumber = request.form.get("phoneNumber")
            data = {
                "reportedAt": time.time(),
                "email": email,
                "title": title,
                "description": description,
                "bugImage": bugImage,
                "phoneNumber": phoneNumber,
                "_id": IDCREATOR_internal(20)
            }

            querydata = {}
            if email == None and phoneNumber == None:
                return {"SCC": False, "err": "You need to specify email or phoneNumber"}
            if email != None:
                querydata["email"] = email
            if phoneNumber != None:
                querydata["password"] = password
            try:
                user = users.find(querydata)[0]
            except:
                return {"SCC": False, "err": "Could not authenticate"}
            uid = user["_id"]
            data["userID"] = uid
            bugs.insert_one(data)
            data["SCC"] = True

            return data
        if request.method == "GET":
            return {"SCC": False, "err": "This endpoint does not support get requests yet."}


class IDVerification:
    @app.route("/api/verify/ID", methods=["POST"])
    def IDVERIFY():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            phoneNumber = request.form.get("phoneNumber")
            if password == None:
                return {"SCC": False, "err": "password can't be null."}
            query_cr = {"password": password}
            if email != None:
                query_cr["email"] = email
            if phoneNumber != None:
                query_cr["phoneNumber"] = phoneNumber
            if email == None and phoneNumber == None:
                return {"SCC": False, "err": "Email or phonenumber is required for authentication"}

            try:
                user = users.find(query_cr)[0]
            except:
                return {"SCC": False, "err": "Could not authenticate"}

            UID = user["_id"]

            photoOfId = request.form.get("photoOfId")
            fullName = request.form.get("fullName")
            dateOfBirth = request.form.get("dateOfBirth")

            if photoOfId == None:
                return {"SCC": False, "err": "You need to specify photoOfId as a static filename"}

            users.update_one({"_id": UID}, {"$set": {"photoOfId": photoOfId, "idVerified": True}})
            user["photoOfId"] = photoOfId
            user["idVerified"] = True
            user["SCC"] = True
            return user


class Listings:
    @app.route("/api/create/listing", methods=["POST","PUT"])
    def createlisting():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        if password == None:
            return {"SCC": False, "err": "password can't be null."}
        query_cr = {"password": password}
        if email != None:
            query_cr["email"] = email
        if phoneNumber != None:
            query_cr["phoneNumber"] = phoneNumber
        if email == None and phoneNumber == None:
            return {"SCC": False, "err": "Email or phonenumber is required for authentication"}

        try:
            user = users.find(query_cr)[0]
        except:
            return {"SCC": False, "err": "Could not authenticate"}
        if user['idVerified'] == False:
            return {"SCC": False, "err": "ID NOT VERIFIED."}
        if request.method == "PUT":
            listingID = request.form.get("listingID")
            if listingID == None:
                return {"SCC":False,"err":"listingID is required for editing"}
            try:
                oldListingData= listings.find({"_id":listingID})[0]
            except:
                return {"SCC":False,"err":"Listing does not exist"}

        typeOfAd = request.form.get("typeOfAd")  # Number 0-1-2
        """
        0-outdoor
        1-indoor
        2-vehicle

        """
        lat = request.form.get("lat")  # number, float
        long = request.form.get("long")  # number, float
        images = request.form.get("images")
        title = request.form.get("title")
        price = request.form.get("price")  # number integer
        location = request.form.get("location")
        revision_limit = request.form.get("revision_limit")  # number integer

        width = request.form.get("width")#Float number
        length = request.form.get("length")# float number

        type_of_listing = request.form.get("type")  # number - between 1-6
        check_in = request.form.get("check_in")  # Date
        check_out = request.form.get("check_out")  # Date
        population = request.form.get("population")  # number
        discountAvailable = request.form.get("discountAvailable")  # Number between 1-4
        """ 
        Discount available:
        yes
        no
        long-term
        partial
        """
        tags = request.form.get("tags")
        extras = request.form.get("extras")  # fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
        requirements = request.form.get("requirements")  # fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
        description = request.form.get("description")  # STR
        bookingNote = request.form.get("bookingNote")  # STR OPT
        bookingOffset = request.form.get("bookingOffset")  # INT OPT
        "Set how many days are required prior to the booking date"
        bookingWindow = request.form.get("bookingWindow")  # INT OPT
        "Set how many days in advance a booking can be made."
        minimumBookingDuration = request.form.get("minimumBookingDuration")
        BookingImportURL = request.form.get("BookingImportURL")
        city = request.form.get("city")
        country = request.form.get("country")
        state = request.form.get("state")

        if typeOfAd == None or width==None or length==None or images == None or lat == None or long == None or title == None or price == None or revision_limit == None or location == None or type_of_listing == None or check_in == None or check_out == None or population == None or discountAvailable == None or description == None or extras == None or requirements == None:
            return {"SCC": False, "err": "some parameters are required"}

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
            return {"SCC": False, "err": "Population should be an integer"}
        try:
            price = int(price)
        except:
            return {"SCC": False, "err": "Price should be an integer"}

        try:
            tags = ''.join([i if ord(i) < 128 else ' ' for i in tags])
            # may give some errors
            tags = tags.split("|-|")
        except:
            tags = []

        if type_of_listing == "1":
            type_of_listing = "Yard Sign"

        if type_of_listing == "2":
            type_of_listing = "Banner"

        if type_of_listing == "3":
            type_of_listing = "Floor Sign"

        if type_of_listing == "4":
            type_of_listing = "Poster"

        if type_of_listing == "5":
            type_of_listing = "Bill Board"

        if type_of_listing == "6":
            type_of_listing = "Digital Signage"

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
            return {"SCC": False, "err": "typeOfAd Should be one of those: 0,1,2"}


        try:
            width = float(width)

        except:
            return {"SCC":False,"err":"width should be a float"}
        try:
            height = float(length)

        except:
            return {"SCC":False,"err":"height should be a float"}

        inchFootage = width*height 
        sqfeet = inchFootage*0.006944444


        data = {
            "title": title,
            "price": price,
            "lat": lat,
            "long": long,
            "images": images,
            "location": location,
            "revision_limit": revision_limit,
            "type": type_of_listing,
            "check_in": check_in,
            "check_out": check_out,
            "population": population,
            "tags": tags,
            "extras": extras,
            "requirements": requirements,
            "description": description,
            "bookingNote": bookingNote,
            "bookingOffset": bookingOffset,
            "bookingWindow": bookingWindow,
            "minimumBookingDuration": minimumBookingDuration,
            "BookingImportURL": BookingImportURL,
            "_id": IDCREATOR_internal(40),
            "user": user['_id'],
            "typeOfAdd": typeOfAd,
            "city": city,
            "state": state,
            "country": country,
            "width":width,
            "height":height,
            "sqfeet":sqfeet,
            "sqfootage":sqfeet,
            "inchFootage":inchFootage
        }
        if request.method == "POST":
            db["Listings"].insert_one(data)
            for t in tags:
                t = t.strip()
                if t!= "":
                    db[t].insert_one(data)
            db[typeOfAd].insert_one(data)

            data["SCC"] = True

            return data
        if request.method == "PUT":
            storeData= data 
            
            oldTags = oldListingData["tags"]
            oldTypeOfAd = oldListingData["typeOfAdd"]
            del data["_id"]

            db["Listings"].update_one({"_id":listingID},{"$set":data})
            for t in oldTags:
                if t not in tags:
                    
                    db[t].delete_one({"_id":listingID})
            for t in tags:
                if t not in oldTags:
                    data["_id"] = listingID
                    db[t].insert_one(data )
                    del data["_id"]
                else:
                    db[t].update_one({"_id":listingID},{"$set":data})


            if typeOfAd != oldTypeOfAd:
                db[oldTypeOfAd].delete_one({"_id":listingID})
                data["_id"] = listingID
                db[typeOfAd].insert_one(storeData)
            else:
                db[typeOfAd].update_one({"_id":listingID},{"$set":data})



            data["SCC"] = True 

            return data
        


    @app.route("/api/get/listings", methods=["GET"])
    def get_listings():
        r = redis.Redis()
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
                return {"SCC": False, "err": "You need to specify mode to use this endpoint"}

            if mode == "near":
                if lat == None or long == None:
                    return {"SCC": False, "err": "We need lat and long to use near function."}
                try:
                    lat = float(lat)
                    long = float(long)
                except:
                    return {"SCC": False, "err": "Lat and long as float"}
                for l in listings.find({}):
                    lat_listing = l["lat"]
                    long_listing = l["long"]
                    listingLocation = (lat_listing, long_listing)
                    originalLocation = (lat, long)

                    distance =geopy.distance.geodesic(listingLocation, originalLocation).km
                    l["distance"] = distance
                    if distance < distanceAsKm:
                        output.append(l)
                output = sorted(output, key=operator.itemgetter('distance'))

            if mode == "search":
                if q == None:
                    return {"SCC": False, "err": "for search mode, you need to send query(q)"}

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
                        state = ""
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
                    

                    try:
                        reviews = l["reviews"]
                    except:
                        reviews = []
                    reviewsTotal = 0 
                    reviewsCount = len(reviews)
                    for r in reviews:
                        star = r["star"]
                        reviewsTotal += star 
                    try:
                        average = reviewsTotal/reviewsCount 
                    except:
                        average = 0 
                    priority += average/6


                    if priority > 0:
                        l["priority"] = -priority

                        output.append(l)
                output = sorted(output, key=operator.itemgetter('priority'))

            sdata = {"output": output, "q": q, "mode": mode}
            r.mset({f"{sessionName}": json.dumps(sdata)})

        else:
            if mode == "search":
                try:
                    cdata = json.loads(r.get(sessionName))
                    output = cdata["output"]
                    try:
                        page = int(page)
                    except:
                        return {"SCC": False, "err": "Send 'page' as INTEGER"}
                    try:
                        if len(output) - (page * 10 - 10) > 10:

                            output = output[(page * 10 - 10):]

                            output = output[:10]
                        elif len(output) - (page * 10 - 10) < 10 and len(output) - (page * 10 - 10) > 0:

                            output = output[(page * 10 - 10):]
                        else:
                            return {"SCC": False, "output": []}

                        return {"SCC": True, "output": output, "session": sessionName}
                    except:
                        return {"SCC": False, "err": "over pagination"}
                except:
                    return {"SCC": False, "err": "Session ID invalid"}

            if mode == "near":
                try:
                    cdata = json.loads(r.get(sessionName))
                    output = cdata["output"]
                    try:
                        page = int(page)
                    except:
                        return {"SCC": False, "err": "Send 'page' as INTEGER"}
                    try:
                        if len(output) - (page * 10 - 10) > 10:

                            output = output[(page * 10 - 10):]

                            output = output[:10]
                        elif len(output) - (page * 10 - 10) < 10 and len(output) - (page * 10 - 10) > 0:

                            output = output[(page * 10 - 10):]
                        else:
                            return {"SCC": False, "output": []}

                        return {"SCC": True, "output": output, "session": sessionName}
                    except:
                        return {"SCC": False, "err": "over pagination"}
                except:
                    return {"SCC": False, "err": "Session ID invalid"}

        dataCount = len(output)

        if len(output) > 10:
            output = output[:10]

        data = {"SCC": True, "output": output, "session": sessionName, "dataCount": dataCount}
        return data

    @app.route("/api/home/listings", methods=["GET"])
    def homeListings():
        # Just takes coordinates
        lat = request.args.get("lat")
        long = request.args.get("long")
        if lat == None or long == None:
            return {"SCC": False, "err": "lat and long can not be none."}
        output = []
        for l in listings.find({}):
            lat_listing = l["lat"]
            long_listing = l["long"]
            listingLocation = [lat_listing, long_listing]
            originalLocation = [lat, long]

            distance = math.dist(originalLocation, listingLocation) * 111
            l["distance"] = distance

            output.append(l)

        output = sorted(output, key=operator.itemgetter('distance'))
        return {"SCC": True, "output": output}

    @app.route("/api/listing/<listingID>")
    def listingIndividual(listingID):
        try:
            listingData = listings.find({"_id": listingID})[0]
            userID = listingData["user"]
            userData = users.find({"_id": userID})[0]
            listingData["user"] = userData
            listingData["SCC"] = True

            return listingData
        except:
            return {"SCC": False, "err": "Could not find listing"}

    @app.route("/api/get/listingsFilterer")
    def getListingsByCategory():
        sessionName =request.args.get("session")
        page= request.args.get("page")
        query = request.args.get("q")
        if query == None:
            query = ""
        if sessionName == None:
            category = request.args.get("category")
            if category == None:
                category= "Listings"
            priceStart = request.args.get("priceStart")
            priceEnd = request.args.get("priceEnd")

            if priceStart == None:
                priceStart = 0 
            if priceEnd == None:
                priceEnd = 1000000
            try:
                priceStart = float(priceStart)
                priceEnd = float(priceEnd)
            except:
                priceStart = 0
                priceEnd=1000000            
            from_date = request.args.get("from")
            to_date = request.args.get("to")
            type_of_listing = request.args.get("type")
            if type_of_listing == None:
                type_of_listing = ""
            if type_of_listing == "1":
                type_of_listing = "Yard Sign"

            if type_of_listing == "2":
                type_of_listing = "Banner"

            if type_of_listing == "3":
                type_of_listing = "Floor Sign"

            if type_of_listing == "4":
                type_of_listing = "Poster"

            if type_of_listing == "5":
                type_of_listing = "Bill Board"

            if type_of_listing == "6":
                type_of_listing = "Digital Signage"

            daysWantToBook = dates2Arr(from_date,to_date)
            
            output = []
            categoryData = db[category].find({})
            lat = request.args.get("lat")
            long_ = request.args.get("long")
            distanced = False
            for c in categoryData:
                try:
                    c = listings.find({"_id":c["_id"]})[0]
                except:
                    continue

                lat_listing = c["lat"]
                long_listing = c["long"]

                listingLocation = (lat_listing, long_listing)
                originalLocation = [lat, long_]

                if lat != None and long_!=None:
                    try:
                        lat = float(lat)
                        long_ = float(long_ )
                    except:
                        return {"SCC":False,"err":"Check lat and long values"}
                    originalLocation = (lat, long_)
                    distance = geopy.distance.geodesic(listingLocation,originalLocation).km
                    c["distance"] = distance
                    distanced = True

                try:
                    allReviews = c["reviews"]
                except:
                    allReviews = []
                totalPoints = 0
                numberOfReviews= len(allReviews)

                for a in allReviews:
                    star = a["star"]
                    totalPoints += star 
                try:
                    average = totalPoints/numberOfReviews
                except:
                    average = 0

                c["averageRating"] = average

                try:
                    cbook = c["Bookings"]
                except:
                    cbook = []
                ctype = c["type"]
                
                gonnacontinue = False
                for d in daysWantToBook:
                    if d in cbook:
                        gonnacontinue = True 
                        break 
                if gonnacontinue:
                    continue
                        
                
                price = c["price"]
                if distanced:
                    try:
                        searchPoint = c["distance"]/average 
                    except:
                        searchPoint = c["distance"]/1 
                    c["searchPoint"] = searchPoint
                tags = c["tags"]
                tagsString = ""
                for t in tags:
                    tagsString += " "+t

                titleString = c["title"]
                descriptionString = c["description"]
                if query in titleString or query in tagsString or query in description:

                    if price>priceStart and price<priceEnd and type_of_listing in ctype:
                        output.append(c)
                else:
                    pass

            if distanced:
                output = sorted(output,key=operator.itemgetter('searchPoint'))
            else:
                output = sorted(output,key=operator.itemgetter('averageRating'))
            sid = IDCREATOR_internal(20)
            r.mset({sid:json.dumps(output)})
            return {"SCC":True,"output":output[:10],"sid":sid}
        else:
            if page == None:
                page = 1
            try:
                output = json.loads(r.get(sessionName))
            except:
                return {"SCC":False,"err":"Check session you entered"}
            output = output[:page*10][10*(page-1):]
            return {"SCC":True,"output":output,"sid":sessionName}

            
    @app.route("/api/get/ListingsOfUser",methods=["POST"])
    def APIGETLISTINGSOFUSER ():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Auth false"}
        output =  getListingsOfUser(user["_id"])  
        return {"SCC":True,"output":output}   

    @app.route("/api/listings/<userID>")
    def getListingsOfUserApp(userID):
        return {"SCC":True,"output":getListingsOfUser(userID)}
class Favorites:
    @app.route("/api/addto/favorites", methods=["POST", "DELETE"])
    def addFavorites():

        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        if user == False:
            return {"SCC": False, "err": "Login Failed."}

        UID = user["_id"]
        listingID = request.form.get("listingID")
        if request.method == "POST":

            if listingID == None:
                return {"SCC": False, "err": "listingID form data is required to add that listing to favorites."}
            try:
                favDATA = favorites.find({"_id": UID})[0]
            except:
                favDATA = {
                    "forUser": UID,
                    "favorites": [],
                    "_id": UID

                }
                favorites.insert_one(favDATA)

            try:
                listingDATA = listings.find({"_id": listingID})[0]
            except:
                return {"SCC": False, "err": "Could not find listing."}

            favDATA["favorites"].append(listingDATA)
            favorites.update_one({"_id": UID}, {"$set": favDATA})

            return {"SCC": True, "favDATA": favDATA}
        if request.method == "DELETE":
            try:
                favDATA = favorites.find({"_id": UID})[0]
            except:
                return {"SCC": False, "err": "You don't have any favorites"}
            AllFavorites = favDATA["favorites"]

            for f in AllFavorites:

                if f["_id"] == listingID:
                    cindex = AllFavorites.index(f)

                    AllFavorites.pop(cindex)

                    favorites.update_one({"_id": UID}, {"$set": {"favorites": AllFavorites}})
                    return {"SCC": True, "deleted": listingID}

            return {"SCC": False, "err": "Could not find listing in your favorites"}

    @app.route("/api/get/favorites", methods=["POST"])
    def getFavorites():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        if user == False:
            return {"SCC": False, "err": "Login Failed."}
        try:

            FAVDATA = favorites.find({"_id": user["_id"]})[0]
        except:
            FAVDATA = {
                "forUser": UID,
                "favorites": [],
                "_id": UID
            }
        FAVDATA["SCC"] = True

        return FAVDATA


class Admin:
    @app.route("/admin")
    def admin_main():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return redirect("/admin/login")
        return render_template("adminIndex.html", adminData=adminData)

    @app.route("/admin/login", methods=["POST", "GET"])
    def adminLogin():
        if request.method == "GET":
            return render_template("adminLogin.html")
        if request.method == "POST":

            expire_date = datetime.datetime.now()
            expire_date = expire_date + datetime.timedelta(days=2)
            username = request.form.get("username")
            password = request.form.get("password")
            try:
                admin.find({"username": username, "password": password})[0]
            except:
                return render_template("adminLogin.html", err="Email or password is not correct.")

            response = make_response(redirect("/admin"))
            response.set_cookie("username", encrypt(username), expires=expire_date)
            response.set_cookie("password", encrypt(password), expires=expire_date)

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
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return redirect("/admin/login")

        return render_template("adminUser.html", users=output, adminData=adminData)

    @app.route("/admin/user/<userID>")
    def viewUserIndependently(userID):
        userListings = listings.find({"user": userID})
        userListingsArray = []
        for ul in userListings:
            userListingsArray.append(ul)
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return redirect("/admin/login")

        try:
            userdata = users.find({"_id": userID})[0]
            try:
                userInbox = userdata["inbox"]
            except:
                userInbox = []
            returnInbox = []
            for u in userInbox:
                try:
                    inboxData = chats.find({"_id": u})[0]
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
                oppositionData = users.find({"_id": opposite})[0]
                idata = {
                    "lastMessage": lastMessage,
                    "oppositionData": oppositionData,
                    "chatID": u
                }
                returnInbox.append(idata)
            return render_template("userView.html", data=userdata, maploader=maploader, userListings=userListingsArray,
                                   inbox=returnInbox, ctime=time.ctime)
        except Exception as e:

            return render_template("user404.html", error=e)

    @app.route("/admin/map")
    def adminMap():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
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
        return render_template("adminMap.html", countryDict=json.dumps(countryDict, indent=4), maploader=maploader)

    @app.route("/admin/booking")
    def adminBooking():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return redirect("/admin/login")

        bookings = db["Bookings"]
        allBookings = bookings.find({})
        approvalData = {}
        listingData = {}

        for a in allBookings:
            clisting = listings.find({"_id":a["_id"]})
            for c in clisting:
                listingData[c["_id"]] = c


            activeOrders = a["activeOrders"]
            try:
                approvalData[a["_id"]]
            except:
                approvalData[a["_id"]] = []
            for ao in activeOrders:
                ao["status"] = "active"
                approvalData[a["_id"]].append(ao)

            waitingForApproval = a["waitingForApproval"]
            
            for wa in waitingForApproval:
                wa["status"] = "waitingForApproval"
                approvalData[a["_id"]].append(wa)



        return render_template("orderApprovalAdmin.html",
                               approvalData=approvalData,
                               listingData=listingData,
                               printFee=printFee,
                               commisionRate=commisionRate,
                               calcPercentage=calcPercentage,
                               returnWidthLength=returnWidthLength
                               )

    @app.route("/admin/listings")
    def adminListings():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return redirect("/admin/login")

        output = []
        allListings = listings.find({})
        for a in allListings:
            output.append(a)


        return render_template("listingsAdmin.html",listings=json.dumps({"output":output}))

    @app.route("/admin/api/acceptBooking/<listingID>/<ListIndex>")
    def AcceptBooking(listingID, ListIndex):
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return {"SCC": False, "err": "Authentication Failed"}

        bookings = db["Bookings"]

        try:
            bookingData = bookings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing"}
        try:
            currentData = bookingData["waitingForApproval"][int(ListIndex)]
        except:
            return {"SCC": False, "err": "Index value is not correct"}
        bookingData["waitingForApproval"].pop(int(ListIndex))
        bookingData["activeOrders"].append(currentData)
        bookings.update_one({"_id": listingID}, {"$set": {"waitingForApproval": bookingData["waitingForApproval"],
                                                          "activeOrders": bookingData["activeOrders"]}})

        # sendMSG -> to host for informing that they have a new order
        # sendMSG -> to user for informing their order is accepted by system admin
        listingData = listings.find({"_id": listingID})[0]
        host = listingData["user"]
        hostData = users.find({"_id": host})[0]
        try:
            orders = hostData["orders"]
        except:
            orders = []
        orders.append(currentData)
        users.update_one({"_id": host}, {"$set": {"orders": orders}})

        return {"SCC": True, "msg": "Updated"}

    @app.route("/admin/api/denyBooking/<listingID>/<ListIndex>")
    def DenyBooking(listingID, ListIndex):
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:

            return {"SCC": False, "err": "Authentication Failed"}

        bookings = db["Bookings"]

        try:
            bookingData = bookings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing"}
        try:
            currentData = bookingData["waitingForApproval"][int(ListIndex)]
        except:
            return {"SCC": False, "err": "Index value is not correct"}
        bookingData["waitingForApproval"].pop(int(ListIndex))
        # bookingData["activeOrders"].append(currentData)
        bookings.update_one({"_id": listingID}, {"$set": {"waitingForApproval": bookingData["waitingForApproval"]}})

        # sendMSG -> DONT INFORM HOST.
        # sendMSG -> Request denied
        customer = currentData["customer"]
        customer = users.find({"_id": customer})[0]
        orders = customer["orders"]
        for o in orders:
            bookingID = o["bookingID"]
            if bookingID == currentData["bookingID"]:
                cindex = orders.index(o)
        orders.pop(cindex)
        users.update_one({"_id": currentData["customer"]}, {"$set": {"orders": orders}})
        listingData = listings.find({"_id": listingID})[0]
        daysWantToBook = currentData["daysWantToBook"]
        for d in daysWantToBook:
            cindex = listingData["Bookings"].index(d)
            listingData["Bookings"].pop(cindex)
        listings.update_one({"_id": listingID}, {"$set": {"Bookings": listingData["Bookings"]}})

        return {"SCC": True, "msg": "Denied successfully"}


class Booking:
    @app.route("/api/book", methods=["POST"])
    def book_it():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        UID = user["_id"]
        if user == False:
            return {"SCC": False, "err": "Authentication failed"}, 401
        paymentID = request.form.get("paymentID")
        if paymentID == None:
            return {"SCC":False,"err":"paymentID is required"},401


        listingID = request.form.get("listingID")
        try:
            listingData = listings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing."},404

        pricePerDay = listingData["price"]

        title = request.form.get("title")
        description = request.form.get("description")

        d1 = request.form.get("from")
        d2 = request.form.get("to")
        if d1 == None or d2 == None:
            return {"SCC": False,
                    "err": "'from' and 'to' are not definded, for booking you need to enter those correctly"},401
        d1 = d1.split("-")
        d1y = int(d1[0])
        try:
            d1m = int(d1[1])
        except:
            return {"SCC": False, "err": "Date format is invalid"},401

        try:
            d1d = int(d1[2])
        except:
            return {"SCC": False, "err": "Date format is invalid"},401
        d1 = date(d1y, d1m, d1d)

        d2 = d2.split("-")
        d2y = int(d2[0])
        try:
            d2m = int(d2[1])
        except:
            return {"SCC": False, "err": "Date format is invalid"},401
        try:
            d2d = int(d2[2])
        except:
            return {"SCC": False, "err": "Date format is invalid"},401
        d2 = date(d2y, d2m, d2d)
        d = d2 - d1
        daysWantToBook = []
        for i in range(d.days + 1):
            day = d1 + timedelta(days=i)
            # print(day)
            day = day.strftime("%Y-%m-%d")
            daysWantToBook.append(day)

        price = pricePerDay * len(daysWantToBook)
        printingFile = request.form.get("printingFile")

        orderData = {
            "title": title,
            "description": description,
            "daysWantToBook": daysWantToBook,
            "pricePerDay": pricePerDay,
            "price": price,
            "printingFile": printingFile,
            "bookingID": IDCREATOR_internal(30),
            "customer": user["_id"],
            "timeStamp": time.time(),
            "paymentID":paymentID

        }

        print(json.dumps(orderData, indent=4), flush=True)
        d1 = request.form.get("from")
        d2 = request.form.get("to")

        try:
            orders = user["orders"]
        except:
            orders = []
        orders.append(orderData)
        users.update_one({"_id": user["_id"]}, {"$set": {"orders": orders}})

        try:
            output = Booker.book(listingID, d1, d2, orderData)
            return output
        except Exception as e:
            return {"SCC": False, "err": str(e)}

        return {"SCC": True, "orderData": orderData}

    @app.route("/api/booking/calendar/<listingID>")
    def calendarAPI(listingID):
        bookings = db["Bookings"]
        try:
            booking_data = bookings.find({"_id": listingID})[0]
            datesList = []
            activeOrders = booking_data["activeOrders"]
            waitingForApproval = booking_data["waitingForApproval"]
            doneOrders = booking_data["doneOrders"]

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

            return {"SCC": True, "output": datesList, "printFee": int(printFee)}


        except:
            return {"SCC": True,"output":[],"printFee":int(printFee)}

    @app.route("/api/stripe/createPayment/<listingID>", methods=["POST"])
    def createPaymentStripe(listingID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)

        if user == False:
            return {"SCC": False, "err": "Authentication failed"}, 401

        try:
            listingData = listings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing."}

        pricePerDay = listingData["price"]

        d1 = request.form.get("from")
        d2 = request.form.get("to")
        if d1 == None or d2 == None:
            return {"SCC": False,
                    "err": "'from' and 'to' are not definded, for booking you need to enter those correctly"}
        d1 = d1.split("-")
        d1y = int(d1[0])
        try:
            d1m = int(d1[1])
        except:
            return {"SCC": False, "err": "Date format is invalid"}

        try:
            d1d = int(d1[2])
        except:
            return {"SCC": False, "err": "Date format is invalid"}
        d1 = date(d1y, d1m, d1d)

        d2 = d2.split("-")
        d2y = int(d2[0])
        try:
            d2m = int(d2[1])
        except:
            return {"SCC": False, "err": "Date format is invalid"}
        try:
            d2d = int(d2[2])
        except:
            return {"SCC": False, "err": "Date format is invalid"}
        d2 = date(d2y, d2m, d2d)
        d = d2 - d1
        daysWantToBook = []
        for i in range(d.days + 1):
            day = d1 + timedelta(days=i)
            # print(day)
            day = day.strftime("%Y-%m-%d")
            daysWantToBook.append(day)

        price = pricePerDay * len(daysWantToBook)
        price = price + printFee

        try:
            customerID = user["stripeCustomerID"]
        except:

            customer = stripe.Customer.create()
            users.update_one({"_id":user["_id"]},{"$set":{"stripeCustomerID":customer["id"]}})
            customerID = customer["id"]
        ephemeralKey = stripe.EphemeralKey.create(
            customer=customerID,
            stripe_version='2022-11-15',
        )
        payment_method = request.form.get("payment_method")
        if payment_method != None:
            paymentIntent = stripe.PaymentIntent.create(
                amount= int(price*100),
                currency='usd',
                customer=customerID,
                automatic_payment_methods={
                    'enabled': True,
                },
                payment_method=payment_method
            )
        else:
            paymentIntent = stripe.PaymentIntent.create(
                amount= int(price*100),
                currency='usd',
                customer=customerID,
                automatic_payment_methods={
                    'enabled': True,
                },
            )

        logger_payment = open("payments.log", "a")
        logger_payment.write(f"{time.time()} - {price} - USD\n")
        logger_payment.close()
        paymentID = paymentIntent["id"]

        return jsonify(paymentIntent=paymentIntent.client_secret,
                        ephemeralKey=ephemeralKey.secret,
                        customer=customerID,
                        paymentID=paymentID,
                        publishableKey='pk_test_51LkdT2BwxpdnO2PUdAlSZzzOM4bAIG9abSAc3e3llUFjDh5KhnlBUrdcfouBgUB2b6JE0WyVUMRgCC6gvF2lTdJp00BgLoJQLk')

        
    @app.route("/api/stripe/setupIntent",methods=["POST"])
    def setupIntentStripe():
        email = request.form.get("email")
        phoneNumber = request.form.get("phoneNumber")
        password = request.form.get("password")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"}
        try:
            customerID = user["stripeCustomerID"]
        except:

            customer = stripe.Customer.create()
            users.update_one({"_id":user["_id"]},{"$set":{"stripeCustomerID":customer["id"]}})
            customerID = customer["id"]
        ephemeralKey = stripe.EphemeralKey.create(
            customer=customerID,
            stripe_version='2022-11-15',
        )
        paymentIntent = stripe.SetupIntent.create(
        customer=customerID
        )
        return jsonify(paymentIntent=paymentIntent.client_secret,
                        ephemeralKey=ephemeralKey.secret,
                        customer=customerID,
                        publishableKey='pk_test_51LkdT2BwxpdnO2PUdAlSZzzOM4bAIG9abSAc3e3llUFjDh5KhnlBUrdcfouBgUB2b6JE0WyVUMRgCC6gvF2lTdJp00BgLoJQLk')

    @app.route("/api/stripe/attach", methods=["POST"])
    def attachStripe():
        email = request.form.get("email")
        phoneNumber = request.form.get("phoneNumber")
        password = request.form.get("password")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"}
        try:
            customerID = user["stripeCustomerID"]
        except:

            customer = stripe.Customer.create()
            users.update_one({"_id":user["_id"]},{"$set":{"stripeCustomerID":customer["id"]}})
            customerID = customer["id"]
        paymentMethod = request.form.get("paymentMethod")
        if paymentMethod == None:
            return {"SCC":False,"err":"paymentMethod is not defined"}
        try:
            stripe.PaymentMethod.attach(
            paymentMethod,
            customer=customerID
            )
        except:
            return {"SCC":False,"err":"paymentMethod is not valid"}
        return {"SCC":True}
    @app.route("/api/stripe/detach",methods=["POST"])
    def stripeDetach():
        email = request.form.get("email")
        phoneNumber = request.form.get("phoneNumber")
        password = request.form.get("password")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"}
        paymentMethod= request.form.get("paymentMethod")
        if paymentMethod == None:
            return {"SCC":False,"err":"paymentMethod is not defined"}
        stripe.PaymentMethod.detach(paymentMethod)
        
        return {"SCC":True }




    @app.route("/api/stripe/list_methods",methods=["POST"])
    def list_methods_stripe():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Authentication Failed"}
        
        try:
            customerID = user["stripeCustomerID"]
        except:
            return {"SCC":False,"err":"Customer not found"}
        output = stripe.PaymentMethod.list(
            customer=customerID,
            type="card",
        )

        return output
    @app.route("/api/booking/addProof/<listingID>/<bookingID>", methods=["POST"])
    def addProof(listingID, bookingID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        images = request.form.get("images")
        if images == None:
            return {
                "SCC": False,
                "error": "images can't be undefined.",
                "docs": "Send image filenames to 'images'. For multiple images, put |-| between all image names"
            }

        """
        images: as list of names. |-| between all images
        """
        images = images.split("|-|")

        if user == False:
            return {
                "SCC": False,
                "err": "Authentication failed"
            }
        try:
            listingData = listings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing"}

        bookings = db["Bookings"]
        try:
            bookingData_all = bookings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find booking data"}

        activeOrders = bookingData_all["activeOrders"]

        bookingData = None
        for a in activeOrders:
            if bookingID == a["bookingID"]:
                bookingData = a
                break
        if bookingData == None:
            return {"SCC": False, "err": "Could not want booking with the id you gave."}
        bindex = activeOrders.index(bookingData)
        try:
            bookingData["proofs"]
            return {"SCC": True, "err": "You already sent it"}
        except:
            bookingData["proofs"] = images
        activeOrders.pop(bindex)
        activeOrders.append(bookingData)
        bookings.update_one({"_id": listingID}, {"$set": {"activeOrders": activeOrders}})

        host = listingData["user"]
        customer = bookingData["customer"]
        hostData = users.find({"_id": host})
        customerData = users.find({"_id": customer})
        ordersHost = hostData["orders"]
        ordersCustomer = customerData["orders"]

        hostBookingData = None
        for oh in ordersHost:
            if bookingID == oh["bookingID"]:
                hostBookingData = oh
                break
        if hostBookingData == None:
            return {"SCC": False,
                    "err": "Could not find booking on host's profile. Data may be corrupted or order not accepted by site admin"}

        customerBookingData = None
        for oc in ordersCustomer:
            if bookingID == oh["bookingID"]:
                customerBookingData = oc
                break

        if customerBookingData == None:
            return {"SCC": False, "err": "Could not find customer booking data. Data may be corrupted"}

        customerBookingData["proofs"] = images
        hostBookingData["proofs"] = images
        hindex = ordersHost.index(hostBookingData)
        cindex = ordersCustomer.index(customerBookingData)
        ordersHost.pop(hindex)
        ordersCustomer.pop(cindex)
        ordersHost.append(hostBookingData)
        ordersCustomer.append(customerBookingData)
        users.update_one({"_id": customer}, {"orders": ordersCustomer})
        users.update_one({"_id": host}, {"orders": ordersHost})
        return {"SCC": True, "bookingData": bookingData}
    

    """
    Update for booking confirmation by host
    """
    @app.route("/api/approve/<bookingID>",methods=["POST"])
    def approveBooking(bookingID):
        "NOTE: In order to approve a booking it needs to be in waitingForApproval state"
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Authentication failed"},401
        bookingData = getBookingData(bookingID)
        if bookingData["status"] == "Not found":
            return {"SCC":False,"err":"Could not find booking"},404
        if bookingData["status"] != "waitingForApproval":
            return {"SCC":False,"err":"This listing is not waiting for approval","data":bookingData},401

        listingData = bookingData["listingData"]
        if user["_id"] != listingData["user"]:
            return {"SCC":False,"err":"This listing does not belong to this user."}
        bookings = db["Bookings"]
        try:
            allBookingData = bookings.find({"_id":listingData["_id"]})[0]
        except:
            return {"SCC":False,"err":"database corrupted"},500
        allWaitingForApproval = allBookingData["waitingForApproval"]
        allActive = allBookingData["activeOrders"]
        waindex = -1
        counter = 0
        for w in allWaitingForApproval:
            
            if w["bookingID"] == bookingData["data"]["bookingID"]:
                
                waindex = counter

                bookingData = w
                break
            counter += 1
        if waindex == -1:
            return {"SCC":False,"err":"There is an error with our side"},500
        allWaitingForApproval.pop(waindex)
        allActive.append(bookingData)
        bookings.update_one({"_id":listingData["_id"]},{"$set":{"activeOrders":allActive,"waitingForApproval":allWaitingForApproval}})
        #Send user Successfull message
        customerEmail = users.find({"_id":bookingData["customer"]})[0]["email"]
        msgTitle = "Your booking request is accepted by the host"
        msgBody = f"{user['fullName']} accepted your booking request for {listingData['title']}. You can follow updates on the app."
        Mail.send([customerEmail],"Your booking is approved by host",'<!DOCTYPE html><html><head> <meta charset="utf-8"> <meta http-equiv="x-ua-compatible" content="ie=edge"> <title>'+msgTitle+'</title> <meta name="viewport" content="width=device-width, initial-scale=1"> <style type="text/css"> /** * Google webfonts. Recommended to include the .woff version for cross-client compatibility. */ @media screen { @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 400; src: local(\'Source Sans Pro Regular\'), local(\'SourceSansPro-Regular\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/ODelI1aHBYDBqgeIAH2zlBM0YzuT7MdOe03otPbuUS0.woff) format(\'woff\'); } @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 700; src: local(\'Source Sans Pro Bold\'), local(\'SourceSansPro-Bold\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/toadOcfmlt9b38dHJxOBGFkQc6VGVFSmCnC_l7QZG60.woff) format(\'woff\'); } } /** * Avoid browser level font resizing. * 1. Windows Mobile * 2. iOS / OSX */ body, table, td, a { -ms-text-size-adjust: 100%; /* 1 */ -webkit-text-size-adjust: 100%; /* 2 */ } /** * Remove extra space added to tables and cells in Outlook. */ table, td { mso-table-rspace: 0pt; mso-table-lspace: 0pt; } /** * Better fluid images in Internet Explorer. */ img { -ms-interpolation-mode: bicubic; } /** * Remove blue links for iOS devices. */ a[x-apple-data-detectors] { font-family: inherit !important; font-size: inherit !important; font-weight: inherit !important; line-height: inherit !important; color: inherit !important; text-decoration: none !important; } /** * Fix centering issues in Android 4.4. */ div[style*="margin: 16px 0;"] { margin: 0 !important; } body { width: 100% !important; height: 100% !important; padding: 0 !important; margin: 0 !important; } /** * Collapse table borders to avoid space between cells. */ table { border-collapse: collapse !important; } a { color: #1a82e2; } img { height: auto; line-height: 100%; text-decoration: none; border: 0; outline: none; } </style></head><body style="background-color: #e9ecef;"> <!-- start preheader --> <div class="preheader" style="display: none; max-width: 0; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #fff; opacity: 0;"> Make fast, cheap, easy advertisements with Adflaunt! </div> <!-- end preheader --> <!-- start body --> <table border="0" cellpadding="0" cellspacing="0" width="100%"> <!-- start logo --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="center" valign="top" style="padding: 36px 24px;"> <a href="" target="_blank" style="display: inline-block;"> <img src="https://adflaunt.com/static/adflaunt.png" alt="Logo" border="0" width="48" style="display: block; width: 48px; max-width: 48px; min-width: 48px;"> </a> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end logo --> <!-- start hero --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="left" bgcolor="#ffffff" style="padding: 36px 24px 0; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; border-top: 3px solid #d4dadf;"> <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -1px; line-height: 48px;">'+msgTitle+'</h1> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end hero --> <!-- start copy block --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <!-- start copy --> <tr> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px;"> <p style="margin: 0;">'+msgBody+'</p> </td> </tr> <!-- start button --> <!-- end button --> <!-- start copy --> <tr style="position: relative;"> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px; border-bottom: 3px solid #d4dadf"> <p style="margin: 0;">Adflaunt <svg style="transform: rotate(180deg);" height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> <p style="margin: 0;font-size:10px;position:absolute;right:20px;bottom:25px">Kentel <svg height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> </td> </tr> <!-- end copy --> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end copy block --> <!-- start footer --> <tr> <td align="center" bgcolor="#e9ecef" style="padding: 24px;"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end footer --> </table> <!-- end body --></body></html>')
        

        bookingData["page"] = "bookingPage"

        send_notification(bookingData["customer"],bookingData,f"{user['fullName']} accepted your order","Click for more details")

        del bookingData["page"]
        try:
            hostOrders = user["orders"]
        except:
            hostOrders = []
        hostOrders.append(bookingData)
        users.update_one({"_id":user["_id"]},{"$set":{"orders":hostOrders}})
        return {"SCC":True,"bookingData":bookingData}

    @app.route("/api/decline/<bookingID>",methods=["POST"])
    def declineBooking(bookingID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)

        if user == False:
            return {"SCC":False,"err":"Authentication failed"},403

        bookingData = getBookingData(bookingID)


        if bookingData["status"] == "Not found":
            return {"SCC":False,"err":"Could not find listing"},404

        if bookingData["listingData"]["user"] != user["_id"]:
            return {"SCC":False,"err":"This listing does not belong to you!"},403


        if bookingData["status"] != "waitingForApproval":
            return {"SCC":False,"err":"This listing is not waiting for host approval"},403

        bookings = db["Bookings"]
        try:
            allBookingData = bookings.find_one({"_id":bookingData["listingData"]["_id"]})[0]
        except:
            return {"SCC":False,"err":"Corruption in database"},500
        allWaitingForApproval = allBookingData["waitingForApproval"]
        counter = 0
        waindex = -1
        for w in allWaitingForApproval:

            if w["bookingID"] == bookingData["data"]["bookingID"]:
                
                waindex = counter
                bookingData = w
                break 

            counter += 1
        if waindex == -1:
            return {"SCC":False,"err":"There is an error on our side"},500
        allWaitingForApproval.pop(waindex)
        bookings.update_one({"_id":allBookingData["_id"]},{"$set":{"waitingForApproval":allWaitingForApproval}})

        customer = bookingData["customer"]
        customersProfile = users.find({"_id":customer})[0]
        try:
            ordersCustomer = customersProfile["orders"]
        except:
            ordersCustomer = [] 

        counter = 0
        oindex = -1
        for o in ordersCustomer:
            if o["bookingID"] == bookingData["bookingID"]:
                oindex = counter
                break
            counter +=1
        ordersCustomer.pop(counter)

        users.update_one({"_id":customer},{"$set":{"orders":ordersCustomer}})

        BookingPaymentID = bookingData["paymentID"]
        bookingPrice = bookingData["price"]
        refundData = stripe.Refund.create(
          payment_intent=BookingPaymentID,
        )



        customerEmail = users.find({"_id":bookingData["customer"]})[0]["email"]
        msgTitle = "Your booking request is declined by the host"
        msgBody = f"{user['fullName']} declined your booking request for {listingData['title']}. You can try talk with them on chat."
        Mail.send([customerEmail],"Your booking is approved by host",'<!DOCTYPE html><html><head> <meta charset="utf-8"> <meta http-equiv="x-ua-compatible" content="ie=edge"> <title>'+msgTitle+'</title> <meta name="viewport" content="width=device-width, initial-scale=1"> <style type="text/css"> /** * Google webfonts. Recommended to include the .woff version for cross-client compatibility. */ @media screen { @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 400; src: local(\'Source Sans Pro Regular\'), local(\'SourceSansPro-Regular\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/ODelI1aHBYDBqgeIAH2zlBM0YzuT7MdOe03otPbuUS0.woff) format(\'woff\'); } @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 700; src: local(\'Source Sans Pro Bold\'), local(\'SourceSansPro-Bold\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/toadOcfmlt9b38dHJxOBGFkQc6VGVFSmCnC_l7QZG60.woff) format(\'woff\'); } } /** * Avoid browser level font resizing. * 1. Windows Mobile * 2. iOS / OSX */ body, table, td, a { -ms-text-size-adjust: 100%; /* 1 */ -webkit-text-size-adjust: 100%; /* 2 */ } /** * Remove extra space added to tables and cells in Outlook. */ table, td { mso-table-rspace: 0pt; mso-table-lspace: 0pt; } /** * Better fluid images in Internet Explorer. */ img { -ms-interpolation-mode: bicubic; } /** * Remove blue links for iOS devices. */ a[x-apple-data-detectors] { font-family: inherit !important; font-size: inherit !important; font-weight: inherit !important; line-height: inherit !important; color: inherit !important; text-decoration: none !important; } /** * Fix centering issues in Android 4.4. */ div[style*="margin: 16px 0;"] { margin: 0 !important; } body { width: 100% !important; height: 100% !important; padding: 0 !important; margin: 0 !important; } /** * Collapse table borders to avoid space between cells. */ table { border-collapse: collapse !important; } a { color: #1a82e2; } img { height: auto; line-height: 100%; text-decoration: none; border: 0; outline: none; } </style></head><body style="background-color: #e9ecef;"> <!-- start preheader --> <div class="preheader" style="display: none; max-width: 0; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #fff; opacity: 0;"> Make fast, cheap, easy advertisements with Adflaunt! </div> <!-- end preheader --> <!-- start body --> <table border="0" cellpadding="0" cellspacing="0" width="100%"> <!-- start logo --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="center" valign="top" style="padding: 36px 24px;"> <a href="" target="_blank" style="display: inline-block;"> <img src="https://adflaunt.com/static/adflaunt.png" alt="Logo" border="0" width="48" style="display: block; width: 48px; max-width: 48px; min-width: 48px;"> </a> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end logo --> <!-- start hero --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="left" bgcolor="#ffffff" style="padding: 36px 24px 0; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; border-top: 3px solid #d4dadf;"> <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -1px; line-height: 48px;">'+msgTitle+'</h1> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end hero --> <!-- start copy block --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <!-- start copy --> <tr> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px;"> <p style="margin: 0;">'+msgBody+'</p> </td> </tr> <!-- start button --> <!-- end button --> <!-- start copy --> <tr style="position: relative;"> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px; border-bottom: 3px solid #d4dadf"> <p style="margin: 0;">Adflaunt <svg style="transform: rotate(180deg);" height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> <p style="margin: 0;font-size:10px;position:absolute;right:20px;bottom:25px">Kentel <svg height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> </td> </tr> <!-- end copy --> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end copy block --> <!-- start footer --> <tr> <td align="center" bgcolor="#e9ecef" style="padding: 24px;"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end footer --> </table> <!-- end body --></body></html>')
        

        bookingData["page"] = "bookingPage"

        send_notification(bookingData["customer"],bookingData,f"{user['fullName']} declined your order","Your order is declined by host")
        del bookingData["page"]

        return bookingData
class Scaling:
    @app.route("/static/<filename>/s<scale>")
    def staticScaler(filename, scale):
        try:
            scale = float(scale)
            try:
                img = cv2.imread('static/{}'.format(filename), cv2.IMREAD_UNCHANGED)
            except:
                return {"SCC": False, "err": "file not found or could not be opened by cv2"}

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
            return {"SCC": False, "err": "Scale should be a valid number like: s50 -> it means 50%"}


class Reviews:
    @app.route("/api/reviews/add/<listingID>/<bookingID>", methods=["POST"])
    def addReview(listingID, bookingID):
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email, phoneNumber, password)
        if user == False:
            return {"SCC": False, "err": "Could not login"}

        try:
            listingData = listings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find listing"}

        review = request.form.get("review")
        stars = request.form.et("stars")

        if review == None:
            return {"SCC": False, "err": "Review can't be none"}
        try:
            stars = float(stars)
        except:
            return {"SCC": False, "err": "stars invalid. Should be a float or int."}

        bookings = db["Bookings"]
        try:
            bookingData = bookings.find({"_id": listingID})[0]
        except:
            return {"SCC": False, "err": "Could not find booking data"}
        activeOrders = bookingData["activeOrders"]
        current = None
        for a in activeOrders:
            if bookingID == a["bookingID"]:
                current = bookingID

                break
        if current == None:
            return {"SCC": False, "err": "Could not find requested booking"}

        bookingData["doneOrders"].append(current)
        cindex = bookingData["activeOrders"].index(current)
        bookingData["activeOrders"].pop(cindex)

        bookings.update_one({"_id": listingID}, {"$set": {bookingData}})

        try:
            hostProfile = users.find({"_id": listingData["user"]})[0]
        except:
            return {"SCC": False, "err": "Could not find host's profile, instead made the booking DONE."}
        del user["password"]

        reviewdata = {
            "customer": user,
            "at": time.time(),
            "review": review,
            "star": stars,
            "host": listingData["user"],
            "listing": listingID,
            "revenue": current["price"] * (100 - commisionRate / 100),
        }
        try:
            hostProfile["reviews"]
        except:
            hostProfile["reviews"] = []
        hostProfile["reviews"].append(reviewdata)
        users.update_one({"_id": listingData["user"]}, {"$set": {"reviews": hostProfile["reviews"]}})
        try:
            balance = hostProfile["balance"]
        except:
            balance = 0
        revenue = current["price"] * (100 - commisionRate / 100)
        balance = balance + revenue
        users.update_one({"_id": listingData["user"]}, {"$set": {"balance": balance}})

        try:
            listingData["reviews"]
        except:
            listingData["reviews"] = []

        listingData["reviews"].append(reviewdata)
        listings.update({"_id": listingID}, {"$set": {"reviews": listingData["reviews"]}})

        reviewdata["SCC"] = True

        return reviewdata

class OrdersAndSellerBalance:
    @app.route("/api/getorders/<listingID>")
    def getOrdersWithListingID(listingID):
        bookings = db["Bookings"]
        try:
            bookingData = bookings.find({"_id":listingID})[0]
        except:
            return {"SCC":False,"err":"Could not find listing"}
        
        bookingData["SCC"] = True 

        return bookingData
    @app.route("/api/orders",methods=["POST"])
    def getOrdersUser():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Authentication failed"}
        userListings = getListingsOfUser(user["_id"])
        if len(userListings)>0:
            type_user = "seller"
        else:
            type_user = "buyer"

        asHost = []
        asCustomer = []
        try:
            profileOrders = user["orders"]
            for p in profileOrders:
                if p["customer"] == user["_id"]:
                    p = getBookingData(p["bookingID"])
                    asCustomer.append(p)


        except:
            pass
        usersListings = getListingsOfUser(user["_id"])
        bookings = db["Bookings"]
        for l in usersListings:
            try:
                bookingData = bookings.find({"_id":l["_id"]})[0]
            except:
                continue 
            activeOrders = bookingData["activeOrders"]
            waitingForApproval = bookingData["waitingForApproval"]
            for a in activeOrders:
                a["status"] = "active"
                asHost.append(a)
            for w in waitingForApproval:
                w["status"] = "waitingForApproval"
                asHost.append(w)


        
        returnData = {
            "userData":user,
            "user_type":type_user,
            "asHost":asHost,
            "asCustomer":asCustomer,
            "SCC":True
        }
        return returnData
    @app.route("/api/order/<bookingID>")
    def getOrderWithBookingID(bookingID):
        bookings = db["Bookings"]
        allBookings = bookings.find({})
        for b in allBookings:
            activeOrders = b["activeOrders"]
            waitingForApproval = b["waitingForApproval"]
            doneOrders= b["doneOrders"]
            for a in activeOrders:
                if a["bookingID"] == bookingID:
                    return {"SCC":True,"status":"Active","data":a}
            for w in waitingForApproval:
                if w["bookingID"] == bookingID:
                    return {"SCC":True,"status":"Waiting for Administrator Approval","data":w}
            for d in doneOrders:
                if d["bookingID"] == bookingID:
                    return {"SCC":True,"status":"Completed","data":d}
        return {"SCC":False,"err":"Could not find booking"}   
    @app.route("/api/getBalance",methods=["POST"])
    def getUserBalance():
        email = request.form.get("email")
        password = request.form.get("password")
        phoneNumber = request.form.get("phoneNumber")
        user = login_internal(email,phoneNumber,password)
        if user == False:
            return {"SCC":False,"err":"Authentication Failed"}
        try:
            balance =user["balance"]
        except:
            balance = 0 
        return {"SCC":True,"user":user,"balance":balance}

class UserMapper:
    @app.route("/api/usermap")
    def usermap():
        try:
            username = decrypt(request.cookies.get("username"))
            password = decrypt(request.cookies.get("password"))
            adminData = admin.find({"username": username, "password": password})[0]
        except Exception as e:
            return {"SCC":False,"err":"Login error"}
        output={}
        allUsers = users.find({})
        for a in allUsers:
            try:
                lat = a["lat"]
                long_ = a["long"]
            except:
                lat = a["IPDATA"]["lat"]
                long_ = a["IPDATA"]["lon"]
            email =  a["email"]
            output[email] = [lat,long_]

        return output

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
