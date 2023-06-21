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
	$.getJSON("/api/usermap",function(data){
		allKeys = Object.keys(data)
		allKeys.forEach(function(key){
			var value = data[key];
			console.log(key+","+value)
		})
	})
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
	const response = await fetch('api/acceptBooking/'+listingID+'/'+bookingIndex);
	data = await response.json();
	if(data["SCC"] != true){
		alert("An error occured while accepting order.")
	}else{
		alert("Order Successfully accepted.");
		document.getElementById(listingID+bookingIndex).style.display="none";
		window.location.reload()


	}
}


async function denyBooking(listingID,bookingIndex){
	const response = await fetch('api/denyBooking/'+listingID+'/'+bookingIndex);
	data =  await response.json();
	if(data.SCC != true){
		alert("An error occured while denying order.");
	}else{
		alert("Order Successfully Denied.");
		document.getElementById(listingID+bookingIndex).style.display="none";
		window.location.reload()

	}
}