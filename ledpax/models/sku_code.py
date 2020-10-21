from odoo import fields, models,api,tools
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

class ProductCategory(models.Model):
    _inherit = 'product.category'
    short_code = fields.Char("Short Code")
    start_num = fields.Integer(string="Start Number")


class ProductAttributeinherit(models.Model):
    _inherit = 'product.attribute.value'
    

    value = fields.Selection([
        ('ww', 'wall washer'),
        ('down', 'Down light'),
        ('AA', 'Adjustable Angle')], string="Field value")
    
    code = fields.Char('Short Code')


class ProductTemplate(models.Model):
    _inherit  = "product.template"
    related_product_ids = fields.Many2many('product.related', string="Related Products", domain="[('product_type', '=', categ_id)]")
    default_code = fields.Char('SKU')
    pdf_image = fields.Binary('Upload Product Image in PDF Format', attachment=True, copy=False)
    excel_file = fields.Binary('Upload Excel File of BOM Products', attchment=True, copy=False)
    prod_variant = fields.Many2one('product.product', 'Product Variant', domain="[('product_tmpl_id', '=', id )]")
    file_excel = fields.Char(string='Upload Excel')
    file_pdf = fields.Char(string='Upload PDF')
    create_rfq = fields.Integer('RFQ', compute='_compute_rfq_count')
    # type = fields.Selection([
    #     ('product', 'Stock Product'),
    #     ('consu', 'Drop Ship'),
    #     ('consu', 'Manufacture'),
    #     ('service', 'Service')], string='Product Type', default='consu', required=True,
    #     help='A Stock Product is a product for which you manage stock. The Inventory app has to be installed.\n'
    #          'A Drop Ship product is a product for which stock is not managed.\n'
    #          'A Manufacture is a non-material product you provide.')
    drawing_number = fields.Char('Drawing Number')
    part_number_index = fields.Char('Part Number Index')
    status_active = fields.Boolean('Active ', default=True)
    status_inactive = fields.Boolean('Not Active', default=False)
    warehouse = fields.Char('WAREHOUSE', compute='_compute_warehouse')
    bin = fields.Char('BIN', compute='_compute_bin')
    uom = fields.Selection([
        ('EA', 'EA'),
        ('FT', 'FT'),
        ('LB', 'LB'),
        ('OZ', 'OZ')], string='UOM', help='Unit of Measure.')
    name = fields.Char('Name', index=True, required=True, translate=True)
    prod_description = fields.Char('Product Description', index=True)
    p_description = fields.Char('Prod Description', compute='_compute_size', size=80)
    short_des = fields.Char('Prods Description', compute='_compute_size', size=80)


    def _compute_size(self):
        for i in self:
            i.p_description = i.prod_description

    @staticmethod
    def generate_sku_code(auto_default_code, auto_vals_list, auto_method, auto_self=None) :
        method = auto_method
        default_code = auto_default_code
        vals_list = auto_vals_list
        sku_codes = []
        if method == 'create':
            try:
                self = auto_self
                count = 0
                for x in vals_list[0]['attribute_line_ids']:
                    originalvalue = self.env['product.attribute.value'].search([('id', '=', vals_list[0]['attribute_line_ids'][count][2]['value_ids'][0][2])]).code
                    default_code = default_code + '-'  + originalvalue
                    count += 1
                sku_codes = default_code
            except KeyError:
                sku_codes = default_code
            except:
                pass
        if method == 'write':
            try:
                self = auto_self
                count = 0
                for x in vals_list['attribute_line_ids']:
                    originalvalue = self.env['product.attribute.value'].search([('id', '=', vals_list['attribute_line_ids'][count][2]['value_ids'][0][2])]).code
                    default_code = default_code + '-'  + originalvalue
                    count += 1
                sku_codes = default_code
            except TypeError:
                pass
            except KeyError:
                try :
                    if self.attribute_line_ids:
                        for x in self.attribute_line_ids:
                            default_code = default_code + '-' + str(x.value_ids.code)
                except:
                    pass
                sku_codes = default_code
            except:
                pass
        return sku_codes

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # TDE FIXME: context brol
        try:
            if vals_list[0]['name'] :
                if self.env['product.template'].search([('name', '=', vals_list[0]['name'])]):
                    raise exceptions.ValidationError('Product Name should be unique !')
        except KeyError:
            pass
        except:
            raise exceptions.ValidationError('Product Name should be unique !')
        try:
            if vals_list[0]['default_code'] :
                if self.env['product.template'].search([('default_code', '=', vals_list[0]['default_code'])]):
                    raise exceptions.ValidationError('SKU should be unique !')
        except KeyError:
            pass
        except:
            raise exceptions.ValidationError('SKU should be unique !')
        try:
            if vals_list[0]['description']:
                vals_list[0]['description_sale'] = vals_list[0]['description']
                vals_list[0]['description_purchase'] = vals_list[0]['description']
        except:
            pass
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
        sku_codes = []
        for v in vals_list:
            try:
                parent_path = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).parent_path
                templates = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).name.upper()
                if templates == 'MASTER PRODUCT STOCKABLE' and v['default_code'] == False:
                    if self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num == 0 :
                        obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                        obj['start_num'] = 100000
                    num_mps = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num
                    sub_code = ''
                    path = parent_path.split('/')[ :-2]
                    for num in path :
                        sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                    curr_code = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).short_code
                    default_code = '[' + curr_code + str(num_mps) + ']' + sub_code[1:]
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals_list,'create',self)
                    update_num_mps = num_mps + 1
                    update_obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                    update_obj['start_num'] = update_num_mps
                elif templates == 'COMPONENT STOCKABLE' and v['default_code'] == False:
                    if self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num == 0 :
                        obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                        obj['start_num'] = 200000
                    num_cs = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num
                    sub_code = ''
                    path = parent_path.split('/')[ :-2]
                    for num in path :
                        sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                    curr_code = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).short_code
                    default_code = '[' + curr_code + str(num_cs) + ']' + sub_code[1:]
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals_list, 'create',self)
                    update_num_cs = num_cs + 1
                    update_obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                    update_obj['start_num'] = update_num_cs
                elif templates == 'MADE TO ORDER PRODUCT' and v['default_code'] == False:
                    if self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num == 0 :
                        obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                        obj['start_num'] = 100000
                    num_mop = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num
                    sub_code = ''
                    path = parent_path.split('/')[ :-2]
                    for num in path :
                        sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                    curr_code = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).short_code
                    default_code = '[' + curr_code + str(num_mop) + ']' + sub_code[1:]
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals_list,'create',self)
                    update_num_mop = num_mop + 1
                    update_obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                    update_obj['start_num'] = update_num_mop
                elif templates == 'MADE TO ORDER COMPONENT' and v['default_code'] == False:
                    if self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num == 0 :
                        obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                        obj['start_num'] = 200000
                    num_moc = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).start_num
                    sub_code = ''
                    path = parent_path.split('/')[ :-2]
                    for num in path :
                        sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                    curr_code = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])]).short_code
                    default_code = '[' + curr_code + str(num_moc) + ']' + sub_code[1:]
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals_list,'create',self)
                    update_num_moc = num_moc + 1
                    update_obj = self.env['product.category'].search([('id', '=', vals_list[0]['categ_id'])])
                    update_obj['start_num'] = update_num_moc
                else:
                    path = parent_path.split('/')[ :-1]
                    default_code = ''
                    for num in path :
                        sub_code = self.env['product.category'].search([('id', '=', num)]).short_code
                        default_code = default_code + '-' + sub_code
                    default_code = default_code[1:]
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals_list,'create',self)
            except :
                pass

            # v['default_code']=default_code
            # vals_list[0]['default_code'] = sku_codes
            part_number_index = self.env['product.template'].search_count([])
            vals_list[0].update({'part_number_index': format(part_number_index+1 ,'08')})
            record = super(ProductTemplate, self).create(vals_list)
            
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
                                self.env['product.image'].create({'product_tmpl_id' : record.id ,
                                        'name' : vals_list[0]['name'] + '_' + str(ncount),
                                        'image' : base64.b64encode(img) })
                            ncount += 1
                            os.remove(rm_img)
                    os.remove(file)
            except:
                pass
        return record

    @api.multi
    def write(self, vals):
        try:
            if 'name' in vals.keys():
                if vals['name']:
                    if self.env['product.template'].search([('name', '=', vals['name'])]):
                        raise exceptions.ValidationError('Product Name should be unique !')
        except:
            raise exceptions.ValidationError('Product Name should be unique !')
        try:
            if 'default_code' in vals.keys():
                if vals['default_code']:
                    if self.env['product.template'].search([('default_code', '=', vals['default_code'])]):
                        raise exceptions.ValidationError('SKU should be unique !')
        except:
            raise exceptions.ValidationError('SKU should be unique !')
        # try:
        #     if vals['name']:
        #         prod_name = vals['name']
        # except KeyError:
        #     prod_name = self.name
        # except:
        #     pass
        try:
            if 'description' in vals.keys():
                if vals['description']:
                    vals['description_sale'] = vals['description']
                    vals['description_purchase'] = vals['description']
        except:
            pass
        try :
            if vals['pdf_image'] :
                from pdf2image import convert_from_path
                try:
                    self.env['product.image'].search([('product_tmpl_id', '=', self.id)]).unlink()
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
            try:
                if vals['name'] and self.excel_file:
                    file_path = '/home/dolly/Desktop/Excel data/' + prod_name + '.xlsx'
                    with open(os.path.expanduser(file_path), 'wb') as fout:
                        fout.write(self.excel_file)
                        os.chmod(file_path, 0o777)
            except:
                pass
        except:
            raise exceptions.ValidationError('Selected file is not Excel supported. Upload Excel file.')

        try :
            if vals['categ_id']:
                try:
                    parent_path = self.env['product.category'].search([('id', '=', vals['categ_id'])]).parent_path
                    templates = self.env['product.category'].search([('id', '=', vals['categ_id'])]).name.upper()
                    if templates == 'MASTER PRODUCT STOCKABLE':
                        if self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num == 0 :
                            obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                            obj['start_num'] = 100000
                        num_mps = self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num
                        sub_code = ''
                        path = parent_path.split('/')[ :-2]
                        for num in path :
                            sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                        curr_code = self.env['product.category'].search([('id', '=', vals['categ_id'])]).short_code
                        default_code = '[' + curr_code + str(num_mps) + ']' + sub_code[1:]
                        sku_codes = ProductTemplate.generate_sku_code(default_code, vals,'write')
                        update_num_mps = num_mps + 1
                        update_obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                        update_obj['start_num'] = update_num_mps
                    elif templates == 'COMPONENT STOCKABLE':
                        if self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num == 0 :
                            obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                            obj['start_num'] = 200000
                        num_cs = self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num
                        sub_code = ''
                        path = parent_path.split('/')[ :-2]
                        for num in path :
                            sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                        curr_code = self.env['product.category'].search([('id', '=', vals['categ_id'])]).short_code
                        default_code = '[' + curr_code + str(num_cs) + ']' + sub_code[1:]
                        sku_codes = ProductTemplate.generate_sku_code(default_code, vals, 'write')
                        update_num_cs = num_cs + 1
                        update_obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                        update_obj['start_num'] = update_num_cs
                    elif templates == 'MADE TO ORDER PRODUCT':
                        if self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num == 0 :
                            obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                            obj['start_num'] = 100000
                        num_mop = self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num
                        sub_code = ''
                        path = parent_path.split('/')[ :-2]
                        for num in path :
                            sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                        curr_code = self.env['product.category'].search([('id', '=', vals['categ_id'])]).short_code
                        default_code = '[' + curr_code + str(num_mop) + ']' + sub_code[1:]
                        sku_codes = ProductTemplate.generate_sku_code(default_code, vals,'write')
                        update_num_mop = num_mop + 1
                        update_obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                        update_obj['start_num'] = update_num_mop
                    elif templates == 'MADE TO ORDER COMPONENT':
                        if self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num == 0 :
                            obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                            obj['start_num'] = 200000
                        num_moc = self.env['product.category'].search([('id', '=', vals['categ_id'])]).start_num
                        sub_code = ''
                        path = parent_path.split('/')[ :-2]
                        for num in path :
                            sub_code = sub_code + '-' +self.env['product.category'].search([('id', '=', num)]).short_code
                        curr_code = self.env['product.category'].search([('id', '=', vals['categ_id'])]).short_code
                        default_code = '[' + curr_code + str(num_moc) + ']' + sub_code[1:]
                        sku_codes = ProductTemplate.generate_sku_code(default_code, vals,'write')
                        update_num_moc = num_moc + 1
                        update_obj = self.env['product.category'].search([('id', '=', vals['categ_id'])])
                        update_obj['start_num'] = update_num_moc
                    else:
                        path = parent_path.split('/')[ :-1]
                        default_code = ''
                        for num in path :
                            sub_code = self.env['product.category'].search([('id', '=', num)]).short_code
                            default_code = default_code + '-' + sub_code
                        default_code = default_code[1:]
                        sku_codes = ProductTemplate.generate_sku_code(default_code, vals,'write',self)
                except :
                    pass
                # vals['default_code'] = sku_codes
        except KeyError:
            try:
                if vals['attribute_line_ids']:
                    default_code = self.default_code
                    sku_codes = ProductTemplate.generate_sku_code(default_code, vals,'write',self)
                    # vals['default_code'] = sku_codes
            except:
                pass
        except:
            pass

        res = super(ProductTemplate, self).write(vals)

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
                            self.env['product.image'].create({'product_tmpl_id' : self.id ,
                                        'name' : prod_name + '_' + str(ncount),
                                        'image' : base64.b64encode(img) })
                        ncount += 1
                        os.remove(rm_img)
                os.remove(file)
        except:
            pass

        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})   
        return res

    def _compute_rfq_count(self):
        for product in self:
            product.create_rfq = self.env['purchase.order.line'].search_count([('product_id.product_tmpl_id.id','=',product.id)])

    def action_view_rfq(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if products and len(products) == 1:
            action['domain'] = [('order_line.product_id.name', '=', self.name)]
            action['context'] = {'default_product_id': products.ids[0],
                                 'default_product_uom':1,
                                 'default_name':self.name,
                                }
        elif products :
            try:
                for prod in products :
                    if prod.id == self.prod_variant.id:
                        id = prod.id
                        name = prod.name
                action['domain'] = [('order_line.product_id.name', '=', name)]
                action['context'] = {'default_product_id': id,
                                 'default_product_uom':1,
                                 'default_name': name
                                }
            except UnboundLocalError:
                raise exceptions.ValidationError('Select the product variant.')
        else:
            action['domain'] = [('product_id', 'in', products.ids)]
            action['context'] = {}
        return action

    @api.multi
    @api.onchange('categ_id')
    def on_change_review(self):
        keys =[]
        if self.categ_id.name == 'Downlight' :
            for key in self.env['product.related'].search([('product_type', '=', self.categ_id.name)]):
                keys.append(key.id)
        else :
            for key in self.env['product.related'].search([('product_type', '=', self.categ_id.name)]):
                keys.append(key.id)
        self.update({'related_product_ids':[(6, 0,[y for y in keys])]})

    def _compute_bin(self):
        bin, str_bin = set(), ''
        products = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        for product in products:
            locations = self.env['stock.quant'].search([('product_id', '=', product.id), ('quantity', '>=', 0)])
            for location in locations:
                bin.add(location.location_id.name)
        count = 0
        for bin_loc in bin:
            if count != 0:
                str_bin = str_bin + ' , ' + str(bin_loc)
            else:
                str_bin = str_bin + str(bin_loc)
                count = 1
        self.bin = str_bin

    def _compute_warehouse(self):
        warehouse, str_warehouse = set(), ''
        products = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        for product in products:
            locations = self.env['stock.quant'].search([('product_id', '=', product.id), ('quantity', '>=', 0)])
            for location in locations:
                for loc in location.location_id.complete_name.split('/'):
                    is_warehouse = self.env['stock.warehouse'].search([('code', '=', loc)])
                    if is_warehouse:
                        warehouse.add(is_warehouse.name)
        count = 0
        for ware_loc in warehouse:
            if count != 0:
                str_warehouse = str_warehouse + ' , ' + str(ware_loc)
            else:
                str_warehouse = str_warehouse + str(ware_loc)
                count = 1
        self.warehouse = str_warehouse
