import requests
import json 
from colorama import Fore
import time
import socket


ipdata = json.loads(requests.get("http://ip-api.com/json").content)
print("CONNECTED AS ",Fore.BLUE,ipdata["query"],Fore.RESET," - Have fun testing!")
def register(email,password,phoneNumber):
	start = time.time()
	page = requests.post("http://127.0.0.1:5000/api/register",
		data={"email":email,"password":password,"phoneNumber":phoneNumber,"IPDATA":json.dumps(ipdata)}
	)
	output=json.loads(page.content)
	#print(json.dumps(output,indent=4))
	try:

		userID = output["_id"]
	except:
		print(Fore.RED,output["err"],Fore.RESET)
		return 0
	end = time.time()
	timeElapsed = end-start
	print(Fore.GREEN,"USER CREATED",Fore.RESET," ",userID)
	print(f"IN {timeElapsed*1000} ms")

#register("efeakaroz13@proton.me","12345","905465941945")
#User t1madk0idr2jujvhjbnh3l6y3oguq
#reciever n2s5qhvd6f4juxq8rpdnu2g6weka4ip6

def createChat(email,password,phoneNumber,reciever):
	sendData = {
		"email":email,
		"password":password,
		"phoneNumber":phoneNumber,
		"reciever":reciever
	}
	page = requests.post("http://127.0.0.1:5000/api/create/chat",data=sendData)
	output =json.loads(page.content)
	print(json.dumps(output,indent=4))

#createChat("efeakaroz13@proton.me","12345","905465941945","n2s5qhvd6f4juxq8rpdnu2g6weka4ip6")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect(("127.0.0.1",5000))




