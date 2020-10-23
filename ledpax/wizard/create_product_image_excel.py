from odoo import api, fields, models
from odoo.exceptions import ValidationError
import sys
import base64
import os
from PIL import Image
import requests
from io import BytesIO
import io
import pandas as pd

class CreateProductImageExcel(models.TransientModel):
    _name = 'product.tmpl.image.excel.wizard'
    _description = 'Create Product Template Image through Excel'

    excel_file = fields.Binary('Upload Excel File', attchment=True)

    def submit(self):
        try:
            if self.excel_file :
                # file_path = '/home/odoo12_entrp/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + 'create_prod_image_wizard' + '.xlsx'
                file_path = 'src/Downloads/Ledpax_Excel_Data/Vendor_Excel/' + 'create_prod_image_wizard' + '.xlsx'                
                code = self.excel_file
                with open(os.path.expanduser(file_path), 'wb') as fout:
                    fout.write(base64.decodestring(code))
                    os.chmod(file_path, 0o777)
                dataframe = pd.read_excel(file_path)
                for row in range(dataframe.shape[0]):
                    product_image = False
                    for col in dataframe.columns:
                        if str(col) == "Master SKU":
                            if str(dataframe[col][row]) != 'nan':
                                product_name = str(dataframe[col][row])
                                product_tmpl_id = self.env['product.template'].search([('name', '=', product_name)]).id or False
                                if not product_tmpl_id:
                                    product_tmpl_id = self.env['product.template'].create({
                                        'name' : product_name,
                                        'type' : 'product',
                                        }).id
                                self.env['product.image'].search([('product_tmpl_id', '=', product_tmpl_id)]).unlink()
                            else:
                                raise ValidationError(f'Provide Master SKU at row {row}.')
                        elif str(col) == "UPC SET 1":
                            pass
                        else:
                            if str(dataframe[col][row]) != 'nan':
                                img = str(dataframe[col][row])
                                response = requests.get(img)
                                image = Image.open(BytesIO(response.content))
                                imgByteArr = io.BytesIO()
                                image.save(imgByteArr, format='PNG')
                                imgByteArr = imgByteArr.getvalue()
                                images = base64.b64encode(imgByteArr)
                                if product_image:
                                    self.env['product.image'].create({'product_tmpl_id' : product_tmpl_id ,
                                        'name' : product_name + '_' + str(col),
                                        'image' : images })
                                else:
                                    self.env['product.template'].browse(product_tmpl_id).write({'image_medium' : images })
                                    product_image = True
                os.remove(file_path)
        except:
            print("Unexpected Error:", sys.exc_info())
            raise ValidationError('Selected file is not Excel supported. Upload Excel file.')