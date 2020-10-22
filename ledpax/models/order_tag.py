from odoo import models, fields, api
from odoo import http
from odoo.addons import decimal_precision as dp
from PyPDF2 import PdfFileWriter, PdfFileReader
import mimetypes


class OrderTag(models.Model):
    _name = 'order.tag'
    _description = "order tag"

    name = fields.Char(string='Name', store=True)
    saleorders = fields.One2many('sale.order','project_name', string='Orders')
    o_tag_line = fields.One2many('order.tag.line','o_id', string='Order Tag Lines', copy=True)

    @api.model
    def create(self,values):
        res = super(OrderTag, self).create(values)
        ol_id = res.id
        s_orders = res.saleorders
        s_data = []
        for so_id in s_orders:
            val = so_id.id
            sale_order = self.env['sale.order'].search([('id','=',val)])
            partner = sale_order.partner_id.name
            o_name = sale_order.name
            prod = sale_order.order_line
            for p in prod:
                type = p.type
                pro_id = p.product_id
                o_qty = p.product_uom_qty
                d_qty = p.qty_delivered
                i_qty = p.qty_invoiced
                u_price = p.price_unit
                o_tax = p.tax_id
                o_subtotal = p.price_subtotal
                o_margin = p.margin
                for i in pro_id:
                    prod_name = i.name
                    prod_description = i.prod_description
                dic = {'order_name': o_name,
                       'o_id': ol_id,
                       'partner_name': partner,
                       'invoice_adrress': sale_order.partner_invoice_id.name,
                       'delivery_address': sale_order.partner_shipping_id.name,
                       'confirm_date': sale_order.confirmation_date,
                       'ordered_quantity': o_qty,
                       'delivered_quantity': d_qty,
                       'invoice_quantity': i_qty,
                       'unit_price': u_price,
                       'tax': o_tax.name,
                       'subtotal': o_subtotal,
                       'margin': o_margin,
                       # 'ref': ref,
                       'products': prod_name,
                       'pd': prod_description,
                       'type': type,
                       }
                # s_data.append(dic)
                self.env['order.tag.line'].sudo().create(dic)
        return res

    @api.multi
    @api.onchange('saleorders')
    def onchange_saleorders(self):
        ol_id = self._origin.id
        s_orders = self.saleorders
        s_data = []
        for so_id in s_orders:
            val = so_id.id
            sale_order = self.env['sale.order'].search([('id','=',val)])
            partner = sale_order.partner_id.name
            o_name = sale_order.name
            prod = sale_order.order_line
            for p in prod:
                type = p.type
                pro_id = p.product_id
                o_qty = p.product_uom_qty
                d_qty = p.qty_delivered
                i_qty = p.qty_invoiced
                u_price = p.price_unit
                o_tax = p.tax_id
                o_subtotal = p.price_subtotal
                o_margin = p.margin
                for i in pro_id:
                    prod_name = i.name
                    prod_description = i.prod_description
                dic = {'order_name': o_name,
                       'o_id': ol_id,
                       'partner_name': partner,
                       'invoice_adrress' : sale_order.partner_invoice_id.name,
                       'delivery_address' : sale_order.partner_shipping_id.name,
                       'confirm_date' : sale_order.confirmation_date,
                       'ordered_quantity' : o_qty,
                       'delivered_quantity' : d_qty,
                       'invoice_quantity' : i_qty,
                       'unit_price' : u_price,
                       'tax': o_tax.name,
                       'subtotal' : o_subtotal,
                       'margin' : o_margin,
                       'products' : prod_name,
                       'pd' : prod_description,
                       'type' : type,
                       }
                # s_data.append(dic)
                self.env['order.tag.line'].sudo().create(dic)

class OrderTagLine(models.Model):

    _name = "order.tag.line"
    _description = "order tag Lines"

    o_id = fields.Many2one('order.tag', string='Order', index=True, ondelete='cascade')
    order_name = fields.Char(string="Name")
    partner_name = fields.Char(string="partner")
    invoice_adrress = fields.Char(string="Invoice Address")
    delivery_address = fields.Char(string="Delivery Address")
    confirm_date = fields.Datetime(string="Confirmation Date", compute='confirmdate', default= None)
    products = fields.Char(string="Products")
    ordered_quantity = fields.Char(string="Ordered Quantity", compute='confirmdate', default= 0.0)
    delivered_quantity = fields.Char(string="Delivered Quantity", compute='confirmdate', default= 0.0)
    invoice_quantity = fields.Char(string="Invoice Quantity", compute='confirmdate', default= 0.0)
    unit_price = fields.Char(string="Unit Price")
    tax = fields.Char(string="Taxes")
    subtotal = fields.Float(string="Subtotal", digits=dp.get_precision('Product Price'))
    margin = fields.Float(string="Margin", digits=dp.get_precision('Product Price'))
    total = fields.Char(string="Total")
    ref = fields.Char(string="Referance", compute='referance', default= None)
    pd = fields.Char(string="PD", required=False, )
    type =fields.Char(string="Type")

    @api.model
    def referance(self):
        for line in self:
            # res = self.env['sale.order'].search([('name', '=', line.order_name)])
            ref = None
            purchase_order_line = self.env['purchase.order.line'].search(
                [('order_id.origin', '=', line.order_name), ('product_id.name', '=', line.products)])
            if purchase_order_line:
                for pol in purchase_order_line:
                    if pol.order_id.origin == line.order_name and pol.product_id.name == line.products:
                        ref = "In Purchase Order " + " " + str(pol.order_id.name)
                        line.update({'ref': ref})
            else:
                stock_line = self.env['stock.move'].search(
                    [('origin', '=', line.order_name), ('product_id.name', '=', line.products)])

                for stol in stock_line:
                    if stol.origin == line.order_name and stol.product_id.name == line.products:
                        ref = "In Transfer " + " " + str(stol.picking_id.name)
                        line.update({'ref': ref})

    @api.model
    def confirmdate(self):
        for line in self:
            sol = self.env['sale.order.line'].search(
                [('order_id.name', '=', line.order_name), ('product_id.name', '=', line.products), ('type', '=', line.type)])
            if sol:
                for i in sol:
                    line.update({'confirm_date': i.order_id.confirmation_date,
                                 'delivered_quantity':i.qty_delivered,
                                 'invoice_quantity':i.qty_invoiced,
                                 'ordered_quantity':i.product_uom_qty,
                                 })
