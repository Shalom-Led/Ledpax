# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Purchase(models.Model):
    _inherit = "purchase.order"

    def has_to_be_signed(self, also_in_draft=False):
        return (self.state == 'sent' or (self.state == 'draft' and also_in_draft)) and not self.is_expired and self.require_signature and not self.signature and self.team_id.team_type != 'website'

class res_partner(models.Model):
    _inherit = 'res.partner'

    make_portal_user = fields.Integer(string = "Make Portal User")

class WebsiteMenuCustom(models.Model):

    _inherit = 'website.menu'

    @api.one
    def _compute_visible(self):
        super()._compute_visible()
        c_user = self.env.user.id
        current_user = self.env['res.users'].browse(c_user)
        user_group = self.pool.get('res.users').has_group(current_user,'base.group_system')
        for i in self:
            if i.name == "Vendor RFQs":
                current_user.create_uid
                if current_user.partner_id.supplier == True or user_group == True:
                    self.is_visible = True
                else:
                    self.is_visible = False
            else:
                self.is_visible = True       