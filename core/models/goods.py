# -*- coding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError

CORE_COST_METHOD = [('average', u'全月一次加权平均法'),
                    ('std', u'定额成本'),
                    ('fifo', u'先进先出法'),
                    ]


class Goods(models.Model):
    _name = 'goods'
    _description = u'商品'

    @api.model
    def _get_default_not_saleable_impl(self):
        return False

    @api.model
    def _get_default_not_saleable(self):
        return self._get_default_not_saleable_impl()

    @api.multi
    def name_get(self):
        '''在many2one字段里显示 编号_名称'''
        res = []

        for Goods in self:
            # name = Goods.code and (Goods.code + '_' + Goods.name) or Goods.name
            name = Goods.name
            if Goods.specs:
                name += '[%s]' % Goods.specs
            if Goods.supplier_id.name:
                name += ' - %s' % Goods.supplier_id.name
            res.append((Goods.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        '''在many2one字段中支持按拼音搜索'''
        if not name or len(name) < 2:
            return []
        args = args or []
        code_search_goods = []
        if name:
            args.append(('pinyin_abbr', 'ilike', name))
            goods_ids = self.search(args)
            if goods_ids:
                code_search_goods = goods_ids.name_get()

            args.remove(('pinyin_abbr', 'ilike', name))
        search_goods = super(Goods, self).name_search(name=name, args=args,
                                                      operator=operator, limit=limit)
        for good_tup in code_search_goods:  # 去除重复产品
            if good_tup not in search_goods:
                search_goods.append(good_tup)
        return search_goods

    @api.model
    def create(self, vals):
        '''导入商品时，如果辅助单位为空，则用计量单位来填充它'''
        if not vals.get('uos_id'):
            vals.update({'uos_id': vals.get('uom_id')})
        return super(Goods, self).create(vals)

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.has_key('name'):
            default.update(name=_('%s (copy)') % (self.name))
        return super(Goods, self).copy(default=default)

    code = fields.Char(u'商品编号')
    name = fields.Char(u'通用名称', required=True, copy=False)
    category_id = fields.Many2one('core.category', u'核算类别',
                                  ondelete='restrict',
                                  domain=[('type', '=', 'goods')],
                                  context={'type': 'goods'}, required=True,
                                  help=u'从会计科目角度划分的类别')
    uom_id = fields.Many2one('uom', ondelete='restrict', string=u'包装单位')
    uos_id = fields.Many2one('uom', ondelete='restrict', string=u'计量单位')
    conversion = fields.Float(string=u'计量规格', default=1, digits=(16, 2),
                              help=u'1个计量单位等于多少包装单位，如1箱30盒药品，这里就输入30')

    cost = fields.Float(u'成本', digits=dp.get_precision('Amount'))
    cost_method = fields.Selection(CORE_COST_METHOD, u'存货计价方法',
                                   help=u'仓库模块使用先进先出规则匹配, 每次出库对应的入库成本和数量，但不实时记账。财务月结时使用此方法相应调整发出成本')

    tax_rate = fields.Float(u'税率(%)', help=u'商品税率')
    not_saleable = fields.Boolean(u'不可销售',
                                  default=_get_default_not_saleable,
                                  help=u'商品是否不可销售，勾选了就不可销售，未勾选可销售')
    active = fields.Boolean(u'启用', default=True)

    company_id = fields.Many2one(
        'res.company',
        string=u'生产企业',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())
    brand = fields.Many2one('core.value', u'品牌/注册商标',
                            ondelete='restrict',
                            domain=[('type', '=', 'brand')],
                            context={'type': 'brand'})

    origin = fields.Char(u'产地', help=u'商品产地')

    _sql_constraints = [
        ('name_uniq', 'unique(name, code)', '商品不能重名'),
        ('conversion_no_zero', 'check(conversion != 0)', '商品的转化率不能为0')
    ]

    @api.model
    def get_warehouse_balance(self, goods_id):
        # get warehouse
        query = """ SELECT goods.name as goods,
                       goods.id as goods_id,
                       wh.id as warehouse_id,
                       wh.name as warehouse,
                       sum(line.qty_remaining) as goods_qty,
                       sum(line.qty_remaining * line.cost_unit) as cost
                FROM wh_move_line line
                    LEFT JOIN warehouse wh ON line.warehouse_dest_id = wh.id
                    LEFT JOIN goods goods ON line.goods_id = goods.id
                WHERE wh.type = 'stock'
                  AND line.state = 'done'
                  AND (goods.no_stock is null or goods.no_stock = FALSE)
                  AND goods_id=%s and line.qty_remaining > 0
                GROUP BY wh.id, goods.id """ % goods_id
        self.env.cr.execute(query)

        return self.env.cr.dictfetchall()
