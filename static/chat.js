const sio = io("wss://adflaunt.com");
function g(id_){
	return document.getElementById(id_).value
}
function m(id_,text){
	document.getElementById(id_).innerHTML =document.getElementById(id_).innerHTML+"<p>"+text+"</p>"; 
}

sio.on('connect',() => {
//connection code
    console.log('connected');
});

sio.on('disconnect',() => {
//disconnection code
console.log('disconnected')
})
userData = "";
function joinChat(){
	sio.emit('join',{"email":g("email"),"password":g("password"),"phoneNumber":g("phoneNumber"),"ChatID":g("ChatID")},(data)=>{
		userData = data;
		console.log(data)

		m("output","Joined to "+data["chatID"]);
	})
}
function sendMessage(){
	message = g("text");
	msgData = userData
	msgData["content"] = message;
	msgData["image"] = "";
	sio.emit('send_msg',userData,(data)=>{
		console.log(data)
	})
}

sio.on('send_msg',(data) =>{
	m("output",JSON.stringify(data))
})