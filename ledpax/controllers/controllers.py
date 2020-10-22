# -*- coding: utf-8 -*-
from odoo import http

# class Ledpax(http.Controller):
#     @http.route('/ledpax/ledpax/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ledpax/ledpax/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ledpax.listing', {
#             'root': '/ledpax/ledpax',
#             'objects': http.request.env['ledpax.ledpax'].search([]),
#         })

#     @http.route('/ledpax/ledpax/objects/<model("ledpax.ledpax"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ledpax.object', {
#             'object': obj
#         })