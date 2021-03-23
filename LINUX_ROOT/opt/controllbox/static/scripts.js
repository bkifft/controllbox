function fetchstate(){
 $("#relay_state").load('/SW1/STATE','');
  setTimeout(fetchstate,1000);
}

$(document).ready(function(){
 setTimeout(fetchstate,1000);
});