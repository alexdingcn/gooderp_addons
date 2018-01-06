# -*- coding: utf-8 -*-
{
    'name': 'App Odoo Customize(Backend Debranding Title,Language,Documentation,Quick Debug,Delete clear)',
    'version': '10.0.1.0',
    'author': 'AlexDing',
    'category': 'Productivity',
    'website': 'http://www.yibanjf.com',
    'license': 'AGPL-3',
    'sequence': 2,
    'summary': 'Quick customize and debranding your own Odoo. Quick debug, Language Switcher, Online Documentation Access,Delete test data.',
    'description': """

App Customize(Debranding Title,Language,Documentation,Quick Debug)
============
White label odoo.
You can config odoo, make it look like your own platform.
1. Deletes label in footer
2. Replaces "company" in Windows title
3. Customize Documentation, Support, About links and title in usermenu
4. Adds "Developer mode" link to the top right-hand User Menu.
5. Adds Quick Language Switcher to the top right-hand User Menu.
6. Adds Country flags  to the top right-hand User Menu.
7. Adds English and Chinese user documentation access to the top right-hand User Menu.
8. Adds developer documentation access to the top right-hand User Menu.
9. Customize "My odoo.com account" button
10. Standalone setting panel, easy to setup.
11. Provide 236 country flags.
12. Multi-language Support.
13. Change Powered by in login screen.(Please change '../views/app_odoo_customize_view.xml' #15)
14. Quick delete test data in Apps: Sales/POS/Purchase/MRP/Inventory/Accounting/Message/Workflow etc.
15. Reset All the Sequence to beginning of 1: SO/PO/MO/Invoice...

This module can help to white label the Odoo.
Also helpful for training and support for your end-user.
The user can get the help document just by one click.

    """,
    'images': ['static/description/banner.png'],
    'depends': ['web'],
    'data': [
        'views/app_odoo_customize_view.xml',
        'views/app_theme_config_settings_view.xml',
        # data
        'data/ir_config_parameter.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'qweb': [
        'static/src/xml/customize_user_menu.xml',
    ],
}

