"""
Author:Efe Akaröz @ Kentel
22june 2023
"""

 
import pymongo
import random
import json
import time
import datetime
import smtp
from stripe_auth import stripeSecret,brevoSecret,firebaseKey

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
    def generate(msgTitle,msgBody):
        return '<!DOCTYPE html><html><head> <meta charset="utf-8"> <meta http-equiv="x-ua-compatible" content="ie=edge"> <title>'+msgTitle+'</title> <meta name="viewport" content="width=device-width, initial-scale=1"> <style type="text/css"> /** * Google webfonts. Recommended to include the .woff version for cross-client compatibility. */ @media screen { @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 400; src: local(\'Source Sans Pro Regular\'), local(\'SourceSansPro-Regular\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/ODelI1aHBYDBqgeIAH2zlBM0YzuT7MdOe03otPbuUS0.woff) format(\'woff\'); } @font-face { font-family: \'Source Sans Pro\'; font-style: normal; font-weight: 700; src: local(\'Source Sans Pro Bold\'), local(\'SourceSansPro-Bold\'), url(https://fonts.gstatic.com/s/sourcesanspro/v10/toadOcfmlt9b38dHJxOBGFkQc6VGVFSmCnC_l7QZG60.woff) format(\'woff\'); } } /** * Avoid browser level font resizing. * 1. Windows Mobile * 2. iOS / OSX */ body, table, td, a { -ms-text-size-adjust: 100%; /* 1 */ -webkit-text-size-adjust: 100%; /* 2 */ } /** * Remove extra space added to tables and cells in Outlook. */ table, td { mso-table-rspace: 0pt; mso-table-lspace: 0pt; } /** * Better fluid images in Internet Explorer. */ img { -ms-interpolation-mode: bicubic; } /** * Remove blue links for iOS devices. */ a[x-apple-data-detectors] { font-family: inherit !important; font-size: inherit !important; font-weight: inherit !important; line-height: inherit !important; color: inherit !important; text-decoration: none !important; } /** * Fix centering issues in Android 4.4. */ div[style*="margin: 16px 0;"] { margin: 0 !important; } body { width: 100% !important; height: 100% !important; padding: 0 !important; margin: 0 !important; } /** * Collapse table borders to avoid space between cells. */ table { border-collapse: collapse !important; } a { color: #1a82e2; } img { height: auto; line-height: 100%; text-decoration: none; border: 0; outline: none; } </style></head><body style="background-color: #e9ecef;"> <!-- start preheader --> <div class="preheader" style="display: none; max-width: 0; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #fff; opacity: 0;"> Make fast, cheap, easy advertisements with Adflaunt! </div> <!-- end preheader --> <!-- start body --> <table border="0" cellpadding="0" cellspacing="0" width="100%"> <!-- start logo --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="center" valign="top" style="padding: 36px 24px;"> <a href="" target="_blank" style="display: inline-block;"> <img src="https://adflaunt.com/static/adflaunt.png" alt="Logo" border="0" width="48" style="display: block; width: 48px; max-width: 48px; min-width: 48px;"> </a> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end logo --> <!-- start hero --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <tr> <td align="left" bgcolor="#ffffff" style="padding: 36px 24px 0; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; border-top: 3px solid #d4dadf;"> <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -1px; line-height: 48px;">'+msgTitle+'</h1> </td> </tr> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end hero --> <!-- start copy block --> <tr> <td align="center" bgcolor="#e9ecef"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> <!-- start copy --> <tr> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px;"> <p style="margin: 0;">'+msgBody+'</p> </td> </tr> <!-- start button --> <!-- end button --> <!-- start copy --> <tr style="position: relative;"> <td align="left" bgcolor="#ffffff" style="padding: 24px; font-family: \'Source Sans Pro\', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 24px; border-bottom: 3px solid #d4dadf"> <p style="margin: 0;">Adflaunt <svg style="transform: rotate(180deg);" height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> <p style="margin: 0;font-size:10px;position:absolute;right:20px;bottom:25px">Kentel <svg height="10" preserveAspectRatio="xMidYMid" viewBox="0 0 256 256" width="10" xmlns="http://www.w3.org/2000/svg"><path d="m128 256c70.692448 0 128-57.307552 128-128s-57.307552-128-128-128-128 57.307552-128 128 57.307552 128 128 128zm0-26.122449c-56.2654178 0-101.877551-45.612133-101.877551-101.877551 0-56.2654178 45.6121332-101.877551 101.877551-101.877551 56.265418 0 101.877551 45.6121332 101.877551 101.877551 0 56.265418-45.612133 101.877551-101.877551 101.877551zm-1.044898-173.7142857c-33.9591836 0-62.432653 23.7714286-69.7469387 55.6408167h34.2204081c6.2693878-13.5836738 19.8530616-22.9877555 35.5265306-22.9877555 21.681633 0 39.183674 17.5020405 39.183674 39.1836735s-17.502041 39.183673-39.183674 39.183673c-15.673469 0-29.2571428-9.404081-35.5265306-22.72653h-34.2204081c7.3142857 31.608163 35.7877551 55.379592 69.7469387 55.379592 39.706122 0 71.836735-32.130613 71.836735-71.836735 0-39.7061224-32.130613-71.8367347-71.836735-71.8367347z"/></svg></p> </td> </tr> <!-- end copy --> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end copy block --> <!-- start footer --> <tr> <td align="center" bgcolor="#e9ecef" style="padding: 24px;"> <!--[if (gte mso 9)|(IE)]> <table align="center" border="0" cellpadding="0" cellspacing="0" width="600"> <tr> <td align="center" valign="top" width="600"> <![endif]--> <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;"> </table> <!--[if (gte mso 9)|(IE)]> </td> </tr> </table> <![endif]--> </td> </tr> <!-- end footer --> </table> <!-- end body --></body></html>'


