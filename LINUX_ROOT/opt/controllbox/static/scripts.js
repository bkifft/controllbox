function fetchstate(){
 $("#relay_state").load('/SW1/STATE','');
 $("#mk312_state").load('/MK312/STATE','');

// setTimeout(fetchstate,1000);
}

$(document).ready(function(){
 setTimeout(fetchstate,1000);
});