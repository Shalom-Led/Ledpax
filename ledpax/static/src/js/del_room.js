odoo.define('ledpax.AddQuantity', function (require) {
"use strict";
	$(document).ready(function() {
	$('#add_quantity').click(function (e){

	var rpc = require('web.rpc');
	var bol_id= [];
    var add_qnt = [];
    $('input[name^="additional_quantity"]').each(function() {
    bol_id.push($(this).data('id'));
    add_qnt.push($(this).val());
    });
	var url = window.location.href
	var do_id = url.split("/")[5]

    rpc.query({
                model: "sale.order",
                method: 'create_so',
                args: [[], [do_id, add_qnt,bol_id]],
            }).then(function (result) { 
                alert(result)
                window.location = '/my/del_room'
            }) 
	});
	});

	});