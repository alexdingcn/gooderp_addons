# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WhTemperature(models.Model):
    _name = 'wh.temperature'
    _description = u'库房温湿度记录'
    _order = 'date desc, id DESC'

    TYPE_SELECTION = [
        ('in', u'库房内'),
        ('out', u'库房外')]

    type = fields.Selection(TYPE_SELECTION, u'库房内/外', default='in')

    date = fields.Date(u'检查日期', required=True, default=fields.Date.context_today)

    warehouse_id = fields.Many2one('warehouse', u'仓库',
                                   ondelete='restrict',
                                   required=True)

    weather = fields.Char(u'气候')

    temperature = fields.Float(u'温度', required=True)

    humidity = fields.Float(u'湿度', required=True)

    maintenance_periods = fields.Integer(u'养护时间(分钟)', help=u'如果超标后的养护时间')

    maintenance_content = fields.Char(u'养护措施', help=u'如果超标后的养护措施')

    temperature_after = fields.Float(u'养护后的温度')

    humidity_after = fields.Float(u'养护后的湿度')

    next_maintenance = fields.Date(u'下次养护时间')

    note = fields.Char(u'备注')