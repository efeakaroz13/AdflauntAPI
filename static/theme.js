/*
Author:Efe Akaröz
AT: 4th of June 2023
note: Feel free to use this code.
*/

function changeIcon(filename){
	var link = document.querySelector("link[rel~='icon']");
	if (!link) {
	    link = document.createElement('link');
	    link.rel = 'icon';
	    document.head.appendChild(link);
	}
	link.href = filename;
}

if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    changeIcon('/static/logoWhite256.png'); 
}else{
	changeIcon('/static/logo256.png');
}



window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
    const newColorScheme = event.matches ? "dark" : "light";
    if (newColorScheme == "dark") {
    	changeIcon('/static/logoWhite256.png');

    }else{
    	changeIcon('/static/logo256.png');
    };
});
function getFlagEmoji(countryCode) {
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char =>  127397 + char.charCodeAt());
  return String.fromCodePoint(...codePoints);
}


function changeCodesToCountries(){
	allFlagClasses = document.getElementsByClassName("flag")
	for (a in allFlagClasses){
		current = allFlagClasses[a];
		current.innerHTML = getFlagEmoji(current.innerHTML)
	}
}
changeCodesToCountries()
