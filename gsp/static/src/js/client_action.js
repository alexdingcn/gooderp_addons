odoo.define('gsp.goods_class_list_action', function (require) {
    "use strict";

    var config = require('web.config');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var data = require('web.data');
    var data_manager = require('web.data_manager');
    var ListView = require('web.ListView');

    var pyeval = require('web.pyeval');
    var SearchView = require('web.SearchView');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;

    var GoodsListCustomizedList = ListView.extend({
        select_record: function (index, view) {
            this.dataset.index = index;
            this.do_action({
                name: 'Goods',
                type: 'ir.actions.act_window',
                res_model: "goods",
                views: [[false, 'form']],
                res_id: this.dataset.ids[index]
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        }
    });

    var GoodsClassListAction = Widget.extend(ControlPanelMixin, {
        template: 'gsp.goods_class_list_action',

        events: {
            "click .o_sidebar_menu_item": "set_menu_item"
        },

        set_menu_item: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var target = this.$(event.currentTarget);
            if (target) {
                var item_id = target.data('item-id');
                var item_title = target.find(".o_channel_name").first().text()
                this.set_content(item_id, item_title);
            }
        },

        on_attach_callback: function () {

        },

        init: function (parent, action, options) {
            this._super.apply(this, arguments);
            this.action_manager = parent;
            this.dataset = new data.DataSetSearch(this, 'goods.class');
            this.relatedDataset = new data.DataSetSearch(this, 'goods');
            this.domain = [];
            this.action = action;
            this.options = options || {};
        },

        on_goods_class_loaded: function (data) {
            this.render_sidebar(data);
            if (data && data.length > 0) {
                $(".o_sidebar_menu_item").first().click();
            }
        },

        willStart: function () {
            var self = this;
            var view_id = this.action && this.action.search_view_id && this.action.search_view_id[0];
            var def = data_manager
                .load_fields_view(this.relatedDataset, view_id, 'tree', false)
                .then(function (fields_view) {
                    self.fields_view = fields_view;
                });
            return $.when(this._super(), def);
        },

        start: function () {
            var self = this;

            // create searchview
            var options = {
                $buttons: $("<div>"),
                action: this.action,
                disable_groupby: true,
            };

            this.searchview = new SearchView(this, this.relatedDataset, this.fields_view, options);
            this.searchview.on('search_data', this, this.on_search);

            this.$buttons = $(QWeb.render("mail.chat.ControlButtons", {}));
            this.$buttons.find('button').css({display: "inline-block"});

            this.$buttons.on('click', '.o_new_goods_class', this.on_click_btn_new_goods_class);
            this.$buttons.on('click', '.o_new_goods', this.on_click_btn_new_goods);

            var def2 = this.searchview.appendTo($("<div>")).then(function () {
                self.$searchview_buttons = self.searchview.$buttons.contents();
            });

            return $.when(def2).then(function () {
                self.dataset.read_slice(['name', 'parent_id', 'child_ids'], {}).done(self.on_goods_class_loaded);
            });
        },

        render_sidebar: function (items) {
            if (items) {
                var dataset = _.indexBy(items, 'id');
                var $sidebar = this._render_sidebar({
                    active_id: this.current_id ? this.current_id : undefined,
                    dataset: dataset,
                    items: items
                });
                this.$(".o_mail_chat_sidebar").html($sidebar.contents());
                $('#sidebar_tree').bonsai({
                    expandAll: false
                });
            }
        },

        _render_sidebar: function (options) {
            return $(QWeb.render("gsp.GoodsClass.Sidebar", options));
        },

        set_content: function (sidebar_menu_id, menu_title) {
            var self = this;

            this.current_id = sidebar_menu_id;
            this.action.context.active_id = sidebar_menu_id;
            this.action.context.active_ids = [sidebar_menu_id];

            this.domain = [];
            if (sidebar_menu_id) {
                this.domain.push(['goods_class_id', '=', sidebar_menu_id]);
            }

            return this.fetch_and_render_content().then(function () {
                // Update control panel
                self.set("title", menu_title);
                // // Hide 'invite'', 'unsubscribe' and 'settings' buttons in static channels and DM
                // self.$buttons
                //     .find('.o_mail_chat_button_invite, .o_mail_chat_button_unsubscribe, .o_mail_chat_button_settings')
                //     .toggle(sidebar_menu.type !== "dm" && sidebar_menu.type !== 'static');
                // self.$buttons
                //     .find('.o_mail_chat_button_mark_read')
                //     .toggle(sidebar_menu.id === "channel_inbox");
                // self.$buttons
                //     .find('.o_mail_chat_button_unstar_all')
                //     .toggle(sidebar_menu.id === "channel_starred");
                //
                self.$('.o_sidebar_menu_item')
                    .removeClass('o_active')
                    .filter('[data-item-id=' + self.current_id + ']')
                    .addClass('o_active');

                // var $new_messages_separator = self.$('.o_thread_new_messages_separator');
                // if ($new_messages_separator.length) {
                //     self.content.$el.scrollTo($new_messages_separator);
                // } else {
                //     self.content.scroll_to({offset: new_channel_scrolltop});
                // }


                // Update control panel before focusing the composer, otherwise focus is on the searchview
                self.update_cp();
                if (config.device.size_class === config.device.SIZES.XS) {
                    self.$('.o_mail_chat_sidebar').hide();
                }

                self.action_manager.do_push_state({
                    action: self.action.id,
                    active_id: sidebar_menu_id,
                });
            });
        },


        fetch_and_render_content: function () {
            var self = this;
            var contentData = new data.DataSetSearch(null, 'goods', null, this.domain);
            var contentDiv = this.$('.o_mail_chat_content');
            contentDiv.empty();
            this.content = new GoodsListCustomizedList(self, contentData, self.fields_view);

            return this.content.appendTo(contentDiv).then(self.content.proxy('reload'));
        },

        update_cp: function () {
            this.update_control_panel({
                breadcrumbs: this.action_manager.get_breadcrumbs(),
                cp_content: {
                    $buttons: this.$buttons,
                    $searchview: this.searchview.$el,
                    $searchview_buttons: this.$searchview_buttons,
                },
                searchview: this.searchview,
            });
        },

        do_show: function () {
            this._super.apply(this, arguments);
            this.update_cp();
            this.action_manager.do_push_state({
                action: this.action.id,
                active_id: this.current_id,
            });
        },

        on_search: function (domains) {
            var result = pyeval.sync_eval_domains_and_contexts({
                domains: domains
            });
            this.domain = result.domain;
            if (this.current_id) {
                this.domain.push(['goods_class_id', '=', this.current_id]);
            }

            this.fetch_and_render_content();
        },

        on_click_btn_new_goods_class: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "goods.class",
                views: [[false, 'form']],
                target: 'current'
            });
        },

        on_click_btn_new_goods: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "goods",
                views: [[false, 'form']],
                target: 'current'
            });
        },

        destroy: function () {
            if (this.$buttons) {
                this.$buttons.off().destroy();
            }
            this._super.apply(this, arguments);
        }
    });

    core.action_registry.add('gsp.goods_class_list', GoodsClassListAction);
});
