from odoo import api, fields, models
from odoo.exceptions import ValidationError
import sys
import base64
import os
import pandas as pd

class CreateProductExcel(models.TransientModel):
    _name = 'product.tmpl.excel.wizard'
    _description = 'Create Product Template through Excel'

    excel_file = fields.Binary('Upload Excel File', attchment=True)

    def submit(self):
        try:
            if self.excel_file :
                # file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + 'create_prod_wizard' + '.xlsx'
                file_path = 'src/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + 'create_prod_wizard' + '.xlsx'                
                code = self.excel_file
                with open(os.path.expanduser(file_path), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file_path, 0o777)

                excel = pd.ExcelFile(file_path)
                for sheet in excel.sheet_names:
                    dataframe = pd.read_excel(file_path, sheet_name=sheet)
                    c = []
                    col = dataframe.columns
                    for i in col:
                        c.append(i)
                    df = dataframe.rename(columns={c[0] : 'Ids',
                        c[1] : 'Product Name', 
                        c[2] : 'Category',
                        c[3] : 'Attribute Short Code', 
                        c[4] : 'Description',
                        c[5] : 'Warehouse',
                        c[6] : 'Location',
                        c[7] : 'Bin',
                        c[8] : 'Quantity',
                        c[9] : 'Expiration Date', 
                        c[10] : 'Multi Customer SKU', 
                        c[11] : 'Price',
                        c[12] : 'Currency',
                        c[13] : 'Default Supplier',
                        })

                    for row in range(df.shape[0]):
                        if str(df['Product Name'][row]) != 'nan':
                            product_name = df['Product Name'][row]
                        else:
                            raise ValidationError(f'Provide product name at row {row}.')
                        product_exist = self.env['product.template'].search([('name', '=', product_name)]) or False
                        if not product_exist:
                            product_type = 'product'
                            if str(df['Category'][row]) != 'nan':
                                product_category = self.env['product.category'].search([('complete_name', '=', df['Category'][row])]).id
                                if not product_category:
                                    raise ValidationError(f'Provided product category at row {row} does not exist in system.')
                            else:
                                raise ValidationError(f'Provide product category at row {row}.')
                            attribute_line_ids = []
                            try:
                                if str(df['Attribute Short Code'][row]) != 'nan':
                                    attribute_short_code = str(df['Attribute Short Code'][row])
                                    for attribute_value_pair in attribute_short_code.split(';'):
                                        attribute_values = attribute_value_pair.split(':')
                                        attribute = attribute_values[0]
                                        attributeId = self.env['product.attribute'].search([('name', '=', attribute.strip())]).id or False
                                        if not attributeId:
                                            raise ValidationError(f'Attribute "{attribute}" at row {row} does not exist in system.')
                                        valueIds = []
                                        values = attribute_values[1]
                                        for value in values.split(','):
                                            valueId = self.env['product.attribute.value'].search([('code', '=', value.strip())]).id or False
                                            if not valueId:
                                                raise ValidationError(f'Attribute Value Short Code "{value}" at row {row} does not exist in system.')
                                            valueIds.append(valueId)
                                        attribute_line_ids.append((0, 0, {'attribute_id': attributeId,'value_ids': [(6, 0, valueIds)]}))
                            except:
                                print("Unexpected Error:", sys.exc_info())
                                raise ValidationError(f'Unexpected Attribute Short Code format at row {row}.')
                            if str(df['Description'][row]) != 'nan':
                                description = df['Description'][row]
                                description_sale = df['Description'][row]
                                description_purchase = df['Description'][row]
                            else :
                                description = ''
                                description_sale = ''
                                description_purchase = ''
                            if str(df['Bin'][row]) != 'nan':
                                binId = self.env['stock.location'].search([('name', '=', str(df['Bin'][row]).strip())]).id or False
                                if not binId:
                                    if str(df['Location'][row]) != 'nan':
                                        locationId = self.env['stock.location'].search([('name', '=', str(df['Location'][row]).strip())]).id or False
                                        if not locationId:
                                            if str(df['Warehouse'][row]) != 'nan':
                                                warehouseId = self.env['stock.location'].search([('name', '=', str(df['Warehouse'][row]).strip()[:5])]).id or False
                                                if not warehouseId:
                                                    warehouse = self.env['stock.warehouse'].create({
                                                        'name' : str(df['Warehouse'][row]),
                                                        'code' : str(df['Warehouse'][row])[:5]
                                                        }).id
                                                    warehouseId = self.env['stock.location'].search([('name', '=', str(df['Warehouse'][row]).strip()[:5])]).id
                                            else:
                                                raise ValidationError(f'Provide product warehouse location at row {row}.')
                                            locationId = self.env['stock.location'].create({
                                                'name' : str(df['Location'][row]),
                                                'usage': 'internal',
                                                'location_id' : warehouseId
                                                }).id
                                    else:
                                        raise ValidationError(f'Provide product location at row {row}.')
                                    binId = self.env['stock.location'].create({
                                        'name' : str(df['Bin'][row]),
                                        'usage': 'internal',
                                        'location_id' : locationId
                                        }).id
                            else :
                                raise ValidationError(f'Provide product bin location at row {row}.')
                            if str(df['Quantity'][row]) != 'nan':
                                product_quantity = df['Quantity'][row]
                            else:
                                product_quantity = 0
                            if str(df['Price'][row]) != 'nan':
                                product_sale_price = df['Price'][row]
                            else:
                                product_sale_price = 0.00
                            if str(df['Multi Customer SKU'][row]) != 'nan':
                                default_code = str(df['Multi Customer SKU'][row])
                            else:
                                default_code = ''

                            part_number_index = self.env['product.template'].search_count([])
                            product_template = self.env['product.template'].create({
                                'name' : product_name,
                                'type' : product_type,
                                'categ_id' : product_category,
                                'prod_description' : description,
                                'list_price' : product_sale_price,
                                'default_code': default_code,
                                'part_number_index': format(part_number_index + 1, '08'),
                                'attribute_line_ids' : attribute_line_ids
                                })
                            products = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)])
                            line_ids = []
                            for product in products:
                                line_ids.append((0, 0, {
                                    'product_id': product.id,
                                    'product_qty': product_quantity,
                                    'location_id': binId
                                    }))
                            inventory = self.env['stock.inventory'].create({
                                'name': 'Inventory For Product' + product_template.name,
                                'filter': 'partial',
                                'line_ids': line_ids
                                })
                            inventory.action_start()
                            inventory.action_validate()
                os.remove(file_path)
        except:
            print("Unexpected Error:", sys.exc_info())
            raise ValidationError('Selected file is not Excel supported. Upload Excel file.')