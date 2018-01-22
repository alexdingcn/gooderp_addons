odoo.define('buy.buy_order_view', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.DataModel');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;

    ListView.include({
        set_groups: function (groups) {
            this._super(groups);
            if (this.model === 'buy.order.line') {
                $(this.groups).off('row_link');
            }
        }
    });

    ListView.List.include({
        row_clicked: function (event) {
            this._super(event);
            if (this.view.editable() && this.view.is_action_enabled('edit')) {
                if (this.view && this.view.model === 'buy.order.line') {
                    // var tabButtons = $('#goods_detail a[data-toggle="tab"]');
                    // tabButtons.unbind('shown.bs.tab');

                    var record_id = $(event.currentTarget).data('id');
                    $('.oe_list_record_index').removeClass("selected");
                    $(event.currentTarget).find('.oe_list_record_index').addClass('selected');
                    var cached_goods = _.filter(this.dataset.cache, function (item) {
                        return record_id === item.id && !_.isEmpty(item.values) && !item.to_delete;
                    });
                    if (cached_goods && cached_goods.length === 1) {
                        var goods_id = cached_goods[0].values['goods_id'];
                        if (goods_id instanceof Array) {
                            goods_id = goods_id[0];
                        }

                        new Model('goods').call('search_read', [[['id', '=', goods_id]], []]).then(function (records) {
                            if (records && records.length > 0) {
                                $('#goods_info_tab').html(QWeb.render('GoodsInfoDetail', {
                                    goods_info: records[0],
                                    order_line: cached_goods[0].values
                                }));
                            }
                        });
                        new Model('goods').call('get_warehouse_balance', [goods_id]).then(function (records) {
                            $('#goods_warehouse_tab').html(QWeb.render('GoodsWarehouseBalance', {
                                balance: records
                            }));
                        });
                        new Model('vendor.goods').call('search_read', [[['goods_id', '=', goods_id]], []]).then(function (records) {
                            $('#goods_buy_history_tab').html(QWeb.render('GoodsBuyHistory', {
                                vendors: records
                            }));
                            $('#goods_detail').removeClass('hidden');
                        });
                    }
                }
            }
        }
    });
});