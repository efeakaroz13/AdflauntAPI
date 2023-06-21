import pymongo
import random
import json
import time
import datetime

sampleReviews = ["Excellent service!","What a great service!","Good deal!","Fair Price!"]

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
                for b in bookings.find({"_id":listingID})[0]["activeOrders"]:
                    lastDay = b["daysWantToBook"][-1]
                    year = int(lastDay.split("-")[0])
                    month = int(lastDay.split("-")[1])
                    day = int(lastDay.split("-")[2])
                    lastTimestamp = datetime.datetime(year,month,day,0,0).timestamp()
                    if lastTimestamp+259200<time.time():
                        allBookings.append(b["bookingID"])
                for bookingID in allBookings:


            
                    review = random.choice(sampleReviews)
                    stars = 5.0

                    


                    try:
                        bookingData = bookings.find({"_id": listingID})[0]
                    except:
                        print({"SCC": False, "err": "Could not find booking data"})
                        continue
                    activeOrders = bookingData["activeOrders"]
                    current = None
                    counter = 0
                    for a in activeOrders:
                        if bookingID == a["bookingID"]:
                            current = bookingID
                            cindex=counter
                            
                            break
                        counter += 1
                    if current == None:
                        print({"SCC": False, "err": "Could not find requested booking"})
                        continue

                    bookingData["doneOrders"].append(current)
                    
                    bookingData["activeOrders"].pop(cindex)

                    bookings.update_one({"_id": listingID}, {"$set": {bookingData}})

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
                    print(json.dumps(reviewdata,indent=4))
doit()

