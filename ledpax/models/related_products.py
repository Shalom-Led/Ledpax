from odoo import models, fields, api


class Review(models.Model):
    _name = 'product.related'
    _description = "Product Related"

    # name = fields.Char('name')
    name = fields.Many2one('product.template', string='Product Name')
    # project = fields.Many2one('project.project',
    #                           string='Project',
    #                           default=lambda self: self.env.context.get('default_project_id'),
    #                           index=True,
    #                           track_visibility='onchange',
    #                           change_default=True)
    cost = fields.Float(string="Cost",compute='_compute_cost')
    product_type = fields.Selection([('Downlight', 'DL'),('Adjustable Angle', 'AA')],
                                    string="Type")

    @api.depends('name')
    def _compute_cost(self):
        prod_id = []
        for rec in self:
            prod_id.append(rec.name.id)
           
        if not (False in prod_id):
            if prod_id:
                product = self.env['product.template'].search([('id','in', prod_id)])
            else:
                product = self.env['product.template'].search([('id','=', self.id)])
            for rec in self:
                for prod in product:
                    if rec.name.name == prod.name:
                        rec.cost = prod.standard_price
                    else:
                        continue