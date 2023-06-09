passwordState = 0;
//state 0 is hidden
password_save = ""
currentURL = window.location.href

function g(elementId){
	return document.getElementById(elementId).innerHTML
}
if(currentURL.includes("admin/user/")){
	countryCode = document.getElementById("cc").innerHTML
	password_save = g("password")
	document.getElementById(countryCode).style.fill="red";
	showHidePassword()
	document.getElementById("password").style.display="";

}
if(currentURL.includes("admin/map")){
	data= JSON.parse(document.getElementById("data").innerHTML);
	allKeys = Object.keys(data)
	valueData = []
	allKeys.forEach(function(key){
		var value = data[key].length;
		valueData.push(value);
	})
	console.log(valueData)
	max = Math.max(valueData);
	for (i=0;i<valueData.length;i++) {
		var current = valueData[i];
		red = (current/max)*255;
		country = allKeys[i];
		green = Math.round(red/2);
		blue=green
		document.getElementById(country).style.fill="rgb("+red+","+green+","+blue+")"
	};
}

function showHidePassword(){
	if(passwordState==0){

		document.getElementById("showhide").innerHTML = "Show";

		password = g("password")
		newPassword = "";
		for(i=0;password.length>i;i++){
			newPassword = newPassword+"*";

		}
		document.getElementById("password").innerHTML = newPassword;
		passwordState=1;
	}else{
		passwordState = 0;
		document.getElementById("password").innerHTML = password_save;
		document.getElementById("showhide").innerHTML = "Hide";
	}

}

async function acceptBooking(listingID,bookingIndex){
	const response = await fetch('admin/api/acceptBooking/'+listingID+'/'+bookingIndex);
	data = response.json();
	if(data.SCC != true){
		alert("An error occured while accepting order.")
	}else{
		alert("Order Successfully accepted.");
		document.getElementById(listingID+bookingIndex).style.display="none";


	}
}


async function denyBooking(listingID,bookingIndex){
	const response = await fetch('admin/api/denyBooking/'+listingID+'/'+bookingIndex);
	data = response.json();
	if(data.SCC != true){
		alert("An error occured while denying order.");
	}else{
		alert("Order Successfully Denied.");
		document.getElementById(listingID+bookingIndex).style.display="none";
		

	}
}