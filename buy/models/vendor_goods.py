# -*- coding: utf-8 -*-
import datetime
import logging

import odoo
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class VendorGoods(models.Model):
    _name = 'vendor.goods'
    _description = u'供应商供货价格表'
    _order = 'last_buy_time desc'

    goods_id = fields.Many2one(
        string=u'商品',
        required=True,
        comodel_name='goods',
        ondelete='cascade',
        help=u'商品',
    )

    vendor_id = fields.Many2one(
        string=u'供应商',
        required=True,
        comodel_name='partner',
        domain=[('type', '=', 'SUP'), ('state', '=', 'done')],
        ondelete='cascade',
        help=u'供应商',
    )

    price = fields.Float(u'协议供货价',
                         digits=dp.get_precision('Price'),
                         help=u'供应商提供的价格')

    min_price = fields.Float(u'最低价',
                             digits=dp.get_precision('Price'),
                             help=u'供应商提供的最低价格')
    max_price = fields.Float(u'最高价',
                             digits=dp.get_precision('Price'),
                             help=u'供应商提供的最高价格')
    last_price = fields.Float(u'最近价',
                              digits=dp.get_precision('Price'),
                              help=u'供应商最后一次的价格')
    last_buy_time = fields.Datetime(u'最后进货时间')

    code = fields.Char(u'供应商商品编号',
                       help=u'供应商提供的商品编号')

    name = fields.Char(u'供应商商品名称',
                       help=u'供应商提供的商品名称')

    min_qty = fields.Float(u'最低订购量',
                           digits=dp.get_precision('Quantity'), default=1,
                           help=u'采购商品时，大于或等于最低订购量时，商品的价格才取该行的供货价')

    total_qty = fields.Float(u'总采购量', digits=dp.get_precision('Quantity'))

    subtotal = fields.Float(u'总采购金额', digits=dp.get_precision('Amount'))

    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())

    _sql_constraints = [
        ('unique_vendor_goods', 'unique(vendor_id, goods_id)', u'供应商-商品关系要求唯一!'),
    ]

    @api.model
    def _calc_stats(self):
        """ This Function is called by scheduler. """
        # TODO: use more efficient way to update
        _logger.info("Start calculate vendor goods data")
        newids = []
        # 从审核过的订单中统计最小最大
        query = """ SELECT o.partner_id, bol.goods_id, 
                      sum(bol.quantity) as total_quantity,
                      sum(bol.subtotal) as subtotal, 
                      min(bol.price_taxed) as min_price, 
                      max(bol.price_taxed) as max_price
                    FROM buy_order o, buy_order_line bol
                    WHERE o.id = bol.order_id
                    AND o.state='done'
                    GROUP BY o.partner_id, bol.goods_id """
        self.env.cr.execute(query)

        for partner_id, goods_id, total_quantity, subtotal, min_price, max_price in self.env.cr.fetchall():
            try:
                values = {
                    'vendor_id': partner_id,
                    'goods_id': goods_id,
                    'company_id': self.env.user.company_id.id,
                    'total_qty': total_quantity,
                    'subtotal': subtotal,
                    'min_price': min_price,
                    'max_price': max_price
                }
                old_record = self.search([('goods_id', '=', goods_id), ('vendor_id', '=', partner_id)], limit=1)
                if old_record:
                    old_record.write(values)
                else:
                    newids.append(self.create(values))
            except Exception, e:
                _logger.error(odoo.tools.exception_to_unicode(e))
                raise

        # 统计最近的订单
        query = """ SELECT ab.partner_id, ab.goods_id, ol.price_taxed as last_price, ol.write_date as last_write_date
            FROM buy_order_line as ol, (SELECT  o.partner_id, bol.goods_id, max(bol.id) as maxid
                                FROM buy_order o, buy_order_line bol
                                WHERE o.id = bol.order_id
                                AND o.state='done'
                                GROUP BY o.partner_id, bol.goods_id) as ab
            WHERE ol.id = ab.maxid """
        self.env.cr.execute(query)

        for partner_id, goods_id, last_price, last_buy_time in self.env.cr.fetchall():
            try:
                self.env.cr.execute(
                    "UPDATE %s SET last_price='%s', last_buy_time='%s' WHERE vendor_id=%s and goods_id=%s"
                    % (self._table, last_price, last_buy_time, partner_id, goods_id))
            except Exception, e:
                _logger.error(odoo.tools.exception_to_unicode(e))
                raise

        self.env.cr.commit()

        return newids


class Partner(models.Model):
    _inherit = 'partner'

    goods_ids = fields.One2many(
        string=u'供应商品',
        comodel_name='vendor.goods',
        inverse_name='vendor_id',
        help=u'供应商供应的商品价格列表',
    )


class Goods(models.Model):
    _inherit = 'goods'

    vendor_ids = fields.One2many(
        string=u'供应价格',
        comodel_name='vendor.goods',
        inverse_name='goods_id',
        help=u'各供应商提供的基于最低订购量的供货价格列表',
    )
