function convertKitTagSubscriber(subscriber_id,tag,post_id){if(convertkit.debug){console.log('convertKitTagSubscriber');console.log(convertkit);console.log(subscriber_id);console.log(tag);console.log(post_id)}
fetch(convertkit.ajaxurl,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded',},body:new URLSearchParams({action:'convertkit_tag_subscriber',convertkit_nonce:convertkit.nonce,subscriber_id:subscriber_id,tag:tag,post_id:post_id,})}).then(function(response){if(convertkit.debug){console.log(response)}
return response.json()}).then(function(result){if(convertkit.debug){console.log(result)}
convertKitRemoveSubscriberIDFromURL(window.location.href)}).catch(function(error){if(convertkit.debug){console.error(error)}
convertKitRemoveSubscriberIDFromURL(window.location.href)})}
function convertStoreSubscriberIDInCookie(subscriber_id){if(convertkit.debug){console.log('convertStoreSubscriberIDInCookie');console.log(subscriber_id)}
fetch(convertkit.ajaxurl,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded',},body:new URLSearchParams({action:'convertkit_store_subscriber_id_in_cookie',convertkit_nonce:convertkit.nonce,subscriber_id:subscriber_id})}).then(function(response){if(convertkit.debug){console.log(response)}
return response.json()}).then(function(result){if(convertkit.debug){console.log(result)}
convertKitRemoveSubscriberIDFromURL(window.location.href)}).catch(function(error){if(convertkit.debug){console.error(error)}
convertKitRemoveSubscriberIDFromURL(window.location.href)})}
function convertStoreSubscriberEmailAsIDInCookie(emailAddress){if(convertkit.debug){console.log('convertStoreSubscriberEmailAsIDInCookie');console.log(emailAddress)}
fetch(convertkit.ajaxurl,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded',},body:new URLSearchParams({action:'convertkit_store_subscriber_email_as_id_in_cookie',convertkit_nonce:convertkit.nonce,email:emailAddress})}).then(function(response){if(convertkit.debug){console.log(response)}}).then(function(result){if(convertkit.debug){console.log(result)}}).catch(function(error){if(convertkit.debug){console.error(error)}})}
function convertKitRemoveSubscriberIDFromURL(url){var clean_url=url.substring(0,url.indexOf("?ck_subscriber_id"));var title=document.getElementsByTagName("title")[0].innerHTML;if(clean_url){window.history.pushState(null,title,clean_url)}}
function convertKitSleep(milliseconds){var start=new Date().getTime();for(var i=0;i<1e7;i++){if((new Date().getTime()-start)>milliseconds){break}}}
document.addEventListener('DOMContentLoaded',function(){if(convertkit.subscriber_id>0&&convertkit.tag&&convertkit.post_id){convertKitTagSubscriber(convertkit.subscriber_id,convertkit.tag,convertkit.post_id)}else if(convertkit.subscriber_id>0){convertStoreSubscriberIDInCookie(convertkit.subscriber_id)}
document.addEventListener('click',function(e){if(!e.target.matches('.formkit-submit')&&!e.target.parentElement.matches('.formkit-submit')){if(convertkit.debug){console.log('not a ck form')}
return}
let emailAddress=document.querySelector('input[name="email_address"]').value;if(!emailAddress.length){if(convertkit.debug){console.log('email empty')}
return}
var validator=/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;if(!validator.test(emailAddress.toLowerCase())){if(convertkit.debug){console.log('email not an email address')}
return}
convertKitSleep(2000);convertStoreSubscriberEmailAsIDInCookie(emailAddress)})})