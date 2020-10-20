# -*- coding: utf-8 -*-
{
    'name': "vendor portal",

    'summary': """
        Vendor Portal """,

    'description': """
        This module allows the Odoo admin to create RFQ. The vendors once registered can view the RFQs from their respective website accounts and submit their quotations right away. The Odoo admin can select the best-suited deal and create a purchase order.
    """,

    'author': "Techspawn",
    'website': "http://www.techspawn.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'purchase', 'portal','website','sale_stock'],
    'data':[
        'security/ir.model.access.csv',
        'views/main.xml',
        'views/vendor_portal_menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}