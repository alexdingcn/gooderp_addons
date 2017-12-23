# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
from odoo import models, fields, api


class Goods(models.Model):
    '''
    继承了core里面定义的goods 模块，并定义了视图和添加字段。
    '''
    _name = 'goods'
    _inherit = ['goods', 'mail.thread']

    state = fields.Selection([
        ('draft', u'未审核'),
        ('done', u'已审核'),
        ('cancel', u'已作废')
    ], string=u'首营审核', readonly=True,
        default='draft', copy=False, index=True,
        help=u'商品首营审核状态。新建时状态为未审核;审核后状态为已审核')

    english_name = fields.Char(u'外文名')
    pinyin_abbr = fields.Char(u'拼音简码')
    specs = fields.Char(u'规格')
    description = fields.Char(u'商品名称', required=True)

    check_first_documents = fields.Boolean(u'检查首营档案', default=True)
    special_managed = fields.Boolean(u'特殊管理商品')
    digital_audited = fields.Boolean(u'是否有电子监管码')
    digital_audit_code = fields.Char(u'电子监管码')
    need_maintained = fields.Boolean(u'是否需要养护')
    need_quality_report = fields.Boolean(u'需要质检报告')
    is_superiority = fields.Boolean(u'是否优势品种')

    expire_date = fields.Date(u'有效期', default=fields.Date.context_today,
                              help=u'药品有效期, 默认为当前天')
    incoming_tax_rate = fields.Float(u'进项税率')
    outgoing_tax_rate = fields.Float(u'销项税率')
    licence_number = fields.Char(u'批准文号/进口注册证号')

    storage_condition = fields.Many2one('core.value', u'储藏条件', required=True,
                                        ondelete='restrict',
                                        domain=[('type', '=', 'storage_type')],
                                        context={'type': 'storage_type'})
    storage_description = fields.Char(u'储藏条件描述')
    storage_position = fields.Char(u'默认货位号')
    warehouse_comment = fields.Char(u'入库验收')

    contact_info = fields.Char(u'联系方式')

    brand_number = fields.Char(u'档案号')
    main_function = fields.Text(u'主治功能')
    sale_policy = fields.Char(u'销售政策')
    big_category = fields.Char(u'大分类属性')
    special_manage_category = fields.Char(u'特殊管理属性')
    prescription = fields.Char(u'处方/非处方')
    foreign_medicine = fields.Boolean(u'进口药')
    administration_route = fields.Char(u'给药用途')
    functional_category = fields.Char(u'功能分类')
    profit_prop = fields.Char(u'利润属性')
    social_security = fields.Char(u'社保属性')
    traditional_medicine = fields.Char(u'中西药属性')
    maintenance_prop = fields.Char(u'养护属性')
    formulation = fields.Char(u'剂型')
    gmp_certified = fields.Boolean(u'GMP认证')
    business_scope = fields.Char(u'经营范围')
    abc_category = fields.Char(u'ABC分类属性')
    essential_medicine = fields.Char(u'基药属性')

    no_stock = fields.Boolean(u'虚拟商品')

    using_batch = fields.Boolean(u'管理批号', default=True, help=u'默认医药商品都需要批号管理')
    force_batch_one = fields.Boolean(u'管理序列号')

    attribute_ids = fields.One2many('attribute', 'goods_id', string=u'属性')
    image = fields.Binary(u'图片', attachment=True)
    supplier_id = fields.Many2one('partner',
                                  u'生产企业',
                                  ondelete='restrict',
                                  domain=[('type', '=', 'MNF')])
    price = fields.Float(u'零售价')
    barcode = fields.Char(u'条形码')
    note = fields.Text(u'备注')
    goods_class_id = fields.Many2one(
        'goods.class', string=u'商品分类',
        help="选择商品分类")

    cert_ids = fields.One2many('goods.cert.info', 'goods_id', string=u'商品认证信息')

    _sql_constraints = [
        ('barcode_uniq', 'unique(barcode)', u'条形码不能重复'),
    ]

    @api.multi
    def goods_done(self):
        '''商品的审核按钮'''
        self.ensure_one()

        if self.check_first_documents:
            if not self.licence_number or len(self.cert_ids) == 0:
                raise UserError(u'请配置商品批准文号')

        return self.write({
            'state': 'done',
        })

    @api.multi
    def goods_draft(self):
        '''商品的反审核按钮'''
        self.ensure_one()

        return self.write({
            'state': 'draft',
        })

    @api.onchange('uom_id')
    def onchange_uom(self):
        """
        :return: 当选取单位时辅助单位默认和 单位相等。
        """
        self.uos_id = self.uom_id

    @api.onchange('using_batch')
    def onchange_using_batch(self):
        """
        :return: 当将管理批号的勾去掉后，自动将管理序列号的勾去掉
        """
        if not self.using_batch:
            self.force_batch_one = False

    def conversion_unit(self, qty):
        """ 数量 × 转化率 = 辅助数量
        :param qty: 传进来数量计算出辅助数量
        :return: 返回辅助数量
        """
        self.ensure_one()
        return self.conversion * qty

    def anti_conversion_unit(self, qty):
        """ 数量 = 辅助数量 / 转化率
        :param qty: 传入值为辅助数量
        :return: 数量
        """
        self.ensure_one()
        return self.conversion and qty / self.conversion or 0


