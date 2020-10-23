# -*- coding: utf-8 -*-
from odoo import fields, models,api,tools
from odoo import exceptions
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import *

class PurchaseOrderLin(models.Model):
    _inherit = 'purchase.order.line'
    difference = fields.Float(string="difference", compute='_compute_difference')
    settled = fields.Boolean(string='Settled')
    type = fields.Char(string='Type')

    @api.depends('product_id', 'product_qty', 'price_unit','qty_received')
    def _compute_difference(self):
        for line in self:
            diff = (line.qty_received * line.price_unit ) - (line.product_qty * line.price_unit)
            line.update({'difference': diff})

class SaleOrderLin(models.Model):
    _inherit = 'sale.order.line'

    margin = fields.Float(string="Margin", compute='_compute_margin', digits=dp.get_precision('Product Price'))
    margindper=fields.Float(string='Marginper',compute='compute_permargin')
    margin_percentage = fields.Char(string="Margin Percentage", compute='_compute_margin_percentage')

    @api.depends('product_id','product_uom_qty','price_unit','discount')
    def _compute_margin(self):
        for prod in self:
            discout = ((prod.product_uom_qty  * prod.price_unit )/100) * prod.discount
            marg = (prod.product_uom_qty  * prod.price_unit ) - (prod.product_uom_qty * prod.product_id.standard_price) - discout
            if marg != 0.0:
                prod.update({'margin': marg})
                break
            else:
                prod.update({'margin': 0.00})


    @api.depends('product_id','product_uom_qty','price_unit','discount')
    def _compute_margin_percentage(self):
        cost = margin_percentage = 0.0
        for line in self:
            discout = ((line.product_uom_qty  * line.price_unit )/100) * line.discount
            # cost = line.product_id.standard_price * line.product_uom_qty
            selling_price = (line.product_uom_qty * line.price_unit) - discout
            if selling_price:
                margin_percentage = (((line.product_uom_qty  * line.price_unit ) - (line.product_uom_qty * line.product_id.standard_price) - discout) / selling_price) * 100
            else:
                margin_percentage = 100
            line.margin_percentage = str(round(margin_percentage,2)) + ' %'
    # not update on sh
    # @api.onchange('product_id')
    # @api.multi
    # def onchange_prodcut_id(self):
    #     date = fields.Date.today()
    #     supplier_list = []
    #     ven_price = []
    #     if self.product_id.seller_ids:
    #         for supplier in self.product_id.seller_ids:
    #             if supplier.date_start and supplier.date_end:
    #                 if supplier.date_start and supplier.date_start > date:
    #                     continue
    #                 if supplier.date_end and supplier.date_end < date:
    #                     continue
    #                 supplier_list.append(supplier)
    #         for rec in supplier_list:
    #             ven_price.append(rec.price)
    #         if ven_price:
    #             ven_price = min(ven_price)
    #             self.update({'price_unit': ven_price})
    #     elif not self.product_id.seller_ids:
    #         for rec in self:
    #             rec.price_unit = rec.product_id.lst_price

    @api.multi
    @api.depends('order_id.delivery_count')
    def _compute_qty_delivered(self):
        super(SaleOrderLin, self)._compute_qty_delivered()
        for line in self:
            for move in line.move_ids:
                if move.state == 'assigned':
                    m_qty = move.product_uom_qty
                    done_q = float(line.product_uom_qty) - float(m_qty)
                    line.qty_delivered = done_q

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project=fields.Many2one('project.project',
                            string='project',
                            default=lambda self: self.env.context.get('default_project_id'),
                            index=True,
                            track_visibility='onchange')

    state = fields.Selection(selection_add=[
        ('Estimatedtime','Ack. from Vendor'),    
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    print_company_id = fields.Many2one('res.company', string='Report Company', required=True,
                                       default=lambda self: self.env['res.company']._company_default_get(
                                           'purchase.order'))

    project_so = fields.Char(string="Project", related='group_id.sale_id.project_name.name', default=None)
    date_ack = fields.Date(track_visibility='onchange')
    date_for_name = fields.Date('Estimated Date', track_visibility='onchange')


    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        if(self._context.get('default_product_id')):
            order_line = []
            line = (0, 0, {'product_id': self._context.get('default_product_id'),
                           'product_uom':self._context.get('default_product_uom'),
                           'name':self._context.get('default_name')
                          })
            order_line.append(line)
            res.update({
                'order_line': order_line,
            })
        return res

#     @api.multi
#     def write(self, values):
#         try:
#             if values['date_ack'] != False:   
#                 values.update(state='Estimatedtime')
#         except Exception:
#             pass
#         return super(PurchaseOrder, self).write(values)

#     @api.multi
#     def button_confirm(self):
#         button_confirm = self.env['purchase.order'].search([('id', '=', self.id)])
#         button_confirm.update({'state':'to approve'})
#         self.ensure_one()
#         ir_model_data = self.env['ir.model.data']
#         try:
#             template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_porder_done')[1]
#         except ValueError:
#             template_id = False
#         try:
#             compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
#         except ValueError:
#             compose_form_id = False
#         ctx = {
#             'default_model': 'purchase.order',
#             'default_res_id': self.ids[0],
#             'default_use_template': bool(template_id),
#             'default_template_id': template_id,
#             'default_composition_mode': 'comment',
#             'mark_so_as_sent': True,
#             'proforma': self.env.context.get('proforma', False),
#             'force_email': True
#         }
#         return {
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'mail.compose.message',
#             'views': [(compose_form_id, 'form')],
#             'view_id': compose_form_id,
#             'target': 'new',
#             'context': ctx,
#         }

#     @api.multi
#     def fill_eta(self, data):
#         try:
#             if data[1] == "" :
#                 raise exceptions.UserError("Select the ETA Date...")
#             y = int(data[1].split('-')[0])
#             m = int(data[1].split('-')[1])
#             d = int(data[1].split('-')[2])
#             if (date.today() > date(y,m,d)):
#                 raise exceptions.UserError("Select the correct ETA Date...")
#             obj = self.sudo().search([('id', '=', int(data[0]))])
#             obj.sudo().date_ack = data[1]
#         except :
#             pass

class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')),
                                           ('res_id', '=', vals.get('res_id')),
                                           ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.unlink()
        res = super(Followers, self).create(vals)
        return res

class SaleOrde(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('exp', 'Expire'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=False, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    project = fields.Many2one('project.project',
                              string='Project',
                              default=lambda self: self.env.context.get('default_project_id'),
                              index=True,
                              track_visibility='onchange',
                              change_default=True)

    project_name = fields.Many2one('order.tag', string= "ProjectName")
    total_margin = fields.Monetary(string="Total Margin", readonly=True, compute='_compute_total_margin')
    print_company_id = fields.Many2one('res.company', string='Report Company', required=True, default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    total_margin_percentage = fields.Char(string="Total Margin Percentage", compute='_compute_total_margin_percentage')

    @api.depends('order_line.product_id','order_line.product_uom_qty','order_line.price_unit')
    def _compute_total_margin(self):
        for order in self:
            tot_margin = 0.0
            for line in order.order_line:
                tot_margin += line.margin
            order.update({'total_margin': tot_margin})

    @api.depends('order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_unit', 'order_line.margin_percentage')
    def _compute_total_margin_percentage(self):
        for order in self:
            i = 0
            total = 0.0
            for line in order.order_line:
                if (' %' in line.margin_percentage):
                    val = line.margin_percentage
                    val = val.replace(' %', '')
                    margin_percentage = float(val)
                    total += margin_percentage
                    i += 1
                    final = float(total / (i * 100)) * 100
                    order.total_margin_percentage = str(round(final, 2)) + ' %'
                else:
                    total_margin_percentage = 0.0
                    order.total_margin_percentage = str(round(total_margin_percentage, 2)) + ' %'

    @api.multi
    def unlink(self):
        saleorder = self.name
        tag_line = self.env['order.tag.line'].search([('order_name','=',saleorder)])
        if tag_line:
            for tag in tag_line:
                tag.unlink()
        super(SaleOrde, self).unlink()

    @api.model
    def create(self, vals):
        res = super(SaleOrde, self).create(vals)
        if res.project_name:
            proj_value = res.project_name.id
            project = res.id
            project_n = res.env['sale.order'].search([('id','=',project)]).id
            s_order_obj = res.env['sale.order'].search([('id','=',project)])
            val = res.env['order.tag'].search([('id','=',proj_value)])
            sale_o = []
            s_orders = val.saleorders
            for s in s_orders:
                so = s.id
                sale_o.append(so)
            s_data = []
            sale_o.append(project_n)      
            val.update({'saleorders': [( 6, 0, sale_o)]})
            prod = res.order_line
            for obj in prod:
                type = obj.type
                pro_id = obj.product_id
                o_qty = obj.product_uom_qty
                d_qty = obj.qty_delivered
                i_qty = obj.qty_invoiced
                u_price = obj.price_unit
                o_tax = obj.tax_id
                o_subtotal = obj.price_subtotal
                o_margin = obj.margin
                for i in pro_id:
                    prod_name = i.name
                    prod_description = i.prod_description
                dic = {'order_name': s_order_obj.name,
                            'o_id': val.id,
                            'partner_name': s_order_obj.partner_id.name,
                            'invoice_adrress' : s_order_obj.partner_invoice_id.name,
                            'delivery_address' : s_order_obj.partner_shipping_id.name,
                            'confirm_date' : s_order_obj.confirmation_date,
                            'ordered_quantity' : o_qty,
                            'delivered_quantity' : d_qty,
                            'invoice_quantity' : i_qty,
                            'unit_price' : u_price,
                            'tax': o_tax.name,
                            'subtotal' : o_subtotal,
                            'margin' : o_margin,
                            'products' : prod_name,
                            'pd': prod_description,
                            'type': type,
                              }
            # s_data.append(dic)
                res.env['order.tag.line'].sudo().create(dic)
        return res

    @api.onchange('project_name')
    def project_onchange(self):
        if self.project_name:
            proj_value = self.project_name.id
            project = self._origin.id
            project_n = self.env['sale.order'].search([('id','=',project)]).id
            s_order_obj = self.env['sale.order'].search([('id','=',project)])
            val = self.env['order.tag'].search([('id','=',proj_value)])
            sale_o = []
            s_orders = val.saleorders
            for s in s_orders:
                so = s.id
                sale_o.append(so)
            s_data = []
            sale_o.append(project_n)      
            val.update({'saleorders': [( 6, 0, sale_o)]})
            prod = self.order_line
            if prod:
                for obj in prod:
                    type = obj.type
                    pro_id = obj.product_id
                    o_qty = obj.product_uom_qty
                    d_qty = obj.qty_delivered
                    i_qty = obj.qty_invoiced
                    u_price = obj.price_unit
                    o_tax = obj.tax_id
                    o_subtotal = obj.price_subtotal
                    o_margin = obj.margin
                    for i in pro_id:
                        prod_name = i.name
                        prod_description = i.prod_description
                    dic = {'order_name': s_order_obj.name,
                            'o_id': val.id,
                            'partner_name': s_order_obj.partner_id.name,
                            'invoice_adrress' : s_order_obj.partner_invoice_id.name,
                            'delivery_address' : s_order_obj.partner_shipping_id.name,
                            'confirm_date' : s_order_obj.confirmation_date,
                            'ordered_quantity' : o_qty,
                            'delivered_quantity' : d_qty,
                            'invoice_quantity' : i_qty,
                            'unit_price' : u_price,
                            'tax': o_tax.name,
                            'subtotal' : o_subtotal,
                            'margin' : o_margin,
                            'products' : prod_name,
                            'pd': prod_description,
                            'type': type,
                           }
                    # s_data.append(dic)
                    self.env['order.tag.line'].sudo().create(dic)
 
    @api.multi
    def create_so(self,data):
        d_order = data[0]
        add_qnt = data[1]
        ol_ids = data[2]
        if '?' in d_order:
            doid = d_order[:-1]
        else:
            doid = d_order        
        partner = self.env.user.partner_id
        s_order = self.env['stock.picking'].sudo().search([('id','=',doid)])
        sale_order = s_order.origin
        s_name = self.env['sale.order'].sudo().search([('name','=',sale_order)])
        s_line = []
        for qnt in s_order.move_ids_without_package: 
            for y in add_qnt:
                if y != "":
                    if float(y) > float(qnt.product_id.qty_available):
                        return "Not enough stock !"
                    o_line = (0, 0, {'product_id': qnt.product_id.id,
                                        'product_uom_qty': y,
                                        })
                    s_line.append(o_line)
                if add_qnt : 
                    add_qnt.pop(0)
                    break
                else:
                    pass

        so_vals = {'partner_id': partner.id,
                    'project_name':s_name.project_name.id,
                    'order_line': s_line           
                    }

        self.env['sale.order'].sudo().create(so_vals)
        return "New Quotation Created"

class CustomStockMove(models.Model):
    _inherit = "stock.move"
    
    reserved_availability = fields.Float(
        'Quantity Reserved', compute='_compute_reserved_availability',
         help='Quantity that has already been reserved for this move')

    shipping_note = fields.Char("Shipping Note")               

class Pickinginherit(models.Model):
    _inherit = 'stock.picking'
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    prod_typ = fields.Char(string='Product Type',compute='_find_type')
    project_so = fields.Char(string="Project", compute='custom_so_project', default=None, store=True)

    @api.depends('origin')
    def custom_so_project(self):
        for order in self:
            so = self.env['sale.order'].search([('name', '=', order.origin)])
            po = self.env['purchase.order'].search([('name', '=', order.origin)])
            if so:
                for i in so:
                    order.update({'project_so': i.project_name.name,
                                  })
            elif po:
                for i in po:
                    order.update({'project_so': i.project_so,
                                  })
            else:
                order.update({'project_so': None,
                              })

    @api.multi
    def _find_type(self):
        prod_typ_list=[]
        for id in self:
            obj=self.env['stock.picking'].search([("name","=",id.name)])
            obj1=self.env['stock.move'].search([('picking_id','=',obj.id)])
            for stock_move in obj1:
                type_sal = stock_move.product_id.type
                prod_typ_list.append(type_sal)
            id.update({'prod_typ' :'%s' % ', '.join(map(str, prod_typ_list))})
            prod_typ_list=[]
     
    sku_cod = fields.Char( string='SKU' , compute='_find_code')
    @api.multi
    def _find_code(self):
        sku_cod_list=[]
        for id in self:
            obj=self.env['stock.picking'].search([("name","=",id.name)])
            obj1=self.env['stock.move'].search([('picking_id','=',obj.id)])
            for stock_move in obj1:
                default_code =stock_move.product_id.default_code
                sku_cod_list.append(default_code)
            id.update({'sku_cod' :'%s' % ', '.join(map(str, sku_cod_list))})
            sku_cod_list=[]

    tot_qnt = fields.Float(string='Total quantity' , compute='_find_quantity')
    @api.one
    def _find_quantity(self):
        temp_total = 0
        for id in self:
            sp_obj=self.browse(id)
            sm_obj=self.env['stock.move'].search([('picking_id','=',sp_obj.id.id)])
            for line in sm_obj:
                temp_total += line.quantity_done
        self.tot_qnt = temp_total

    @api.multi
    def release_qty(self,data):
        b_order = data[0]
        bol_id = data [1]
        r_qty = data [2]
        ship_notes = data [3]
        if '?' in b_order:
            boid = b_order[:-1]
        else:
            boid = b_order        
        delivery_line = []
        back_order = self.env['stock.picking'].sudo().search([('id','=',boid)])
        delivery_order = back_order.backorder_id
        s_order = back_order.origin
        sal_order = self.env['sale.order'].sudo().search([('name','=',s_order)]).id
        for obj in back_order.move_lines:
            for note in ship_notes:
                for x in r_qty:
                    if (x != '' or note != ''):
                        if float(x) > float(obj.product_id.qty_available):
                            return "Not enough stock !"
                        reserved = float(obj.reserved_availability) - float(x)
                        if obj.state != 'partially_available':
                            if float(obj.reserved_availability) < float(x):
                                return "Hey reserved quantity is"+ " " + str(obj.reserved_availability) + " " + "if you want more quantity you can add in additional quantity"
                        obj.update({'product_uom_qty':reserved})
                        products = obj.product_id.id
                        sal_line = self.env['sale.order.line'].sudo().search(['&',('order_id','=',sal_order),('product_id','=',products)]) 
                        delivered = float(sal_line.qty_delivered) + float(x)
                        so_line = sal_line.id
                        move_line = {   'picking_id': back_order.id,
                                        'sale_id' : back_order.sale_id.id,
                                        'group_id' : back_order.group_id.id,
                                        'name': 'outgoing_shipment_move',
                                        'product_id': products,
                                        'product_uom_qty': x,
                                        'quantity_done' : x,
                                        'product_uom': 1,
                                        'state': 'done' ,
                                        'shipping_note': note,
                                        'location_id':  self.env.ref('stock.stock_location_stock').id,
                                        'location_dest_id': self.env.ref('stock.stock_location_customers').id}               
                        delivery_line.append(move_line)
                    if r_qty: 
                        r_qty.pop(0)
                        break
                    else:
                        pass                      
                if ship_notes: 
                    ship_notes.pop(0)
                    break
                else:
                    pass 
        backorders = self.env['stock.picking']
        for picking in back_order:
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            if moves_to_backorder:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id
                })
                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorder_picking.action_assign()
                backorders |= backorder_picking
        
        for pick in backorders.move_lines:
            for mov in r_qty:
                reserved = float(pick.reserved_availability) - float(mov)
                pick.update({'product_uom_qty': reserved})
                if r_qty : 
                    r_qty.pop(0)
                break
        self.env['stock.move'].sudo().create(delivery_line)
        back_order.action_done()
        back_order.write({'state':'done'})
        return backorders

class CustomResPartner(models.Model):
    _inherit = 'res.partner'
    documents_url = fields.Char(string='Documents URL')
    
class CustomAccountInvoice(models.Model):
    _inherit = 'account.invoice'
    print_company_id = fields.Many2one('res.company', string='Report Company', required=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    project_so = fields.Char(string="Project", compute='customproject', default=None, store=True)
    @api.depends('origin')
    def customproject(self):
        for order in self:
            so = self.env['sale.order'].search([('name', '=', order.origin)])
            po = self.env['purchase.order'].search([('name', '=', order.origin)])
            if so:
                for i in so:
                    order.update({'project_so': i.project_name.name,
                                 })
            elif po:
                for i in po:
                    order.update({'project_so': i.project_so,
                                 })
            else:
                order.update({'project_so': None,
                                 })

# class CustomPurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#     print_company_id = fields.Many2one('res.company', string='Report Company', required=True, default=lambda self: self.env['res.company']._company_default_get('purchase.order'))
#     project_so = fields.Char(string="Project",related='group_id.sale_id.project_name.name', default=None)
#
