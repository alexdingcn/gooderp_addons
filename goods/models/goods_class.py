# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class GoodsClass(models.Model):
    _name = "goods.class"
    _description = u"商品分类"
    _order = "sequence, name"

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValueError(u'错误 ! 您不能创建循环分类')

    name = fields.Char(required=True, string=u'名字')
    parent_id = fields.Many2one('goods.class', string=u'上级分类', index=True)
    child_ids = fields.One2many('goods.class', 'parent_id', string=u'子分类')
    sequence = fields.Integer(u'显示顺序(越小越靠前)')
    note = fields.Text(u'备注')

    image = fields.Binary(attachment=True)
    image_medium = fields.Binary(string="Medium-sized image", attachment=True)
    image_small = fields.Binary(string="Small-sized image", attachment=True)

    @api.multi
    def view_detail(self):
        for item in self:
            res_id = self.env['goods.class'].search([('id', '=', item.id)])
            view_id = self.env.ref('goods.goods_class_form_view').id

            return {
                'name': u'商品分类/' + item.name,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'goods.class',
                'res_id': res_id.id,
                'view_id': False,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }