# -*- coding: utf-8 -*-

from odoo import models, fields, api

class new_quot(models.Model):
    # _name = 'new_quot.new_quot'
    _inherit = "sale.order.line"

    type = fields.Char(string='Type')
