
odoo.define('vendor_portal_management.Submit', function (require) {
"use strict";
$(document).ready(function() {
$('#submit').click(function (e){

var rpc = require('web.rpc');

var date = document.getElementById("date").value ;
var note = document.getElementById("note").value ;
var qoute_p = document.getElementById("qoute_p").value ;
var url = window.location.href
var po_id = url.split("/")[5]

console.log("URL : ", url)
console.log("My PRICE : ", qoute_p)
console.log("My DATE : ", date)
console.log("My NOTE : ", note)
console.log("PO_ID : ", po_id)


rpc.query({
// your model
model: "vendor.portal",
// data function
method: 'get_values',
//args, first id of record, and array another args
args: [[], [qoute_p,date,note,po_id]],

}).then(function (result) { 
alert(result)
window.location = '/'
})



});
});

});