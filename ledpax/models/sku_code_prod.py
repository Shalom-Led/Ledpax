# -*- coding: utf-8 -*-
from odoo import fields, models,api,tools, _
from odoo.modules import get_module_resource
from odoo import exceptions
import psycopg2
import base64
import io
import os
try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class CustomProductProduct(models.Model):
    _inherit  = "product.product"

    related_product_ids = fields.Many2many('product.related', string="Related Products", domain="[('product_type', '=', categ_id)]")
    pdf_image = fields.Binary('Upload Product Image in PDF Format', attachment=True)
    excel_file = fields.Binary('Upload Excel File of BOM Products', attchment=True)
    prod_variant = fields.Many2one('product.product', 'Product Variant', domain="[('product_tmpl_id', '=', id )]")
    file_excel = fields.Char(string='Upload Excel')
    file_pdf = fields.Char(string='Upload PDF')
    # default_code = fields.Char(compute='_compute_default_code', search='_product_search')
    default_code = fields.Char()
    rfq_count = fields.Integer('RFQ count', compute='_compute_rfq_count')

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        try:
            if 'default_code' in vals_list[0].keys():
                if vals_list[0]['default_code']:
                    if self.env['product.product'].search([('default_code', '=', vals_list[0]['default_code'])]):
                        raise exceptions.ValidationError('SKU should be unique !')
        except KeyError:
            pass
        except:
            raise exceptions.ValidationError('SKU should be unique !')
        try :
            if vals_list[0]['pdf_image'] :
                from pdf2image import convert_from_path
                code = bytes(vals_list[0]['pdf_image'], encoding='utf-8')
                file = '/home/odoo12_entrp/Downloads/Temp_PDF/' + vals_list[0]['name'] + '.pdf' 
                with open(os.path.expanduser(file), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file,0o777)
                pdf = convert_from_path(file)
                for page in pdf:
                    img_name = vals_list[0]['name'] + '.jpg'
                    rm_img = '/odoo12/custom/addons/ledpax/static/image/' + img_name
                    page.save(os.path.join('/odoo12/custom/addons/ledpax/static/image', img_name), 'JPEG')
                    img = False
                    img_path = get_module_resource('ledpax', 'static/image', img_name)
                    if img_path:
                        with open(img_path, 'rb') as f:
                            img = f.read()
                            vals_list[0]['image_medium'] = base64.b64encode(img)
                    os.remove(rm_img)
                    break
        except KeyError:
            pass
        except Exception as e:
            print(str(e))
            raise exceptions.ValidationError('Selected file is not PDF supported. Upload PDF file.')
        try :
            if vals_list[0]['excel_file'] :
                file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/' + vals_list[0]['name'] + '.xlsx'
                code = bytes(vals_list[0]['excel_file'], encoding='utf-8')
                with open(os.path.expanduser(file_path), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file_path, 0o777)
        except KeyError:
            pass
        except :
            raise exceptions.ValidationError('Selected file is not Excel supported. Upload Excel file.')

        record = super(CustomProductProduct, self).create(vals_list)
        try:
            if vals_list[0]['pdf_image']:
                file = '/home/odoo12_entrp/Downloads/Temp_PDF/' + vals_list[0]['name'] + '.pdf' 
                pdf = convert_from_path(file)
                img_name = vals_list[0]['name'] + '.jpg'
                rm_img = '/odoo12/custom/addons/ledpax/static/image/' + img_name
                ncount = 0
                for page in pdf:
                    if ncount == 0:
                        ncount += 1
                    else :
                        page.save(os.path.join('/odoo12/custom/addons/ledpax/static/image', img_name), 'JPEG')
                        img = False
                        img_path = get_module_resource('ledpax', 'static/image', img_name)
                        if img_path:
                            with open(img_path, 'rb') as f:
                                img = f.read()
                                self.env['product.image'].create({'product_tmpl_id' : record.product_tmpl_id.id ,
                                        'name' : vals_list[0]['name'] + '_' + str(ncount),
                                        'image' : base64.b64encode(img) })
                        ncount += 1
                        os.remove(rm_img)
                os.remove(file)
        except Exception:
            pass
        return record

    @api.multi
    def write(self, vals):
        try:
            if 'default_code' in vals.keys():
                if vals['default_code']:
                    if self.env['product.product'].search([('default_code', '=', vals['default_code'])]):
                        raise exceptions.ValidationError('SKU should be unique !')
        except:
            raise exceptions.ValidationError('SKU should be unique !')
        try:
            if vals['name']:
                prod_name = vals['name']
        except KeyError:
            try:
                for product in self:  
                    prod_name = product.name
                    break
            except:
                pass
        except:
            pass
        try :
            if vals['pdf_image'] :
                from pdf2image import convert_from_path
                try:
                    self.env['product.image'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)]).unlink()
                except:
                    pass
                code = bytes(vals['pdf_image'], encoding='utf-8')
                file = '/home/odoo12_entrp/Downloads/Temp_PDF/' + prod_name + '.pdf' 
                with open(os.path.expanduser(file), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file, 0o777)
                pdf = convert_from_path(file)
                for page in pdf:
                    img_name = prod_name + '.jpg'
                    rm_img = '/odoo12/custom/addons/ledpax/static/image/' + img_name
                    page.save(os.path.join('/odoo12/custom/addons/ledpax/static/image', img_name), 'JPEG')
                    img = False
                    img_path = get_module_resource('ledpax', 'static/image', img_name)
                    if img_path:
                        with open(img_path, 'rb') as f:
                            img = f.read()
                            vals['image_medium'] = base64.b64encode(img)
                    os.remove(rm_img)
                    break
        except KeyError:
            pass
        except:
            raise exceptions.ValidationError('Selected file is not PDF supported. Upload PDF file.')
        try :
            if vals['excel_file'] :
                file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/' + prod_name + '.xlsx'
                code = bytes(vals['excel_file'], encoding='utf-8')
                with open(os.path.expanduser(file_path), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file_path, 0o777)
        except KeyError:
            try :
                if vals['name'] and self.excel_file:
                    file_path = '/home/dolly/Desktop/Excel data/' + prod_name + '.xlsx'
                    with open(os.path.expanduser(file_path), 'wb') as fout:
                        fout.write(self.excel_file)
                        os.chmod(file_path, 0o777)
            except:
                pass
        except:
            raise exceptions.ValidationError('Selected file is not Excel supported. Upload Excel file.')

        res = super(CustomProductProduct, self).write(vals)

        try:
            if vals['pdf_image']:
                file = '/home/odoo12_entrp/Downloads/Temp_PDF/' + prod_name + '.pdf' 
                pdf = convert_from_path(file)
                img_name = prod_name + '.jpg'
                rm_img = '/odoo12/custom/addons/ledpax/static/image/' + img_name
                ncount = 0
                for page in pdf:
                    if ncount == 0:
                        ncount += 1
                    else :
                        page.save(os.path.join('/odoo12/custom/addons/ledpax/static/image', img_name), 'JPEG')
                        img = False
                        img_path = get_module_resource('ledpax', 'static/image', img_name)
                        if img_path:
                            with open(img_path, 'rb') as f:
                                img = f.read()
                            self.env['product.image'].create({'product_tmpl_id' : self.product_tmpl_id.id ,
                                        'name' : prod_name + '_' + str(ncount),
                                        'image' : base64.b64encode(img) })
                        ncount += 1
                        os.remove(rm_img)
                os.remove(file)
        except:
            pass
 
        return res

    @api.multi
    def _product_search(self, operator, value):
        recs = self.search([('product_tmpl_id.name',operator,value)])
        if recs:
            return [('id','in',[x.id for x in recs])]

    def _compute_rfq_count(self):
        for product in self:
            product.rfq_count = self.env['purchase.order.line'].search_count([('product_id.id','=',product.id)])

    def action_view_rfq(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if products :
            for prod in products :
                if prod.default_code == self.default_code:
                    id = prod.id
                    name = prod.name
            action['domain'] = [('order_line.product_id.name', '=', name)]
            action['context'] = {'default_product_id': id,
                                 'default_product_uom':1,
                                 'default_name': name
                                }
        else:
            action['domain'] = [('product_id', 'in', products.ids)]
            action['context'] = {}
        return action

    @api.one
    def _compute_default_code(self):
        try :
            parent_path = self.env['product.category'].search([('id', '=', self.categ_id.id)]).parent_path
            count = 0
            final_list = []
            for x in self.attribute_value_ids :
                sub_list = []
                sub_list.append(self.attribute_value_ids[count].attribute_id.name.upper())
                sub_list.append(self.attribute_value_ids[count].code)
                final_list.append(sub_list)
                count += 1
            templates = self.env['product.category'].search([('id', '=', self.categ_id.id)]).name.upper()
            if templates == 'MASTER PRODUCT STOCKABLE':
                if self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num == 0 :
                    obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                    obj['start_num'] = 100000
                num_mps = self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num
                sub_code = ''
                path = parent_path.split('/')[ :-2]
                for num in path :
                    sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                curr_code = self.env['product.category'].search([('id', '=', self.categ_id.id)]).short_code
                default_code = '[' + curr_code + str(num_mps) + ']' + sub_code[1:]
                update_num_mps = num_mps + 1
                update_obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                update_obj['start_num'] = update_num_mps
            elif templates == 'COMPONENT STOCKABLE':
                if self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num == 0 :
                    obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                    obj['start_num'] = 200000
                num_cs = self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num
                sub_code = ''
                path = parent_path.split('/')[ :-2]
                for num in path :
                    sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                curr_code = self.env['product.category'].search([('id', '=', self.categ_id.id)]).short_code
                default_code = '[' + curr_code + str(num_cs) + ']' + sub_code[1:]
                update_num_cs = num_cs + 1
                update_obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                update_obj['start_num'] = update_num_cs
            elif templates == 'MADE TO ORDER PRODUCT':
                if self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num == 0 :
                    obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                    obj['start_num'] = 100000
                num_mop = self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num
                sub_code = ''
                path = parent_path.split('/')[ :-2]
                for num in path :
                    sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                curr_code = self.env['product.category'].search([('id', '=', self.categ_id.id)]).short_code
                default_code = '[' + curr_code + str(num_mop) + ']' + sub_code[1:]
                update_num_mop = num_mop + 1
                update_obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                update_obj['start_num'] = update_num_mop
            elif templates == 'MADE TO ORDER COMPONENT':
                if self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num == 0 :
                    obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                    obj['start_num'] = 200000
                num_moc = self.env['product.category'].search([('id', '=', self.categ_id.id)]).start_num
                sub_code = ''
                path = parent_path.split('/')[ :-2]
                for num in path :
                    sub_code = sub_code + '-' + self.env['product.category'].search([('id', '=', num)]).short_code
                curr_code = self.env['product.category'].search([('id', '=', self.categ_id.id)]).short_code
                default_code = '[' + curr_code + str(num_moc) + ']' + sub_code[1:]
                update_num_moc = num_moc + 1
                update_obj = self.env['product.category'].search([('id', '=', self.categ_id.id)])
                update_obj['start_num'] = update_num_moc
            else:
                path = parent_path.split('/')[ :-1]
                default_code = ''
                for num in path :
                    sub_code = self.env['product.category'].search([('id', '=', num)]).short_code
                    default_code = default_code + '-' + sub_code  
                default_code = default_code[1:]
            for a in final_list :
                originalvalue = a[1]
                default_code = default_code + '-'  + originalvalue
        except TypeError:
            try:
                parent_path = self.env['product.category'].search([('id', '=', self.categ_id.id)]).parent_path
                path = parent_path.split('/')[ :-1]
                default_code = ''
                for num in path :
                    sub_code = self.env['product.category'].search([('id', '=', num)]).short_code
                    default_code = default_code + '-' + sub_code  
                default_code = default_code[1:]
            except TypeError:
                default_code = ''
        except:
            default_code = ''

        self.default_code = default_code
