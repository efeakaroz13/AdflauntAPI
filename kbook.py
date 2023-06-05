import pymongo
from datetime import date, timedelta


client = pymongo.MongoClient()
db = client['Adflaunt']
bookings = db["Bookings"]

"""
Date format:
YYYY-MM-DD
"""



class Booker:
    def book(listingID,d1,d2,bookingData):
        try:
            listingData= db["Listings"].find({"_id":listingID})[0]
        except:
            raise ValueError("Listing ID not correct")
        try:
            oldBookings = listingData["Bookings"]
        except:
            oldBookings = []
        

        bookings_db = db["Bookings"]





        d1 = d1.split("-")
        d1y = int(d1[0])
        try:
            d1m = int(d1[1])
        except:
            raise ValueError("Date format is invalid")
        
        try:
            d1d = int(d1[2])
        except:
            raise ValueError("Date format is invalid")
        d1 = date(d1y,d1m,d1d)

        d2 = d2.split("-")
        d2y= int(d2[0])
        try:
            d2m = int(d2[1])
        except:
            raise ValueError("Date format for d2 is invalid")
        try:
            d2d=int(d2[2])
        except:
            raise ValueError("Date format for d2 is invalid")
        d2 = date(d2y,d2m,d2d)
        d = d2-d1
        daysWantToBook = []
        for i in range(d.days + 1):
            day = d1 + timedelta(days=i)
            #print(day)
            day = day.strftime("%Y-%m-%d")
            daysWantToBook.append(day)
        for d in daysWantToBook:
            if d in oldBookings:
                return {"SCC":False,"err":"Booking is not available for these days."}
        for d in daysWantToBook:
            oldBookings.append(d)
        db["Listings"].update_one({"_id":listingID},{"$set":{"Bookings":oldBookings}})


        try:
            current_booking_db_data = bookings_db.find({"_id":listingID})[0]
            current_booking_db_data["waitingForApproval"].append(bookingData)
            bookings_db.update_one({'_id':listingID},{"$set":current_booking_db_data})
        except:
            current_booking_db_data = {
                "_id":listingID,
                "activeOrders":[],
                "waitingForApproval":[],
                "doneOrders":[]
            }

            current_booking_db_data["waitingForApproval"].append(bookingData)
            bookings_db.insert_one(current_booking_db_data)
        current_booking_db_data["SCC"] = True
        current_booking_db_data["message"] = "Placed the order waiting for approval by admin."
        return current_booking_db_data




