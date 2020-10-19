odoo.define('ledpax.LedpaxPurchase', function (require) {
    "use strict";
    $(document).ready(function() {
    $('#submit_date').click(function (e){

    var rpc = require('web.rpc');
    var date = document.getElementById("get_date").value ;
    var url = window.location.href
    var po_id = url.split("/")[5]

    if (date == '')
    {
        alert('Enter Date...');
        return
    }
    var y = date.split('-')[0];
    var m = date.split('-')[1];
    var d = date.split('-')[2];
    var today = new Date();
    var today_date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
    if (Date(y,m,d) < today_date)
    {
        alert('Enter Correct Date...')
        return
    }

    rpc.query({
                model: "purchase.order",
                method: 'fill_eta',
                args: [[], [po_id, date]],
            })      
});
});
});