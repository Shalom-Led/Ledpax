from odoo import models, fields, api
from odoo import http
from odoo.addons import decimal_precision as dp
from PyPDF2 import PdfFileWriter, PdfFileReader
import mimetypes


class OrderTag(models.Model):
    _name = 'order.tag'
    _description = "order tag"

    name = fields.Char(string='Name', store=True)
    saleorders = fields.One2many('sale.order','project_name', string='Sale Orders')
    o_tag_line = fields.One2many('order.tag.line','o_id', string='Order Tag Lines', copy=True)
    purchaseorders = fields.One2many('purchase.order','project_po', string='Purchase Orders') 
    po_tag_line = fields.One2many('order.tag.purchase.line','tag_po', string='Po Order Tag Lines', copy=True)                                              

    @api.model
    def create(self,values):
        res = super(OrderTag, self).create(values)
        ol_id = res.id
        s_orders = res.saleorders
        p_orders = res.purchaseorders
        s_data = []
        if s_orders:
            for so_id in s_orders:
                val = so_id.id
                sale_order = self.env['sale.order'].search([('id','=',val)])
                prod = sale_order.order_line
                for p in prod:
                    pro_id = p.product_id
                    for i in pro_id:
                        prod_name = i.name
                        prod_description = i.prod_description
                    dic = {'order_name': sale_order.name,
                           'o_id': ol_id,
                           'partner_name': sale_order.partner_id.name,
                           'invoice_adrress': sale_order.partner_invoice_id.name,
                           'delivery_address': sale_order.partner_shipping_id.name,
                           'confirm_date': sale_order.confirmation_date,
                           'ordered_quantity': p.product_uom_qty,
                           'delivered_quantity': p.qty_delivered,
                           'invoice_quantity': p.qty_invoiced,
                           'unit_price': p.price_unit,
                           'tax': p.tax_id.name,
                           'subtotal': p.price_subtotal,
                           'margin': p.margin,
                           'products': prod_name,
                           'pd': prod_description,
                           'type': p.type,
                           }
                    self.env['order.tag.line'].sudo().create(dic)
        if p_orders:
            for po_id in p_orders:
                po_val = po_id.id
                purchase_order = self.env['purchase.order'].search([('id','=',po_val)])
                po_lines = purchase_order.order_line
                for line in po_lines:
                    po_dic = {'po_order_name': purchase_order.name,
                            'tag_po' : ol_id,
                            'vendor_name' : purchase_order.partner_id.name, 
                            'vendor_ref' : purchase_order.partner_ref,
                            'order_date' : purchase_order.date_order,
                            'po_type' : line.type,
                            'prod': line.product_id.name,
                            'po_description': line.name,
                            'estimate_date' : line.date_planned,
                            'quantity' : line.product_qty,
                            'po_unit_price' : line.price_unit,
                            'po_tax' : line.taxes_id.name,
                            'po_subtotal' : line.price_subtotal,
                            }
                    self.env['order.tag.purchase.line'].sudo().create(po_dic)
        return res

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
    ordered_quantity = fields.Char(string="Ordered Quantity",  compute='confirmdate', default= 0.0)
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

class OrderTagPurchaseLine(models.Model):

    _name = "order.tag.purchase.line"
    _description = "order tag purchase Lines"

    tag_po = fields.Many2one('order.tag', string='Po Order', index=True, ondelete='cascade')
    po_order_name = fields.Char(string="Order Name")
    vendor_name = fields.Char(string="Vendor")
    vendor_ref = fields.Char(string="Vendor Ref")
    order_date = fields.Datetime(string="Order date")
    po_type = fields.Char(string="Type")
    prod = fields.Char(string="Product")
    po_description = fields.Char(string="Description")
    estimate_date = fields.Datetime(string="Estimated date")
    quantity = fields.Char(string="Quantity")
    po_unit_price = fields.Char(string="Unit Price")
    po_tax = fields.Char(string="Tax")
    po_subtotal = fields.Char(string="Subtotal")
    po_total = fields.Char(string="Total")
