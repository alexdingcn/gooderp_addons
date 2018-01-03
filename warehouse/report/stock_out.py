# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
from odoo import models, fields, api


class ReportStockOut(models.TransientModel):
    _name = 'report.stock.out'
    _description = u'商品缺货明细表'
    _inherit = 'report.base'

    goods_id = fields.Many2one('goods', u'商品', help=u'本次报表查看的商品')
    goods_qty = fields.Integer(u'库存余额')
    last_update_date = fields.Date(u'最后更新时间')
    warning_days = fields.Integer(u'预警天数')
    goods_warehouse_min = fields.Integer(u'最小库存预警')
    goods_warehouse_max = fields.Integer(u'最大库存预警')
    uom = fields.Char(u'单位')
    warehouse = fields.Char(u'仓库')

    id_lists = fields.Text(u'库存调拨id列表')

    def select_sql(self, sql_type='out'):
        return '''
        SELECT min(line.id) as id,
                goods.id as goods_id,
                goods.warehouse_min as goods_warehouse_min,
                goods.warehouse_max as goods_warehouse_max,
                array_agg(line.id) as id_lists,
                uom.name as uom,
                wh.name as warehouse,
                max(line.date) as last_update_date,
                sum(case when
                    line.type = 'in' THEN line.goods_qty ELSE -line.goods_qty END)
                    as goods_qty
        '''

    def from_sql(self, sql_type='out'):
        return '''
        FROM wh_move_line line
            LEFT JOIN goods goods ON line.goods_id = goods.id
            LEFT JOIN attribute att ON line.attribute_id = att.id
            LEFT JOIN uom uom ON line.uom_id = uom.id
            LEFT JOIN warehouse wh ON line.warehouse_id = wh.id or line.warehouse_dest_id = wh.id
        '''

    def where_sql(self, sql_type='out'):
        extra = ''
        if self.env.context.get('warehouse_id'):
            extra += ' AND wh.id = {warehouse_id}'
        if self.env.context.get('goods_id'):
            extra += ' AND goods.id = {goods_id}'
        return '''
        WHERE line.state = 'done'
          AND wh.type = 'stock'
          AND line.date >= '{date_start}'
          AND line.date < '{date_end}'
          %s
        ''' % extra

    def group_sql(self, sql_type='out'):
        return '''
        GROUP BY goods.id, uom.id, wh.id
        HAVING 
            sum(case when line.type = 'in' THEN line.goods_qty ELSE -line.goods_qty END) <= goods.warehouse_min
            or
            (sum(case when line.type = 'in' THEN line.goods_qty ELSE -line.goods_qty END) >= goods.warehouse_max and goods.warehouse_max > 0)
        '''

    def order_sql(self, sql_type='out'):
        return '''
        ORDER BY goods.name, wh.name
        '''

    def get_context(self, sql_type='out', context=None):
        # get start of date of next date
        date_end = datetime.strptime(context.get('date_end'), '%Y-%m-%d') + timedelta(days=1)
        date_end = date_end.strftime('%Y-%m-%d')

        return {
            'date_start': context.get('date_start') or '',
            'date_end': date_end,
            'warehouse_id': context.get('warehouse_id') and context.get('warehouse_id')[0] or '',
            'goods_id': context.get('goods_id') and context.get('goods_id')[0] or '',
        }

    def collect_data_by_sql(self, sql_type='out'):
        res = self.execute_sql()
        for record in res:
            if 'last_update_date' in record:
                days = (date.today() - datetime.strptime(record['last_update_date'], '%Y-%m-%d').date()).days
                record['warning_days'] = days
        return res

    @api.multi
    def find_source_move_line(self):
        # 查看库存调拨明细
        move_line_ids = []
        # 获得'report.stock.transceive'记录集
        move_line_lists = self.get_data_from_cache(sql_type='out')

        for line in move_line_lists:
            if line.get('id') == self.id:
                move_line_ids = line.get('id_lists')

        view = self.env.ref('warehouse.wh_move_line_tree')
        return {
            'view_mode': 'tree',
            'views': [(view.id, 'tree')],
            'res_model': 'wh.move.line',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_line_ids)]
        }
