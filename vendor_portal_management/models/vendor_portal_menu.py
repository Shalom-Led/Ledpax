from odoo import api, fields, models, _
from datetime import date
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class VendorPortalWebsite(models.Model):
    _name = "vendor.portal"
    _description = "Vendor Portal"

    name = fields.Char(string='RFQ Reference', readonly=True, required=True, copy=False, default='New')
    product_id = fields.Many2one('product.product', string='Product', change_default=True, required=True)
    rfq_reference = fields.Char(string='Rfq Reference', compute='_rfq_reference')
    product_qty = fields.Float(string='Quantity', required=True)
    estimated_quote = fields.Text(string='Our Estimated Quote')
    estimated_delivery = fields.Date(string='Our Estimated Delivery')
    vendor = fields.Text(string="Vendor")
    rfq_closing_date = fields.Date(string='RFQ Closing Date', required=True)
    date_order = fields.Datetime('Order Date', required=True, index=True, copy=False, default=fields.Datetime.now,\
    help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    vendor_line = fields.One2many('vendor.order.lines', 'vportal_id', string='Order Lines', copy=True)
    select_vendor = fields.Many2one('vendor.order.lines', string='Select Vendor', domain="[('vportal_id','=',id)]")
    state = fields.Selection([
        	('draft', 'Draft'),
         	('pending', 'Pending'),
         	('done', 'Done'),
         	('cancelled', 'Cancelled')
         	], string='RFQ Status', store=True, readonly=True, default='draft')        

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                with_context(ir_sequence_date=vals.get('date_order')).\
                next_by_code('vendor.portal.name')
        return super(VendorPortalWebsite, self).create(vals)

    def cancel(self):
        self.write({'state': 'cancelled'})

    def set_to_pending(self):
        self.write({'state': 'pending'})

    def get_values(self,data):
        e_price = data[0]
        e_date = data[1]
        e_note = data[2]
        e_rfqid = data[3]
        epoid = e_rfqid
        vid = self.env['vendor.portal'].sudo().search([('id','=',epoid)])
        close_date = str(vid.rfq_closing_date)
        if e_date < close_date:
            return "The date can't be in the past."
        partner = self.env.user.partner_id.name
        pol_vals = {    'vendors': partner,
                        'estimated_quote_by_vendor':e_price,
                        'estimated_date_by_vendor':e_date,
                        'notes':e_note,
                        'vportal_id':epoid,
                        }            
        self.env['vendor.order.lines'].sudo().create(pol_vals)
        return "Thanks. We receive your qoute." 

    def create_po(self):
        v_partner = self.vendor
        v_partner_id = self.env['res.partner'].search([('name','=',v_partner)])
        result = self.env['purchase.order'].create({
            'partner_id': v_partner_id.id,
            'date_order': self.date_order,
            'order_line': [
                (0, 0, {
                    'name': self.product_id.name,
                    'product_id': self.product_id.id,
                    'product_qty': self.product_qty,
                    'product_uom': self.product_id.uom_po_id.id,
                    'price_unit': self.estimated_quote,
                    'date_planned': self.estimated_delivery,
                })],
        })
        body = "<p>Dear,<p><p>Purchase Order Created</p><br></br><tr><td>Regards,</td></tr><tr><td>%s</td></tr>" %(v_partner_id.company_id.name)
        mail_values = {
                'email_to': v_partner_id.email,
                'subject': "Purchase Order",
                'body_html': body,
                'state': 'outgoing',
                'type': 'email',
                }
        mail_id =self.env['mail.mail'].create(mail_values)
        mail_id.send()
        return result

    @api.multi
    def submit_button(self):
        self.write({'state':'done'})
        selected_vendor = self.select_vendor
        self.update({
                    'vendor': selected_vendor.vendors,
                    'estimated_quote':selected_vendor.estimated_quote_by_vendor,
                    'estimated_delivery':selected_vendor.estimated_date_by_vendor,
                    })

class VendorOrderLines(models.Model):
    _name = "vendor.order.lines"
    _description = "Vendor Order Lines"

    vportal_id = fields.Many2one('vendor.portal', string='Order Reference', index=True, required=True, ondelete='cascade')
    estimated_quote_by_vendor = fields.Float(string='Our Estimated Quote')
    estimated_date_by_vendor = fields.Date(string="Estimated Date", required=False)
    vendors =fields.Text(string='Vendor', change_default=True,)
    notes = fields.Text(string="Note")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s - (%s)' % (record.vendors, record.estimated_quote_by_vendor)))
        return result