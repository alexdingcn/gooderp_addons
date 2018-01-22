# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class GoodsQuality(models.Model):
    _name = 'goods.quality'
    _description = u'商品质量'

    @api.multi
    def name_get(self):
        '''在many2one字段里显示 编号_名称'''
        res = []
        if self.goods_id:
            name = self.goods_id.code and (self.goods_id.code + '_' + self.goods_id.name) or self.goods_id.name
            name += self.goods_id.specs and ('[' + self.goods_id.specs + ']')
            res.append((self.goods_id.id, name))
        return res

    @api.one
    @api.depends('goods_qty', 'accept_qty', 'reject_qty')
    def _get_checking_status(self):
        self.state = 'done' if self.goods_qty - self.accept_qty - self.reject_qty == 0 else 'draft'

    def update_warehouse_move_qc_status(self):
        if self.move_id and self.move_id.quality_ids:
            total_num = accept_total = reject_total = 0
            for line in self.move_id.quality_ids:
                total_num += line.goods_qty
                if line.state == 'done':
                    accept_total += line.accept_qty
                    reject_total += line.reject_qty

            if reject_total == total_num:
                qc_result_brief = '质检全部拒收'
            elif accept_total == total_num:
                qc_result_brief = '质检全部通过'
            elif 0 < accept_total < total_num:
                qc_result_brief = '质检部分通过'
            elif 0 < reject_total < total_num:
                qc_result_brief = '质检部分拒收'

            self.move_id.write({
                'qc_result_brief': qc_result_brief,
                'qc_user_id': self.create_uid.id
            })

    @api.one
    def accept_all(self):
        if self.goods_id:
            self.accept_qty = self.goods_qty
            self.reject_qty = 0
            self.update_warehouse_move_qc_status()

    @api.one
    def reject_all(self):
        if self.goods_id:
            self.reject_qty = self.goods_qty
            self.goods_reject_reason = '质检全部拒收'
            self.accept_qty = 0
            self.update_warehouse_move_qc_status()

    name = fields.Char(u'描述', help=u'描述')

    move_id = fields.Many2one('wh.move', string=u'移库单', ondelete='cascade',
                              help=u'出库/入库/移库单行对应的移库单')

    goods_id = fields.Many2one('goods',
                               u'商品',
                               ondelete='restrict')

    date = fields.Datetime(u'检验时间')

    line_in_id = fields.Many2one('wh.move.line', u'入库明细',
                                 help=u'入库质检单对应的入库明细')

    goods_qty = fields.Float(u'到货数量',
                             digits=dp.get_precision('Quantity'),
                             default=1,
                             required=True,
                             help=u'商品的数量')

    lot = fields.Char(u'批号', help=u'该单据行对应的商品的批号')
    location_id = fields.Many2one('location', string='库位', track_visibility='onchange')

    accept_qty = fields.Float(u'收货数量',
                              digits=dp.get_precision('Quantity'),
                              default=0,
                              required=True)
    reject_qty = fields.Float(u'拒收数量',
                              digits=dp.get_precision('Quantity'),
                              default=0,
                              required=True)
    goods_reject_reason = fields.Char(u'拒收理由', help=u'商品拒收理由')

    question_qty = fields.Float(u'存疑数量',
                                digits=dp.get_precision('Quantity'),
                                default=0,
                                required=True,
                                help=u'商品的数量')
    note = fields.Char(u'备注')

    state = fields.Char(u'状态', compute=_get_checking_status, store=True)

    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())

    _sql_constraints = [
        ('goods_quality_uniq', 'unique(move_id,line_in_id)', u'入/出库单对应的质检单必须唯一'),
    ]