class GoodsCertInfo(models.Model):
    _name = "goods.cert.info"
    _description = u"商品认证信息"

    @api.one
    @api.depends('cert_expire')
    def _get_expire_status(self):
        res = 0
        if self.cert_expire:
            exp_date = datetime.strptime(self.cert_expire, '%Y-%m-%d')
            res = (date.today() - exp_date.date()).days
        self.days_to_expire = res

    goods_id = fields.Many2one('goods', u'商品', ondelete='cascade')

    cert_name = fields.Many2one('core.value', u'证书名称', required=True,
                                ondelete='restrict',
                                domain=[('type', '=', 'goods_cert_name')],
                                context={'type': 'goods_cert_name'})
    cert_number = fields.Char(u'证书编号', required=True)
    cert_expire = fields.Date(u'证书有效期', default=fields.Date.context_today,
                              help=u'证书有效期, 默认为当前天')
    cert_count = fields.Integer(u'张数', default=1)
    note = fields.Text(u'备注')

    days_to_expire = fields.Integer(u'过期天数', compute=_get_expire_status, readonly=True)

    _sql_constraints = [
        ('cert_number_uniq', 'unique(cert_number)', u'证书编号不能重复'),
    ]


class Attribute(models.Model):
    _name = 'attribute'
    _description = u'属性'

    @api.one
    @api.depends('value_ids')
    def _compute_name(self):
        self.name = ' '.join(
            [value.category_id.name + ':' + value.value_id.name for value in self.value_ids])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        '''在many2one字段中支持按条形码搜索'''
        args = args or []
        if name:
            attribute_ids = self.search([('ean', '=', name)])
            if attribute_ids:
                return attribute_ids.name_get()
        return super(Attribute, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    ean = fields.Char(u'条码')
    name = fields.Char(u'属性', compute='_compute_name',
                       store=True, readonly=True)
    goods_id = fields.Many2one('goods', u'商品', ondelete='cascade')
    value_ids = fields.One2many(
        'attribute.value', 'attribute_id', string=u'属性')
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())

    _sql_constraints = [
        ('ean_uniq', 'unique (ean)', u'该条码已存在'),
    ]


class AttributeValue(models.Model):
    _name = 'attribute.value'
    _rec_name = 'value_id'
    _description = u'属性明细'

    attribute_id = fields.Many2one('attribute', u'属性', ondelete='cascade')
    category_id = fields.Many2one('core.category', u'属性',
                                  ondelete='cascade',
                                  domain=[('type', '=', 'attribute')],
                                  context={'type': 'attribute'},
                                  required='1')
    value_id = fields.Many2one('attribute.value.value', u'值',
                               ondelete='restrict',
                               domain="[('category_id','=',category_id)]",
                               default=lambda self: self.env.context.get(
                                   'default_category_id'),
                               required='1')
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())


class AttributeValueValue(models.Model):
    _name = 'attribute.value.value'
    _description = u'属性值'

    category_id = fields.Many2one('core.category', u'属性',
                                  ondelete='cascade',
                                  domain=[('type', '=', 'attribute')],
                                  context={'type': 'attribute'},
                                  required='1')
    name = fields.Char(u'值')
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())
