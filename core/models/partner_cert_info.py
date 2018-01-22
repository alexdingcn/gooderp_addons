# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models


class PartnerCertInfo(models.Model):
    _name = "partner.cert.info"
    _description = u"合作伙伴认证信息"
    _sort = "id desc"

    @api.multi
    def name_get(self):
        return [(record.id, "%s[%s]" % (record.partner_id.name, record.cert_name.name)) for record in self]

    @api.one
    @api.depends('cert_expire')
    def _get_expire_status(self):
        res = 0
        if self.cert_expire:
            exp_date = datetime.strptime(self.cert_expire, '%Y-%m-%d')
            res = (date.today() - exp_date.date()).days
        self.days_to_expire = res

    partner_id = fields.Many2one('partner', u'合作伙伴', ondelete='cascade')
    partner_type = fields.Selection(
        related='partner_id.type',
        string='合作伙伴类型',
        readonly=True,
        store=False,
    )

    cert_name = fields.Many2one('core.value', u'证书名称',
                                ondelete='restrict',
                                domain=[('type', '=', 'cert_name')],
                                context={'type': 'cert_name'})
    cert_number = fields.Char(u'证书编号', required=True)
    cert_company_name = fields.Char(u'证书企业名称', required=True)
    cert_company_address = fields.Char(u'证书企业地址')
    cert_issue_date = fields.Date(u'证书发证日期', required=True)
    cert_expire = fields.Date(u'证书有效期', default=fields.Date.context_today, required=True,
                              help=u'证书有效期, 默认为当前天')
    cert_scope = fields.Char(u'许可范围')
    cert_count = fields.Integer(u'张数', default='1')

    economics_type = fields.Char(u'经济性质')
    business_type = fields.Char(u'经营方式')
    registration_amount = fields.Integer(u'注册资金')
    legal_person = fields.Char(u'法人')

    note = fields.Text(u'备注')

    days_to_expire = fields.Integer(u'过期天数', compute=_get_expire_status, readonly=True)

    _sql_constraints = [
        ('cert_number_uniq', 'unique(cert_number)', u'证书编号不能重复'),
    ]
