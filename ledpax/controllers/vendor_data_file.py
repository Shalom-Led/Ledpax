import base64
from odoo import http
from odoo.http import request
import pandas as pd
import os

class VendorData(http.Controller):

    @http.route(['/my/vendor_product_upload'], type='http', auth="user", website=True)
    def portal_vendor_file(self, order_id=None, access_token=None, **kw):

        return request.render("ledpax.vendor_product_upload")

    @http.route(['/add_product'], type='http', auth="user", methods=['POST'], website=True)
    def portal_add_product(self, **kw):
        try:
            if kw['attachment'] == '':
                return request.redirect('/my/vendor_product_upload')
            # file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + str(request.env.user.partner_id.name) + '.xlsx'
            file_path = 'src/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + str(request.env.user.partner_id.name) + '.xlsx'
            file = kw['attachment']
            attachment = file.read()
            with open(file_path, 'ab') as f:
                f.seek(0,0)
                f.write(attachment)

            dataframe = pd.read_excel(file_path)
            c = []
            col = dataframe.columns
            for i in col:
                c.append(i)
            df = dataframe.rename(columns={c[0] : 'Product Name',
                c[1] : 'Type', 
                c[2] : 'Category', 
                c[3] : 'Product Variant',
                c[4] : 'Min Quantity',
                c[5] : 'Price',
                })

            for x in range(df.shape[0]):
                prod_exist = request.env['product.product'].sudo().search([('product_tmpl_id.name', '=', df['Product Name'][x])]).id or False
                if prod_exist:
                    pass
                else:
                    product_name = df['Product Name'][x]
                    if (df['Type'][x] == 'Consumable'):
                        product_type = 'consu'
                    elif (df['Type'][x] == 'Service'):
                        product_type = 'service'
                    elif (df['Type'][x] == 'Storable Product'):
                        product_type = 'product'
                    product_category = request.env['product.category'].sudo().search([('complete_name', '=', df['Category'][x])]).id
                    product_min_quantity = df['Min Quantity'][x] or 0
                    product_price = df['Price'][x] or 0
                    product_vendor = request.env['res.partner'].sudo().search([('name', '=', request.env.user.partner_id.name)]).id

                    supplier_info = request.env['product.supplierinfo'].sudo().create({
                        'name' : product_vendor,
                        'min_qty' : product_min_quantity,
                        'price' : product_price,
                    })

                    product_template = request.env['product.template'].sudo().create({'name' : product_name, 
                                                        'type' : product_type,
                                                        'categ_id' : product_category ,
                                                        'default_code' : None ,
                                                        'seller_ids' : [(6, 0, [supplier_info.id])]})
                    try:
                        if (str(df['Product Variant'][x]) == 'nan' or df['Product Variant'][x] == product_name):
                            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', product_template.id)])
                            request.env['product.supplierinfo'].sudo().browse(supplier_info.id).write({'product_id' : product_product.id})
                    except:
                        pass

            os.remove(file_path)

        except:
            pass
        return request.redirect('/my/vendor_product_upload')

    @http.route(['/update_product'], type='http', auth="user", methods=['POST'], website=True)
    def portal_update_product(self, **kw):
        try:
            if kw['attachment'] == '':
                return request.redirect('/my/vendor_product_upload')
            # file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + str(request.env.user.partner_id.name) + '.xlsx'
            file_path = 'src/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + str(request.env.user.partner_id.name) + '.xlsx'
            file = kw['attachment']
            attachment = file.read()
            with open(file_path, 'ab') as f:
                f.seek(0,0)
                f.write(attachment)

            dataframe = pd.read_excel(file_path)
            c = []
            col = dataframe.columns
            for i in col:
                c.append(i)
            df = dataframe.rename(columns={c[0] : 'Product Name',
                c[1] : 'Product Variant', 
                c[2] : 'Min Quantity', 
                c[3] : 'Price',
                })

            for x in range(df.shape[0]):
                prod_exist = request.env['product.template'].sudo().search([('name', '=', df['Product Name'][x])]) or False
                if prod_exist:
                    product_min_quantity = df['Min Quantity'][x] if (str(df['Min Quantity'][x]) != 'nan') else [x.min_qty for x in prod_exist.seller_ids if x.name.name == request.env.user.partner_id.name][0]
                    product_price = df['Price'][x] if (str(df['Price'][x]) != 'nan') else [x.price for x in prod_exist.seller_ids if x.name.name == request.env.user.partner_id.name][0]
                    product_vendor = request.env['res.partner'].sudo().search([('name', '=', request.env.user.partner_id.name)]).id

                    product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', prod_exist.id)])
                    if (str(df['Product Variant'][x]) == 'nan' and len(product_product) == 1):
                        supplier_info = request.env['product.supplierinfo'].sudo().create({
                            'name' : product_vendor,
                            'product_id' : product_product.id,
                            'min_qty' : product_min_quantity,
                            'price' : product_price,
                        })
                        ids = [x.id for x in prod_exist.seller_ids if x.name.name != request.env.user.partner_id.name]
                        ids.append(supplier_info.id)
                        request.env['product.template'].browse(prod_exist.id).sudo().write({'seller_ids' : [(6, 0, ids)]})

                    elif (str(df['Product Variant'][x]) == 'nan' and len(product_product) > 1):
                        supplier_info = request.env['product.supplierinfo'].sudo().create({
                            'name' : product_vendor,
                            'min_qty' : product_min_quantity,
                            'price' : product_price,
                        })
                        ids = [x.id for x in prod_exist.seller_ids if x.name.name != request.env.user.partner_id.name]
                        ids.append(supplier_info.id)
                        request.env['product.template'].browse(prod_exist.id).sudo().write({'seller_ids' : [(6, 0, ids)]})

                    elif (str(df['Product Variant'][x]) != 'nan'):
                        product_variant = str(df['Product Variant'][x]).split(',')
                        product_variant_list = []
                        for prod_var in product_variant:
                            prod_attr_val = request.env['product.attribute.value'].sudo().search([('code', '=', prod_var.strip())]).id
                            if prod_attr_val:
                                product_variant_list.append(prod_attr_val)
                        product_variant_list.sort()

                        for prod_prod in product_product:
                            attr_val = []
                            for prod_var in prod_prod.attribute_value_ids:
                                attr_val.append(prod_var.id)
                            attr_val.sort()
                            if product_variant_list == attr_val:
                                id = [x.id for x in prod_exist.seller_ids if x.name.name == request.env.user.partner_id.name and x.product_id.id == prod_prod.id]
                                if id:
                                    request.env['product.supplierinfo'].sudo().browse(id).write({'min_qty' : product_min_quantity,'price' : product_price})
                                else:
                                    supplier_info = request.env['product.supplierinfo'].sudo().create({
                                        'name' : product_vendor,
                                        'product_id' : prod_prod.id,
                                        'min_qty' : product_min_quantity,
                                        'price' : product_price,
                                        })
                                    ids = [x.id for x in prod_exist.seller_ids]
                                    ids.append(supplier_info.id)
                                    request.env['product.template'].browse(prod_exist.id).sudo().write({'seller_ids' : [(6, 0, ids)]})
                else:
                    pass
            os.remove(file_path)
        except:
            pass

        return request.redirect('/my/vendor_product_upload')