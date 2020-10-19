# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, http, models
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager


class OrderTag(CustomerPortal):
    _inherit = "sale.order"

    @http.route(['/my/orders/project', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_order_tag_project(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = {}
        partner = request.env.user.partner_id
        SaleOrder = request.env['order.tag'].sudo().search([]) 
        values.update({
            'orders': SaleOrder,
        })
        return request.render("ledpax.order_tag_project", values)