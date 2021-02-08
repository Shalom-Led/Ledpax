# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.exceptions import AccessError, UserError, RedirectWarning, MissingError, ValidationError, Warning
from odoo.addons.website_sale.controllers.main import WebsiteSale


class PurchaseOrder(http.Controller):

    @http.route('/my/purchase', type='http', auth="user", website=True)
    def purchase_order_details(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = {}
        partner = request.env.user.partner_id
        PurchaseOrder = request.env['purchase.order'].sudo().search(['&',('partner_id','=',partner.id),('state','=','purchase')])  
        values.update({
            'orders': PurchaseOrder,
        })
        return request.render('ledpax.purchase_order_details', {'values':values})

    @http.route(['/my/purchase/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_purchase_order(self, order_id=None, access_token=None, **kw):
        try:
            values = {}
            order = request.env['purchase.order'].sudo().search([('id','=',order_id)])
            values.update({'order' : order})
        except:
            pass
        return request.render("ledpax.my_purchase_order", {'values': values})

class CustomerPortal(http.Controller):

    @http.route(['/my/project'], type='http', auth="user", website=True)
    def project_page_function(self, **kw):
        values = {}
        partner = request.env.user.partner_id.id
        SaleOrder = request.env['order.tag'].sudo().search([]) 
        values.update({
            'orders': SaleOrder,
            'partner_id': partner
        })
        return request.render("ledpax.order_tag_project", values)

    @http.route(['/my/project/<int:order_id>'], type='http', auth="user", website=True)
    def project_name_page(self,order_id=None, access_token=None, **kw):
        values = {}
        partner = request.env.user.partner_id
        SaleOrder = request.env['order.tag'].sudo().search([('id','=',order_id)]) 
        values.update({
            'orders': SaleOrder,
        })
        return request.render("ledpax.project_name_page", values)

    @http.route(['/my/project/quotes'], type='http', auth="user", website=True)
    def project_qoutes(self, access_token=None, **kw):
        try:
            values = {}
            url_referrer = request.httprequest.referrer
            proj_id = url_referrer.split("/")[5]
            if '?' in proj_id:
                or_id = proj_id[:-1]
            else:
                or_id = proj_id
            order = []
            order_tags = request.env['order.tag'].sudo().search([('id','=',or_id)])
            partner_id = request.env.user.partner_id.id
            for tag in order_tags.saleorders:
                o_tag = tag.id
                quotes = request.env['sale.order'].sudo().search([('id','=',o_tag),('partner_id','=',partner_id)])
                if quotes.state == 'draft' or quotes.state == 'sent': 
                    order.append(quotes)
            values.update({'orders' : order,})
        except:
            pass
        return request.render("ledpax.delivery_room", {'values': values})


    @http.route(['/my/project/quotes/<int:order_id>'],  type='http', auth="public", website=True)
    def portal_quotation_details(self, order_id=None, access_token=None, **kw):
        values = {}
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo().search([('id','=',order_id)]) 
        values.update({
            'orders': SaleOrder,
        })
        return request.render("ledpax.qoutation_order", {'values': values})

    @http.route(route='/my/delivery_room/quotation_so', csrf=False, type='http', auth="public", methods=['POST'], website=True)
    def quotation_to_so(self, **kw):
        try:
            sale_ids = kw['data'].split(',')
            msg_id = ''
            for x in sale_ids:
                if x == '':
                    return "Select the Quotation."
                sale_order = request.env['sale.order'].sudo().browse(int(x)).action_confirm()
                if sale_order == True:
                    msg_id += request.env['sale.order'].sudo().search([('id','=',int(x))]).name + ' '
            return 'Sale Order ' + msg_id + ' Created.'
        except:
            pass
        return

    @http.route(['/my/del_room'], type='http', auth="user", website=True)
    def del_room_page_function(self, **kw):
        url_referrer = request.httprequest.referrer
        proj_id = url_referrer.split("/")[5]
        if '?' in proj_id:
            del_proj = proj_id[:-1]
        else:
            del_proj = proj_id        
        proj_int = int(del_proj)
        proj = request.env['order.tag'].sudo().search([('id','=',proj_int)])
        proj_name = proj.name
        values = {}
        partner = request.env.user.partner_id
        Del_room = request.env['stock.picking'].sudo().search([('partner_id','=',partner.id),('project_so','=',proj_name)])  
        values.update({
            'orders': Del_room,
        })
        return request.render("ledpax.del_room_page", values)

    @http.route(['/my/del_room/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_backorders(self, order_id=None, access_token=None, **kw):
        values = {}
        Del_room = request.env['stock.picking'].sudo().search([('id','=',order_id)])  
        values.update({
            'orders': Del_room,
        })
        return request.render('ledpax.del_room_order', {'values': values}) 

    @http.route(['/my/del_room/add_qty/<int:order_id>/<int:line_id>'], type='http', auth="public", website=True)
    def decline(self, order_id, line_id, access_token=None, **post):
        # _logger.error(order_id)
        # _logger.error(line_id)
        _logger.error(post)
        try:
            order_sudo = self._document_check_access('stock.picking', order_id, access_token=access_token)
            _logger.error(line_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        request.env['sale.order.line'].browse([line_id]).write({'price_unit': post.get('price')})

        return request.redirect("/my/del_room/" + str(order_id))


    @http.route(route='/my/home_page/graph_data', csrf=False, type='http', auth="public", methods=['POST'], website=True)
    def graph_data(self, **kw):
        date_data = []
        orders = request.env['sale.order'].sudo().search([['partner_id.name','=',request.env.user.partner_id.name],['state','=','sale']])
        for x in orders:
            date_data.append(x.date_order)
        final_data =[]
        for di in range(1,13):
            count = 0
            for dd in date_data:
                if ((int((str(dd))[:4]) == int(kw['year'])) and (int((str(dd))[5:7]) == int(str(di)))):
                    count += 1
            final_data.append(count)
        data = str(final_data)[1:-1]

        return data   

    @http.route(['/my/projects'], type='http', auth="public", website=True)
    def portal_orders(self, order_id=None, access_token=None, **kw):
        values = {}
        Projects = request.env['order.tag'].sudo().search([])  
        values.update({
            'orders': Projects,
        })
        return request.render('ledpax.add_project', values)

    @http.route(['/my/projects/pdf/<int:order_id>'], type='http', auth="public", website=True)
    def portal_project_report(self, order_id, access_token=None, **kw):
        projects = request.env['order.tag'].browse([order_id])
        project_sudo = projects.sudo()

        pdf = request.env.ref('ledpax.action_report_project').sudo().render_qweb_pdf([project_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)  

    @http.route(['/my/documents'], type='http', auth="public", website=True)
    def document_page_function(self, **kw):
        documents = request.env['res.partner'].sudo().search([('id', '=', request.env.user.partner_id.id)]).documents_url or False
        if not documents:
            return '<h2> No documents for,</h2>' + '<h1 style="color:Tomato;"> &emsp;&emsp;&emsp;' + str(request.env.user.partner_id.name) + ' !! </h1>'
        else:
            return request.redirect(documents)

class PortalAccountInvoice(CustomerPortal):

    @http.route(['/my/project/invoices'], type='http', auth="public", website=True)
    def portal_invoices(self, **kw):
        url_referrer = request.httprequest.referrer
        proj_id = url_referrer.split("/")[5]
        if '?' in proj_id:
            inv_id = proj_id[:-1]
        else:
            inv_id = proj_id        
        inv_proj = int(inv_id)
        partner = request.env.user.partner_id
        proj = request.env['order.tag'].sudo().search([('id','=',inv_proj)])
        proj_name = proj.name        
        values = {}
        invoices = request.env['account.invoice'].sudo().search([('project_so','=',proj_name),('partner_id','=',partner.id)])
        values.update({
            'invoices': invoices,
        })
        return request.render("account.portal_my_invoices", values)

    @http.route(['/my/project/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.invoice', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices', download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        return request.render("account.portal_invoice_page", values)                   
             
class ProjectModel(http.Controller):

    @http.route(route='/my/add_project', csrf=False, type='http', auth="public", methods=['POST'], website=True)
    def ProjectValue_function(self, **kw):
        proj_id = kw['data'].split(',')
        proj_name = proj_id[0]
        order = request.website.sale_get_order()
        order_id = order.id
        Saleorder = request.env['sale.order'].sudo().search([('id','=',order_id)])
        proj = request.env['order.tag'].sudo().search([('name','=',proj_name)])
        Saleorder.update({'project_name':proj})
        s_data = []
        prod = Saleorder.order_line
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
            dic = {'order_name': Saleorder.name,
                    'o_id': proj.id,
                    'partner_name': Saleorder.partner_id.name,
                    'invoice_adrress' : Saleorder.partner_invoice_id.name,
                    'delivery_address' : Saleorder.partner_shipping_id.name,
                    'confirm_date' : Saleorder.confirmation_date,
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
            http.request.env['order.tag.line'].sudo().create(dic)
        return 'Project added successfully'

class SaleStockPortal(CustomerPortal):

    def _stock_picking_check_access(self, picking_id, access_token=None):
        picking = request.env['stock.picking'].browse([picking_id])
        picking_sudo = picking.sudo()
        try:
            picking.check_access_rights('read')
            picking.check_access_rule('read')
        except exceptions.AccessError:
            if not access_token or not consteq(picking_sudo.sale_id.access_token, access_token):
                raise
        return picking_sudo

    @http.route(['/my/picking/pdf/<int:picking_id>'], type='http', auth="public", website=True)
    def portal_my_picking_report(self, picking_id, access_token=None, **kw):
        try:
            picking_sudo = self._stock_picking_check_access(picking_id, access_token=access_token)
        except exceptions.AccessError:
            return request.redirect('/my')

        pdf = request.env.ref('ledpax.action_report_delivery_room').sudo().render_qweb_pdf([picking_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)                  

class Websites(Home):

    @http.route('/', type='http', auth="user", website=True)
    def home_page_function(self, **kw):
        try:
            values = {}
            orders = request.env['sale.order'].sudo().search([['partner_id.name','=',request.env.user.partner_id.name],['state','=','sale']])
            values.update({'orders' : orders})
        except:
            pass
        return request.render("ledpax.home_page_front", {'values': values})

