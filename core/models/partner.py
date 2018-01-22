# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from pypinyin import pinyin, Style

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    '''
    业务伙伴可能是客户： c_category_id 非空
    '''
    _name = 'partner'
    _description = u'业务伙伴'
    _inherit = ['mail.thread']

    @api.model
    def _default_partner_type(self):
        '''获取默认类型'''
        return self.env.context.get('type', False)

    state = fields.Selection([
        ('draft', u'未审核'),
        ('done', u'已审核'),
        ('cancel', u'已作废')
    ], string=u'首营审核', readonly=True,
        default='draft', copy=False, index=True,
        help=u'合作伙伴首营审核状态。新建时状态为未审核;审核后状态为已审核')

    code = fields.Char(u'编号')
    name = fields.Char(u'名称', required=True, copy=False)
    pinyin_abbr = fields.Char(u'拼音简码')

    contract_number = fields.Char(u'合同编号')
    area = fields.Char(u'区域分类')

    distribute_code = fields.Char(u'线路编号')
    distribute_route = fields.Char(u'配送线路')
    distribute_distance = fields.Integer(u'配送里程')
    distribute_sequence = fields.Char(u'线路排序号')

    main_contact = fields.Char(u'主联系人')
    main_address = fields.Char(u'详细地址')
    main_mobile = fields.Char(u'联系电话', size=20)

    post_company = fields.Char(u'托运公司')
    pickup_contact = fields.Char(u'收货人')
    pickup_address = fields.Char(u'收货地址')
    pickup_mobile = fields.Char(u'收货联系电话', size=20)
    pickup_note = fields.Char(u'交货备注')

    fax = fields.Char(u'传真')
    postcode = fields.Char(u'邮编')

    business_scope = fields.Many2many('core.value',
                                      string=u'经营范围',
                                      domain=[('type', '=', 'goods_scope')],
                                      context={'type': 'goods_scope'})

    c_category_id = fields.Many2one('core.category', u'客户类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'customer')],
                                    context={'type': 'customer'})
    s_category_id = fields.Many2one('core.category', u'供应商类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'supplier')],
                                    context={'type': 'supplier'})
    type = fields.Selection([
        ('MNF', u'生产企业'),
        ('SUP', u'供应商'),
        ('CUS', u'客户'),
    ], default=_default_partner_type, string=u'业务伙伴类型')

    receivable = fields.Float(u'应收余额', readonly=True,
                              digits=dp.get_precision('Amount'))
    payable = fields.Float(u'应付余额', readonly=True,
                           digits=dp.get_precision('Amount'))
    tax_num = fields.Char(u'税务登记号')
    tax_rate = fields.Float(u'税率(%)', help=u'业务伙伴税率')
    bank_name = fields.Char(u'开户行')
    bank_num = fields.Char(u'银行账号')
    pay_method = fields.Many2one('settle.mode', string=u'付款方式',
                                 ondelete='restrict', track_visibility='onchange',
                                 help=u'付款方式：支票、信用卡、现金、月付等')

    credit_limit = fields.Float(u'信用额度', track_visibility='onchange',
                                help=u'客户购买商品时，本次发货金额+客户应收余额要小于客户信用额度')
    active = fields.Boolean(u'启用', default=True)
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())
    tag_ids = fields.Many2many('core.value',
                               string=u'标签',
                               domain=[('type', '=', 'partner_tag')],
                               context={'type': 'partner_tag'})
    source = fields.Char(u'来源')
    note = fields.Text(u'备注')

    responsible_id = fields.Many2one('res.users', u'负责人员', default=lambda self: self.env.user)

    onsite_check = fields.Boolean(u'需要实地考察')

    cert_ids = fields.One2many('partner.cert.info', 'partner_id', string=u'合作伙伴认证信息')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', '业务伙伴不能重名')
    ]

    @api.onchange('name')
    def onchange_name(self):
        """
        :return: 修改名称时候，生成拼音简码
        """
        if self.name:
            # 只获取首字母拼音 [['z'], ['x']]
            abbrs = pinyin(self.name, style=Style.FIRST_LETTER)
            self.pinyin_abbr = ''.join([item[0].upper() for item in abbrs])

    @api.multi
    def partner_done(self):
        '''合作伙伴的审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'done',
        })

    @api.multi
    def partner_draft(self):
        '''合作伙伴的反审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'draft',
        })

    @api.onchange('type')
    def onchange_type(self):
        """
        :return: 根据type调整c_category_id 和 s_category_id
        """
        if self.type == 'MNF':
            self.c_category_id = None
            self.s_category_id = None
        elif self.type == 'SUP':
            self.c_category_id = None
        elif self.type == 'CUS':
            self.s_category_id = None

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        在many2one字段中支持按编号搜索
        """
        args = args or []
        if name:
            args.append(('code', 'ilike', name))
            partners = self.search(args)
            if partners:
                return partners.name_get()
            else:
                args.remove(('code', 'ilike', name))
        return super(Partner, self).name_search(name=name,
                                                args=args,
                                                operator=operator,
                                                limit=limit)

    @api.multi
    def action_view_buy_history(self):
        '''
        This function returns an action that display buy history of given sells order ids.
        Date range [180 days ago, now]
        '''
        self.ensure_one()
        date_end = datetime.today()
        date_start = datetime.strptime(self.env.user.company_id.start_date, '%Y-%m-%d')

        if (date_end - date_start).days > 365:
            date_start = date_end - timedelta(days=365)

        buy_order_track_wizard_obj = self.env['buy.order.track.wizard'].create({'date_start': date_start,
                                                                                'date_end': date_end,
                                                                                'partner_id': self.id})

        return buy_order_track_wizard_obj.button_ok()

    @api.multi
    def write(self, vals):
        # 业务伙伴应收/应付余额不为0时，不允许取消对应的客户/供应商身份
        if self.type == 'CUS' and vals.get('type') == False and self.receivable != 0:
            raise UserError(u'该客户应收余额不为0，不能取消客户类型')
        if self.type == 'SUP' and vals.get('type') == False and self.payable != 0:
            raise UserError(u'该供应商应付余额不为0，不能取消供应商类型')
        return super(Partner, self).write(vals)
