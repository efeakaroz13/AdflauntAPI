import requests
import json 
import time 
import os
import random 


baseURL =  "https://adflaunt.com"
email = "efeakaroz13@gmail.com"
password = "12345"
phoneNumber = "905465941944"
profileImage = "profile.png"
class Users:
	def register():
		timeStart = time.time()
		uploader = json.loads(requests.post(baseURL+"/api/upload",files={"file":open(profileImage,"rb")}).content)
		ipData = requests.get("http://ip-api.com/json").text
		data = {
			"email":email,
			"password":password,
			"phoneNumber":phoneNumber,
			"IPDATA":ipData,
			"fullName":"Efe Akaröz",
			"profileImage":uploader["file"]
		}
		page = json.loads(requests.post(baseURL+"/api/register",data=data).content)
		timeEnd = time.time()
		print((timeEnd-timeStart)*1000)
		print(page)
	def login():
		timeStart = time.time()

		page = json.loads(requests.post(baseURL+"/api/login",data={"email":email,"phoneNumber":phoneNumber,"password":password}).content)
		timeEnd = time.time()
		print((timeEnd-timeStart)*1000)
		print(json.dumps(page,indent=4))
	def idVerifier():
		uploader = json.loads(requests.post(baseURL+"/api/upload",files={"file":open("listingSamplePNG/id.jpg","rb")}).content)
		data= {
			"email":email,
			"password":password,
			"phoneNumber":phoneNumber,
			"fullName":"Efe Akaröz",
			"dateOfBirth":"13/06/2007",
			"photoOfId":uploader["file"]
		}
		page = json.loads(requests.post(baseURL+"/api/verify/ID",data=data).content)
		print(json.dumps(page))

class Listings:
	def createListing():
		data=  {
			"email":email,
			"password":password,
			"phoneNumber":phoneNumber
		}
		adType = random.choice(["Indoor","Outdoor","Vehicle"])
		imagesCurrent = os.listdir(f"listingSamplePNG/{adType}")
		selectedImage = random.choice(imagesCurrent)
		print(f"listingSamplePNG/{adType}/"+selectedImage)
		uploader = json.loads(requests.post(baseURL+"/api/upload",files={"file":open(f"listingSamplePNG/{adType}/"+selectedImage,"rb")}).content)
		print(uploader)
		data["country"] = "United States"#string
		data["state"] = "New York"#string
		data["city"] = "City"
		data["lat"] = 40.622013#number, float
		data["long"] = -73.960045 #number, float
		data["images"] = uploader["file"]
		data["title"] =  f"Test Listing {random.randint(1,300)}"
		data["price"] = random.randint(5,120)#number integer
		if adType == "Indoor":
			data["typeOfAd"] = 1#Number 0-1-2
		if adType == "Outdoor":
			data["typeOfAd"] = 0#Number 0-1-2
		if adType == "Vehicle":
			data["typeOfAd"] = 2#Number 0-1-2
		"""
		0-outdoor
		1-indoor
		2-vehicle
		"""
		data["location"] = "East Midwood Jewish Center"
		data["revision_limit"] = 3
		data["digital"] =  "false"
		data["sqfeet"] =100
		data["square_footage"]=100
		data["type"] =random.randint(1,6)# number - between 1-6
		data["check_in"]="13-06-2023"#Date
		data["check_out"]= "13-06-2024"#Date
		data["population"]=100000 #number
		data["discountAvailable"]=2# Number between 1-4
		"""
		Discount available:
		yes
		no
		long-term
		partial
		"""

		data["extras"] ="[]"#fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
		data["requirements"] ="{}"#fully custom JSON array IF EMPTY, JUST SEND A EMPTY ARRAY
		data["description"] ="description test"#STR
		data["bookingNote"] ="This is a booking note"#STR OPT

		"Set how many days are required prior to the booking date"

		"Set how many days in advance a booking can be made."
		data["minimumBookingDuration"] ="1"
		data["BookingImportURL"] ="https://adflaunt.com"
		page = requests.post(baseURL+"/api/create/listing",data=data)
		print(json.dumps(json.loads(page.content),indent=4))




if __name__ == "__main__":
	for i in range(5):
		Listings.createListing()
