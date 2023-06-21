/*
Kentel Development 
JUNE 2023
All rights reserved
Author:Efe Akaröz
*/

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
	const map = L.map('map').setView([0, 0], 2);

	const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 19,
		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">Kentel Development</a>'
	}).addTo(map);

	$.getJSON("/api/usermap",function(data){
		allKeys = Object.keys(data)
		allKeys.forEach(function(key){
			var value = data[key];

			var marker = L.marker(value);    // Creating a Marker
         

	        marker.bindPopup(key);
	        marker.addTo(map); 
		})
	})
}
if (currentURL.includes("admin/listings")) {
	data= JSON.parse(document.getElementById("data").innerHTML)["output"];
	pageNumberMax = Math.floor(data.length/20)+1
	document.getElementById("pages").innerHTML = "";
	for (var i=0; i<pageNumberMax;i++) {
		ireal = i+1
		document.getElementById("pages").innerHTML = document.getElementById("pages").innerHTML+'<a id="page'+ireal+'" onclick="loadpage(this)">'+ireal+'</a>';
		
	};
	function loadpage(element){
		pageNumber =parseInt( element.innerHTML);
		renderData = data.slice(0,pageNumber*20).slice(-20);
		document.getElementById("results").innerHTML = ""
		for (var i = renderData.length - 1; i >= 0; i--) {
			current= renderData[i];
			document.getElementById("results").innerHTML=  document.getElementById("results").innerHTML +"<div class='card' style='width:500px'>"+"<img class='card-img-top' src='/static/"+current.images[0]+"/s25' >"+"<div class='card-body'>"+"<h5 class='card-title'>"+current.title+"</h5><p class='card-text'>"+"<strong>Location:</strong>"+current.city+","+current.state+" - "+current.country+"<br>"+"<strong>Price:</strong>"+current.price+"<br>"+"<strong>Surface area:</strong>"+current.sqfeet+"<br>"+"</p>"+"</div>"+"</div><br><br>"

		};

	}
	loadpage(document.getElementById("page1"))
	
};
if (currentURL.includes("admin/serverLoad")) {
	data = JSON.parse(document.getElementById("data").innerHTML);
	timeStamps = [];
	CPUload = [];
	RAMload = [];
	DISKload = [];
	const CPUcanvas = document.getElementById('CPU');
	const RAMcanvas = document.getElementById('RAM');
	const DISKcanvas = document.getElementById('DISK');



	for (var i = data.length - 1; i >= 0; i--) {
		var current = data[i];
		d = new Date(current["time"]*1000)
		timeStamps.push(d.toLocaleString());
		CPUload.push(current["CPU"]);
		RAMload.push(current["RAM"]);
		DISKload.push(current["DISK"]);


	};
	CPUload =CPUload.reverse(); 
	RAMload =RAMload.reverse(); 
	DISKload =DISKload.reverse(); 
	const dataCPU = {
	  labels: timeStamps,
	  datasets: [{
	    label: 'CPU Load',
	    data: CPUload,
	    fill: false,
	    borderColor: 'rgb(75, 192, 192)',
	    tension: 0.1
	  }]
	};
	const configCPU = {
	  type: 'line',
	  data: dataCPU,
	};
	new Chart(CPUcanvas,configCPU);


	const dataRAM = {
	  labels: timeStamps,
	  datasets: [{
	    label: 'RAM Load',
	    data: RAMload,
	    fill: false,
	    borderColor: 'rgb(77, 235, 96)',
	    tension: 0.1
	  }]
	};
	const configRAM= {
	  type: 'line',
	  data: dataRAM,
	};
	new Chart(RAMcanvas,configRAM);


	const dataDISK = {
	  labels: timeStamps,
	  datasets: [{
	    label: 'DISK Load',
	    data: DISKload,
	    fill: false,
	    borderColor: 'rgb(232, 96, 86)',
	    tension: 0.1
	  }]
	};
	const configDISK= {
	  type: 'line',
	  data: dataDISK,
	};
	new Chart(RAMcanvas,configDISK);
};






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