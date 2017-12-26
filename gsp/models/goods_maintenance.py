# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

# 字段只读状态
READONLY_STATES = {
    'done': [('readonly', True)],
}


class GoodsMaintenance(models.Model):
    _name = "goods.maintenance"
    _description = u"商品养护"

    state = fields.Selection([
        ('draft', u'草稿'),
        ('done', u'已审核'),
        ('cancel', u'已作废')
    ], string=u'状态', readonly=True,
        default='draft', copy=False, index=True)

    date = fields.Datetime(u'养护时间', required=True, default=lambda self: fields.Datetime.now())

    next_date = fields.Datetime(u'下次养护时间')

    goods_id = fields.Many2one('goods',
                               u'商品',
                               ondelete='restrict')

    details = fields.One2many('goods.maintenance.detail', 'order_id', u'养护明细',
                              states=READONLY_STATES,
                              copy=True,
                              help=u'养护明细项，不能为空')

    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())

    @api.multi
    def maintenance_done(self):
        '''审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'done',
        })

    @api.multi
    def maintenance_draft(self):
        '''反审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'draft',
        })


class GoodsMaintenanceDetail(models.Model):
    _name = 'goods.maintenance.detail'
    _description = u'养护明细项目'

    order_id = fields.Many2one('goods.maintenance',
                               u'商品养护',
                               index=True,
                               required=True,
                               ondelete='cascade',
                               help=u'关联商品养护单的编号')

    line_in_id = fields.Many2one('wh.move.line',
                                 u'批次号',
                                 ondelete='restrict',
                                 help=u'商品入库明细')

    quality_issue = fields.Char(u'质量问题', help=u'商品质量问题')

    deal_method = fields.Char(u'处理措施')
