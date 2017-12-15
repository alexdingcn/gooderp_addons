# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'partner'

    cert_ids = fields.One2many('partner.cert.info', 'partner_id', string=u'合作伙伴认证信息')

    @api.multi
    def action_view_buy_history(self):
        '''
        This function returns an action that display buy history of given sells order ids.
        Date range [180 days ago, now]
        '''
        self.ensure_one()
        date_end = datetime.today()
        date_start = datetime.strptime(
            self.env.user.company_id.start_date, '%Y-%m-%d')

        if (date_end - date_start).days > 365:
            date_start = date_end - timedelta(days=365)

        buy_order_track_wizard_obj = self.env['buy.order.track.wizard'].create({'date_start': date_start,
                                                                                'date_end': date_end,
                                                                                'partner_id': self.id})

        return buy_order_track_wizard_obj.button_ok()


class PartnerCertInfo(models.Model):
    _name = "partner.cert.info"
    _description = u"合作伙伴认证信息"

    partner_id = fields.Many2one('partner', u'合作伙伴', ondelete='cascade')

    cert_name = fields.Char(u'证书名称')
    cert_number = fields.Char(u'证书编号')
    cert_expire = fields.Date(u'证书有效期', default=fields.Date.context_today,
                              help=u'证书有效期, 默认为当前天')
    cert_count = fields.Integer(u'张数')
    note = fields.Text(u'备注')

    _sql_constraints = [
        ('cert_number_uniq', 'unique(cert_number)', u'证书编号不能重复'),
    ]
