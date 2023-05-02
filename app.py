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

data = json.loads(open("data.json", "r").read())
app = Flask(__name__)
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png", "heic"]
alphabet = ["a","b","c","d", "e", "f", "g", "h", "i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]



def loginInternal(email,password):
    try:
        if data["short_auth"][email] != password:
            return False,{"SCC":False,"err":"Password is not correct."}

    except:
        return False,{
            "SCC":False,
            "err":"This user does not exist."
        }
    
    allkeys = list(data["Users"].keys())
    for a in allkeys:
        d = data["Users"][a]
        if d["email"] == email:
            return True,d
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
    @app.route("/login",methods=["POST"])
    def login():
        email = request.form.get("email")
        password = request.form.get("password")
        data=json.loads(open("data.json","r").read())
        try:
            if data["short_auth"][email] != password:
                return {"SCC":False,"err":"Password is not correct."},401

        except Exception as e:

            return {
                "SCC":False,
                "err":"This user does not exist.",
                "e":str(e)
            },404
        
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
        allUsers = data["Users"].keys()

        for u in allUsers:
            cdata = data["Users"][u]
            email_c = cdata["email"]
            if email_c == email:
                return abort(409)
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

class Listing:


    @app.route("/search")
    def search():
        data = json.loads(open("data.json","r").read())

        q = request.args.get("q")
        if q == None or q == "":
            try:
                return data["Listings"]
            except:
                return {}
        results = []
        try:
             data["Listings"]
        except:
            return {}
        for a in list(data["Listings"].keys()):
            d_c = data["Listings"][a]
            try:
                title = d_c["title"]
            except:
                title = ""
            try:
                description = d_c["description"]
            except:
                description = ""
            if (str(q).lower().strip() in title) or (str(q).lower().strip() in description):
                results.append(d_c)
        return {"output":results}
    






    @app.route("/api/listing",methods=["POST","GET","DELETE"])
    def get_and_create_listing_user():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            scc,user = loginInternal(email,password)
            if scc == False:
                return {"SCC":False,"err":"Email or password is not correct or missing"}
            
            title = request.form.get("title")
            price = request.form.get("price")
            location = request.form.get("location")
            type_ = request.form.get("type")
            revisions = request.form.get("revisions")
            digital = request.form.get("digital")
            printsqfeet = request.form.get("sqfeet")
            printsqfootage = request.form.get("sqfootage")
            category = request.form.get("category")
            population  = request.form.get("population")
            discountAvailable = request.form.get("discountAvailable")
            installationDate = request.form.get("installationDate")
            removalDate =request.form.get("removalDate")
            tags = request.form.get("tags")
            if tags != None:
                tags = tags.split(",")
            extras = request.form.get("extras")
            requirements = request.form.get("requirements")
            description = request.form.get("description")
            bookingNote = request.form.get("bookingNote")
            bookingOffset = request.form.get("bookingOffset")
            bookingWindow = request.form.get("bookingWindow")
            maxBookingDuration = request.form.get("maxBookingDuration")
            minBookingDuration = request.form.get("minBookingDuration")
            minGuestsPerBooking = request.form.get("minGuestsPerBooking")
            maxGuestsPerBooking = request.form.get("maxGuestsPerBooking")
            manuallyAcceptNewBookings = request.form.get("manuallyAcceptNewBookings")
            agreeConditions = request.form.get("agreeToConditions")
            try:
                file = request.files['image']
            except:
                file = False 
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
                    
                    file = filename+"."+ext

                except Exception as e:
                    file =False
            else:
                file =False 
            
            PID = IDCREATOR_internal(12)   
            data_s = {
                "title":title,
                "PID":PID,
                "price":price,
                "location":location,
                "type":type_,
                "revisions":revisions,
                "digital":digital,
                "sqfeet":printsqfeet,
                "sqfootage":printsqfootage,
                "category":category,
                "population":population,
                "discountAvailable":discountAvailable,
                "installationDate":installationDate,
                "removalDate":removalDate,
                "tags":tags,
                "image":file,
                "extras":extras,
                "requirements":requirements,
                "description":description,
                "bookingNote":bookingNote,
                "bookingOffset":bookingOffset,
                "bookingWindow":bookingWindow,
                "maxBookingDuration":maxBookingDuration,
                "minBookingDuration":minBookingDuration,
                "minGuestsPerBooking":minGuestsPerBooking,
                "maxGuestsPerBooking":maxGuestsPerBooking,
                "manuallyAcceptNewBookings":manuallyAcceptNewBookings,
                "agreeToConditions":agreeConditions,
                "email":email,
                "machineTime":time.time(),
                "user":user

            }
            try:
                data["Listings"]
            except:
                data["Listings"] = {}
            
            data["Listings"][PID] = data_s

            open("data.json","w").write(json.dumps(data,indent=4))
            return data_s
        
        if request.method == "GET":
            PID = request.args.get("id")
            try:
                return data["Listings"][PID]
            except:
                return {"SCC":False,"err":"Could not find listing"}

        
        if request.method == "DELETE":
            email = request.form.get("email")
            password = request.form.get("password")
            scc,user = loginInternal(email,password)
            if scc == False:
                return {"SCC":False,"err":"email and password is not correct"}
            PID = request.form.get("id")
            try:
                if data["Listings"][PID]["email"] == email:
                    del data["Listings"][PID]

                else:
                    return {"SCC":False,"err":"This element doesn't belong to this email. "}
                
                open("data.json","w").write(json.dumps(data,indent=4))
                return {"SCC":True}
            except:
                return {"SCC":False,"err":"Data does not exist"}



        """
            Needed data for this part:
            Title, --done
            thumbnail,
            price,--done
            location,--done
            category,--done
            revisions(optional), --done
            digital(checkbox),--done
            print(optional)->sqfeet and footage,--done
            Type,--done
            Population,--done
             Discount available,--done
            installation date,--done
            removal date,--done
            tags,--done
            extras(title,price,per x),--done
            Requirements:array,--done
            Description,--done
            booking note,--done
            booking offset,--done
            booking window,--done
            minimum booking duration,--done
            maximum booking duration,--done
            minimum guests per booking,--done
            maximum guests per booking,--done
            Manually accept new bookings,--done
            Agree to conditions.

        """
                

class Reviews:
    @app.route("/add_review/<listingID>",methods=["POST"])
    def add_review_with_listing_id(listingID):
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            scc,user = loginInternal(email,password)
            if scc == False:
                return {"SCC":False,"err":"check email and password"}
            date = request.form.get("date")
            review = request.form.get("review")
            try:
                stars = float(request.form.get("stars"))
            except:
                return {"SCC":False,"err":"Specify stars as float"}
            
            c_data=  {
                "review":review,
                "mtime":time.time(),
                "stars":stars,
                "date":date,
                "user":user
            }
            try:
                data["Listing"][listingID]["Reviews"]
            except:
                data["Listing"][listingID]["Reviews"] = {}
            reviewID = IDCREATOR_internal(12)
            
            data["Listing"][listingID]["Reviews"][reviewID] = c_data 

            #Add review to the listing
            try:
                data["Users"][data["Listing"][listingID]["user"]["UID"]]["Reviews"]
            except:
                data["Users"][data["Listing"][listingID]["user"]["UID"]]["Reviews"] = {}

            #Add review to host of the post.
            data["Users"][data["Listing"][listingID]["user"]["UID"]]["Reviews"][reviewID] = c_data

class OLD:
    @app.route("/static/scaler")
    def scaler():
        filename = request.args.get("filename")
        if filename == None:
            return {"SCC":False,"err":"Filename required"}
        try:
            img = cv2.imread('static/{}'.format(filename), cv2.IMREAD_UNCHANGED)
        except:
            return {"SCC":False,"err":"file not found or could not be opened by cv2"}

        try:
            scale_percent = int(request.args.get("scalePer"))
        except:
            scale_percent = 60
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        retval, buffer = cv2.imencode('.png', resized)
        response = make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response



if __name__ == "__main__":
    app.run(debug=True)