sampleReviews = ["Excellent service!","What a great service!","Good deal!","Fair Price!"]
commisionRate = 30
client = pymongo.MongoClient()
db = client["Adflaunt"]
users = db["Users"]
listings = db["Listings"]
bookings = db["Bookings"]

def doit():
    allUsers = users.find({})
    for user in allUsers:
            allUsersListings= listings.find({"user":user["_id"]})
            for listingData in allUsersListings:
                listingID = listingData["_id"]
                allBookings = []
                
                try:
                    for b in bookings.find({"_id":listingID})[0]["activeOrders"]:
                        lastDay = b["daysWantToBook"][-1]
                        year = int(lastDay.split("-")[0])
                        month = int(lastDay.split("-")[1])
                        day = int(lastDay.split("-")[2])
                        lastTimestamp = datetime.datetime(year,month,day,0,0).timestamp()
                        if lastTimestamp+259200<time.time():
                            allBookings.append(b["bookingID"])
                except:
                    continue
                for bookingID in allBookings:


            
                    review = random.choice(sampleReviews)
                    stars = 5.0

                    


                    try:
                        bookingData = bookings.find({"_id": listingID})[0]
                    except:
                        print({"SCC": False, "err": "Could not find booking data"})
                        continue
                    user = users.find({"_id":bookingData["customer"]})
                    activeOrders = bookingData["activeOrders"]
                    current = None
                    counter = 0
                    for a in activeOrders:
                        if bookingID == a["bookingID"]:
                            current = a
                            cindex=counter

                            break
                        counter += 1
                    if current == None:
                        print({"SCC": False, "err": "Could not find requested booking"})
                        continue

                    bookingData["doneOrders"].append(current)
                    
                    bookingData["activeOrders"].pop(cindex)

                    bookings.update_one({"_id": listingID}, {"$set": bookingData})

                    try:
                        hostProfile = users.find({"_id": listingData["user"]})[0]
                    except:
                        print({"SCC": False, "err": "Could not find host's profile, instead made the booking DONE."})
                        continue
                    del user["password"]

                    reviewdata = {
                        "customer": user,
                        "at": time.time(),
                        "review": review,
                        "star": stars,
                        "host": listingData["user"],
                        "listing": listingID,
                        "revenue": current["price"] * ((100 - commisionRate) / 100),
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
                    revenue = current["price"] * ((100 - commisionRate) / 100)
                    balance = balance + revenue
                    users.update_one({"_id": listingData["user"]}, {"$set": {"balance": balance}})

                    try:
                        listingData["reviews"]
                    except:
                        listingData["reviews"] = []

                    listingData["reviews"].append(reviewdata)
                    listings.update_one({"_id": listingID}, {"$set": {"reviews": listingData["reviews"]}})

                    reviewdata["SCC"] = True
                    html = Mail.generate(f"Your order from {user['fullName']} marked as complete",f"{user['fullName']} {stars}<br>'{review}'<br>For your listing {listingData['title']}<br>We automatically give this rating because of user's 3 days delay.")
                    Mail.send([hostProfile["email"]],f"Your order from {user['fullName']} marked as complete",html)

                    html = Mail.generate(f"Your order marked as complete because of 3 days of delay.",f"Your order for listing {listingData['title']} has marked as complete")
                    Mail.send([user["email"]],f"Your order marked as complete because of 3 days of delay.",html)
                    print(json.dumps(reviewdata,indent=4))
doit()

