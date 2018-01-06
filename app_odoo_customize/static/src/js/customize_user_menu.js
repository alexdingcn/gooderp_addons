odoo.define('app_odoo_customize.customize_user_menu', function (require) {
    "use strict";
    var Model = require('web.Model');
    var session = require('web.session');

    var UserMenu = require('web.UserMenu');
    var documentation_url;
    var documentation_dev_url;
    var support_url;
    UserMenu.include({
        on_menu_debug: function () {
            window.location = $.param.querystring(window.location.href, 'debug');
        },
        on_menu_debugassets: function () {
            window.location = $.param.querystring(window.location.href, 'debug=assets');
        },
        on_menu_quitdebug: function () {
            window.location.search = "?";
        },
        on_menu_documentation: function () {
            window.open(documentation_url, '_blank');
        },
        on_menu_documentation_dev: function () {
            window.open(documentation_dev_url, '_blank');
        },
        on_menu_support: function () {
            window.open(support_url, '_blank');
        }
    });

    $(document).ready(function () {
        documentation_url = 'http://www.yibanjf.com/erpdocs/';
        documentation_dev_url = 'http://www.yibanjf.com/erpdocs/';
        support_url = 'http://www.yibanjf.com';
        setTimeout(function () {
            new Model('ir.config_parameter').call('search_read', [[['key', 'like', 'app_']], ['key', 'value']]).then(function (config) {
                if (config) {
                    _.each(config, function (item) {
                        var key = item['key'];
                        var val = item['value'];
                        if (key === 'app_show_debug') {
                            if (val === "False") {
                                $('.o_user_menu [data-menu="debug"]').parent().hide();
                                $('.o_user_menu [data-menu="debugassets"]').parent().hide();
                                $('.o_user_menu [data-menu="quitdebug"]').parent().hide();
                                $('.o_user_menu .divider').hide();
                            }
                        } else if (key === 'app_show_documentation') {
                            if (val === "False") {
                                $('.o_user_menu [data-menu="documentation"]').parent().hide();
                            } else {
                                documentation_url = val;
                            }
                        } else if (key === 'app_show_documentation_dev') {
                            if (val === "False") {
                                $('.o_user_menu [data-menu="documentation_dev"]').parent().hide();
                            } else {
                                documentation_dev_url = val;
                            }
                        } else if (key === 'app_show_support') {
                            if (val === "False") {
                                $('.o_user_menu [data-menu="support"]').parent().hide();
                            } else {
                                support_url = val;
                            }
                        }
                    });
                }
            });
        }, 2000);
    });
})
