# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class CustomStockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        cache = {}
        suppliers = product_id.seller_ids \
            .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (
                not r.product_id or r.product_id == product_id))
        if not suppliers:
            msg = _('There is no vendor associated to the product %s. Please define a vendor for this product.') % (
                product_id.display_name,)
            raise exceptions.UserError(msg)
        supplier_list = self._make_po_select_supplier(values, suppliers)
        supplier = self.env['product.supplierinfo']
        ven_price = []
        if len(supplier_list) > 1:
            for supplier_obj in supplier_list:
                ven_price.append(supplier_obj.price)
            ven_price = min(ven_price)
            for supplier_obj in supplier_list:
                if supplier_obj.price == ven_price:
                    supplier = supplier_obj
        else:
            try:
                supplier = supplier_list[0]
            except IndexError:
                msg = _('Vendor associated to the product %s does not have values in required fields.') % (product_id.display_name,)
                raise exceptions.UserError(msg)

        partner = supplier.name
        # we put `supplier_info` in values for extensibility purposes
        values['supplier'] = supplier

        domain = self._make_po_get_domain(values, partner)
        if domain in cache:
            po = cache[domain]
        else:
            po = self.env['purchase.order'].sudo().search([dom for dom in domain])
            po = po[0] if po else False
            cache[domain] = po
        if not po:
            vals = self._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
            company_id = values.get('company_id') and values['company_id'].id or self.env.user.company_id.id
            po = self.env['purchase.order'].with_context(force_company=company_id).sudo().create(vals)
            cache[domain] = po
        elif not po.origin or origin not in po.origin.split(', '):
            if po.origin:
                if origin:
                    po.write({'origin': po.origin + ', ' + origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': origin})

        # Create Line
        po_line = False
        for line in po.order_line:
            if line.product_id == product_id and line.product_uom == product_id.uom_po_id:
                if line._merge_in_existing_line(product_id, product_qty, product_uom, location_id, name, origin,
                                                values):
                    vals = self._update_purchase_order_line(product_id, product_qty, product_uom, values, line, partner)
                    po_line = line.write(vals)
                    break
        if not po_line:
            vals = self._prepare_purchase_order_line(product_id, product_qty, product_uom, values, po, partner)
            self.env['purchase.order.line'].sudo().create(vals)

    def _make_po_select_supplier(self, values, suppliers):
        """ Method intended to be overridden by customized modules to implement any logic in the
            selection of supplier.
        """
        date = fields.Date.today()
        supplier_list = []
        for supplier in suppliers:
            if supplier.date_start and supplier.date_end:
                if supplier.date_start and supplier.date_start > date:
                    continue
                if supplier.date_end and supplier.date_end < date:
                    continue
                supplier_list.append(supplier)
        return supplier_list
    
    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, partner):
        procurement_uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id.with_context(force_company=values['company_id'].id)._select_seller(
            partner_id=partner,
            quantity=procurement_uom_po_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id)

       # Added Type filed of so in po
        if 'move_dest_ids' in values.keys():
            sol_type = values['move_dest_ids'].sale_line_id.type

        elif 'sale_line_id' in values.keys():
            sol_type = self.env['sale.order.line'].search(
                [('id', '=',values['sale_line_id'])]).type
        else:
            sol_type = None

        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == values['company_id'].id)

        vender_price = []
        for l in product_id.seller_ids:
            vender_price.append(l.price) 
        min_price = min(vender_price)
        price_unit = self.env['account.tax']._fix_tax_included_price_company(min_price, product_id.supplier_taxes_id, taxes_id, values['company_id']) if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        product_lang = product_id.with_context({
            'lang': partner.lang,
            'partner_id': partner.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.env['purchase.order.line']._get_date_planned(seller, po=po).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return {
            'name': name,
            'type': sol_type,
            'product_qty': procurement_uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,
            'move_dest_ids': [(4, x.id) for x in values.get('move_dest_ids', [])],
        }
