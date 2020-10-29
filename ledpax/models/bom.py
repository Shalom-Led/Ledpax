from odoo import fields, models, api, tools, _
from odoo import exceptions
import pandas as pd
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    prod_name = fields.Char(string="Product Name",  related='product_tmpl_id.name')
    prod_description1 = fields.Char(string="Product Description",  related='product_tmpl_id.prod_description')
    # uom1 = fields.Char(string="UOM",  related='product_tmpl_id.uom_id.name')

    # Added validation to avoide duplicate bill of material
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            mo = self.env['mrp.bom'].search([])
            for val in mo:
                if val.product_tmpl_id == self.product_tmpl_id:
                    raise ValidationError(_('The Bills of Materials of Product ' + self.product_tmpl_id.name + ' is already exist. '))

    @api.model_create_multi
    def create(self, vals_list):
        temp = []
        product_id = False
        try:
            for x in self.env['product.product'].search([('product_tmpl_id', '=', vals_list[0]['product_tmpl_id'])]) :
                product_id = x.prod_variant.id
                break
        except:
            pass
        try :
            for x in self.env['product.product'].search([('product_tmpl_id', '=', vals_list[0]['product_tmpl_id'])]) :
                prod_name = x.name
                break
            # file_name = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/' + prod_name + '.xlsx'
            file_name = 'src/Downloads/Ledpax_Excel_Data/' + prod_name + '.xlsx'
            dataframe = pd.read_excel(file_name)
            c = []
            col = dataframe.columns
            for i in col:
                c.append(i)
            df = dataframe.rename(columns={c[0]:'Product Name', c[1]:'Quantity', c[2]:'Category', c[3]:'Variants'})
            """for the product in Excel which is not created"""
            for x in range(df.shape[0]):
                prod_exist = self.env['product.product'].search([('product_tmpl_id.name', '=', df['Product Name'][x])]).id or False
                if prod_exist :
                    pass
                else:
                    categ_id = self.env['product.category'].search([('complete_name', '=', df['Category'][x])]).id
                    self.env['product.template'].create({'name' : df['Product Name'][x], 
                                                        'categ_id' : categ_id ,
                                                        'default_code' : None })
            variant_ids = []
            try :
                for z in self.env['product.template'].search([('id','=',vals_list[0]['product_tmpl_id'])]).attribute_line_ids:
                    for x in z.value_ids:
                        variant_ids.append(x.id)
            except:
                pass
            list_data = []
            temp_dict = {}
            for x in range(df.shape[0]):
                if len(variant_ids) == 0 : 
                    var_data = []   
                    prod_id = self.env['product.product'].search([('product_tmpl_id.name', '=', df['Product Name'][x])]).id
                    prod_uom_id = self.env['product.product'].search([('product_tmpl_id.name', '=', df['Product Name'][x])]).product_tmpl_id.uom_po_id.id
                    prod_qty = df['Quantity'][x]
                    temp_dict = {'product_qty': prod_qty , 'product_uom_id': prod_uom_id , 'product_id': prod_id }
                    temp_dict.update({'attribute_value_ids' : [[6,False,var_data]]})
                    temp.append((0,0,temp_dict))
                else:
                    var_data = []
                    var_list = str(df['Variants'][x]).split(',')
                    for var in var_list:
                        if var == 'nan':
                            pass
                        else:
                            id = self.env['product.attribute.value'].search([('code','=',var)]).id
                            if id in variant_ids:
                                var_data.append(id)
                            else:
                                raise exceptions.ValidationError('Given variants is invalid.')
                    prod_id = self.env['product.product'].search([('product_tmpl_id.name', '=', df['Product Name'][x])]).id
                    prod_uom_id = self.env['product.product'].search([('product_tmpl_id.name', '=', df['Product Name'][x])]).product_tmpl_id.uom_po_id.id
                    prod_qty = df['Quantity'][x]
                    temp_dict = {'product_qty': prod_qty , 'product_uom_id': prod_uom_id , 'product_id': prod_id }
                    temp_dict.update({'attribute_value_ids' : [[6,False,var_data]]})
                    temp.append((0,0,temp_dict))
        except:
            pass

        if 'bom_line_ids' not in vals_list[0]:
            res = super(MrpBom,self).create({
                'active': vals_list[0]['active'] or None,
                'product_qty': vals_list[0]['product_qty'] or None,
                'product_uom_id': vals_list[0]['product_uom_id'] or None,
                'type': vals_list[0]['type'] or None,
                'company_id': vals_list[0]['company_id'] or None,
                'ready_to_produce': vals_list[0]['ready_to_produce'] or None,
                'product_tmpl_id': vals_list[0]['product_tmpl_id'] or None,
                'product_id' : product_id or None,
                'routing_id': vals_list[0]['routing_id'] or None,
                'code': vals_list[0]['code'] or None,
                'sequence': vals_list[0]['sequence'] or None,
                'picking_type_id': vals_list[0]['picking_type_id'] or None,
                'message_attachment_count': vals_list[0]['message_attachment_count'] or None,
                'bom_line_ids' : temp or None
            })
            return res

        else:
            New_val = [(0, 0, {
                'product_qty': vals_list[0]['bom_line_ids'][0][2]['product_qty'] or None,
                'product_uom_id': vals_list[0]['bom_line_ids'][0][2]['product_uom_id'] or None,
                'product_id': vals_list[0]['bom_line_ids'][0][2]['product_id'] or None,
                'attribute_value_ids': [[vals_list[0]['bom_line_ids'][0][2]['attribute_value_ids']]]
            })]

            res = super(MrpBom, self).create({
                'active': vals_list[0]['active'] or None,
                'product_qty': vals_list[0]['product_qty'] or None,
                'product_uom_id': vals_list[0]['product_uom_id'] or None,
                'type': vals_list[0]['type'] or None,
                'company_id': vals_list[0]['company_id'] or None,
                'ready_to_produce': vals_list[0]['ready_to_produce'] or None,
                'product_tmpl_id': vals_list[0]['product_tmpl_id'] or None,
                'product_id': product_id or None,
                'routing_id': vals_list[0]['routing_id'] or None,
                'code': vals_list[0]['code'] or None,
                'sequence': vals_list[0]['sequence'] or None,
                'picking_type_id': vals_list[0]['picking_type_id'] or None,
                'message_attachment_count': vals_list[0]['message_attachment_count'] or None,
                'bom_line_ids': New_val or None
            })
            return res   

class Mrpproduction(models.Model):
    _inherit = 'mrp.production'

    project_so = fields.Char(string="Project", compute='custom_so_project_in_bom', default=None, store=True)

    @api.depends('origin')
    def custom_so_project_in_bom(self):
        for order in self:
            so = self.env['sale.order'].search([('name', '=', order.origin)])
            if so:
                for i in so:
                    order.update({'project_so': i.project_name.name})
            else:
                order.update({'project_so': None,
                              })
