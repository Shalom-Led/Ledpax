# -*- coding: utf-8 -*-
{
    'name': "ledpax",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Techspawn Solutions",
    'website': "https://www.techspawn.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','sale_management','product','web','account','project','stock','mrp','website_sale','sale_stock','documents','delivery'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
     #    'wizard/create_product_excel.xml',
     #    'wizard/create_product_image_excel.xml',
     #    'views/partner.xml',
     #    'views/related_products.xml',
     #    'views/pdf_view.xml',
     #    'views/related_products.xml',
     #    'views/templates.xml',
     #    'views/purchase_template.xml',
     #    'views/purchase_quotation_template.xml',
     #    'views/custom_header_footer.xml',
     #    'views/create_rfq_button.xml',
     #    'views/mail_to_po.xml',
     #    'views/ack_button.xml',
     #    'views/backorder_pur.xml',
	    # 'views/quatation.xml',
     #    'views/purchase_details_page.xml',
     #    'views/home_page.xml', 
     #    'views/project.xml',
     #    'views/del_room.xml',
     #    'views/order_tag.xml',
     #    'views/project_menu.xml',
     #    'views/process_checkout.xml',
     #    'views/product_view.xml',
     #    'views/report_invoice_doc.xml',
     #    'views/views.xml',
     #    # 'views/report_delivery_slip.xml',
     #    'views/pdf_delivery_room.xml',
     #    'views/report_project.xml',        

    ],
    'external_dependencies' :{
        'python' : ['pdf2image'],
    }, 
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

}
