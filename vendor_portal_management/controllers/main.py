import base64
import logging
from collections import OrderedDict

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import image_resize_image
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.web.controllers.main import Binary
# from odoo.addons.portal.controllers.web import Home
from odoo.addons.portal.controllers.mail import _message_post_helper

_logger = logging.getLogger(__name__)


class VendorPortal(http.Controller):

    def _prepare_portal_layout_values(self):
        values = super(VendorPortal, self)._prepare_portal_layout_values()
        values['vendor_count'] = request.env['vendor.portal'].search_count([
        ])
        return values

    @http.route(['/my/rfq','/my/rfq/page/<int:page>'], type='http', auth='user', website=True)
    def rfq_details(self , **kwargs):
        rfq_details = request.env['vendor.portal'].sudo().search([])
        return  request.render('vendor_portal_management.rfq_details_page', {'my_details': rfq_details})

    @http.route('/my/rfq/<int:rfq_id>', type='http', auth="user", website=True)
    def rfq_page_details(self, rfq_id=None, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = {}
        partner = request.env.user.partner_id
        VendorPortal = request.env['vendor.portal'].sudo().search([('id','=',rfq_id)])  
        values.update({
            'orders': VendorPortal,
        })
        return request.render('vendor_portal_management.rfq_detail_page_view', {'values': values})

    @http.route(['/my/rfq/submit/price/<int:rfq_id>/<int:line_id>'], type='http', auth="public", website=True)
    def decline(self, rfq_id, line_id, access_token=None, **post):
        _logger.error(post)
        try:
            order_sudo = self._document_check_access('vendor.portal', rfq_id, access_token=access_token)
            _logger.error(line_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        request.env['purchase.order.line'].browse([line_id]).write({'price_unit': post.get('price')})

        return request.redirect("/my/rfq/" + str(rfq_id))
        