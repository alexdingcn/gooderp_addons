# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from werkzeug.exceptions import Forbidden

from odoo import http, tools
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
# from odoo.addons.website_form.controllers.main import WebsiteForm

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class TableCompute(object):

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=PPG):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        for p in products:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % PPR, pos / PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) / PPR) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos / PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos / PPR) + y2][(pos % PPR) + x2] = False
            self.table[pos / PPR][pos % PPR] = {
                'product': p, 'x': x, 'y': y,
                'class': " ".join(map(lambda x: x.html_class or '', p.website_style_ids))
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos / PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c]

        return rows

        # TODO keep with input type hidden


# class WebsiteSaleForm(WebsiteForm):
#
#     @http.route('/website_form/shop.sale.order', type='http', auth="public", methods=['POST'], website=True)
#     def website_form_saleorder(self, **kwargs):
#         model_record = request.env.ref('sale.model_sale_order')
#         try:
#             data = self.extract_data(model_record, kwargs)
#         except ValidationError, e:
#             return json.dumps({'error_fields': e.args[0]})
#
#         order = request.website.sale_get_order()
#         if data['record']:
#             order.write(data['record'])
#
#         if data['custom']:
#             values = {
#                 'body': nl2br(data['custom']),
#                 'model': 'sale.order',
#                 'message_type': 'comment',
#                 'no_auto_thread': False,
#                 'res_id': order.id,
#             }
#             request.env['mail.message'].sudo().create(values)
#
#         if data['attachments']:
#             self.insert_attachment(model_record, order.id, data['attachments'])
#
#         return json.dumps({'id': order.id})


class WebsiteSale(http.Controller):

    def get_attribute_value_ids(self, product):
        """ 产品的属性列表

        :return: 产品属性列表
           [attribute id, [attribute ids], price, sale price]
        """
        # product attributes with at least two choices
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        attribute_ids = []
        for attribute in product.attribute_ids:
            attribute_ids.append(
                [attribute.id, product.attribute_ids, product.price, product.price])

        return attribute_ids

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        return 'website_published desc,%s , id desc' % post.get('order', 'website_sequence desc')

    def _get_search_domain(self, search, category, attrib_values):
        #         domain = request.website.sale_product_domain()
        domain = []
        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_ids.value_ids', 'in', ids)]

        return domain

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attributes_ids = set([v[0] for v in attrib_values])
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)
        domain += [('not_saleable', '=', False)]

        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list, order=post.get('order'))

        request.context = dict(
            request.context, partner=request.env.user.gooderp_partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if category:
            category = request.env['goods.class'].browse(int(category))
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list

#         categs = request.env['product.public.category'].search([('parent_id', '=', False)])
        Product = request.env['goods']

        parent_category_ids = []
        if category:
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        product_count = Product.search_count(domain)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'])

        ProductAttribute = request.env['attribute']
        if products:
            # get all products without limit
            selected_products = Product.search(domain, limit=False)
            attributes = ProductAttribute.search(
                [('goods_id', 'in', selected_products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        # 币别
        for user in request.env['res.users'].browse(request.uid):
            currency = user.company_id.currency_id

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'attributes': attributes,
            'keep': keep,
            'parent_category_ids': parent_category_ids,
            'currency': currency,
        }
        if category:
            values['main_object'] = category
        return request.render("good_shop.products", values)

    # 点击界面上的某一个产品
    @http.route(['/shop/product/<model("goods"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        product_context = dict(request.env.context,
                               active_id=product.id,
                               partner=request.env.user.gooderp_partner_id)
        ProductCategory = request.env['goods.class']
#         Rating = request.env['rating.rating']

        if category:
            category = ProductCategory.browse(int(category)).exists()

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        keep = QueryURL('/shop', category=category and category.id,
                        search=search, attrib=attrib_list)

        if not product_context.get('pricelist'):
            #             product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)

        attribute_dict = {}
        for attribute in product.attribute_ids:
            for value in attribute.value_ids:
                if not attribute_dict.has_key(value.category_id.name):
                    attribute_dict.update(
                        {value.category_id.name: [value.value_id.name]})
                else:
                    if value.value_id.name in attribute_dict[value.category_id.name]:
                        continue
                    else:
                        attribute_dict[value.category_id.name].append(
                            value.value_id.name)

        # 货币取当前登录用户公司对应的货币
        for user in request.env['res.users'].browse(request.uid):
            currency = user.company_id.currency_id

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'keep': keep,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'currency': currency,
            'attribute_dict': attribute_dict,
        }
        return request.render("good_shop.product", values)

    # 点击购物车
    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        order = request.website.sale_get_order()

        values = {
            'website_sale_order': order,
            'compute_currency': lambda price: price,
            'suggested_products': [],
        }

        if post.get('type') == 'popover':
            return request.render("good_shop.cart_popover", values)

        if post.get('code_not_available'):
            values['code_not_available'] = post.get('code_not_available')

        return request.render("good_shop.cart", values)

    # 点击 加入购物车
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, goods_id, add_qty=1, set_qty=0, **kw):
        request.website.sale_get_order(force_create=1)._cart_update(
            goods_id=int(goods_id),
            add_qty=float(add_qty),
            set_qty=float(set_qty),
            attributes=self._filter_attributes(**kw),
        )

        # 进入购物车
        return request.redirect("/shop/cart")

    def _filter_attributes(self, **kw):
        return {k: v for k, v in kw.items() if "attribute" in k}

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}

        value = order._cart_update(
            goods_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)
        if not order.cart_quantity:
            request.website.sale_reset()
            return {}
        if not display:
            return None

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity
#         from_currency = order.company_id.currency_id
#         to_currency = order.pricelist_id.currency_id
        value['good_shop.cart_lines'] = request.env['ir.ui.view'].render_template("good_shop.cart_lines", {
            'website_sale_order': order,
            'compute_currency': lambda price: price,
            #             'suggested_products': order._cart_accessories()
        })
        return value

    def _get_mandatory_billing_fields(self):
        return ["name", "address"]  # , "city", "country_id"

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        # 如果没有error
        SellOrder = request.env['sell.order']
        values = {'website_sale_order': order, 'errors': SellOrder._get_errors(order)}
        values.update(SellOrder._get_website_data(order))
        if not values['errors']:
            if order.partner_id.id == request.website.user_id.sudo().gooderp_partner_id.id:
                return request.redirect('/shop/address')

            for f in self._get_mandatory_billing_fields():
                if not order.partner_id[f]:
                    return request.redirect('/shop/address?partner_id=%d' % order.partner_id.id)

            values.update(self.prepare_checkout_values(**post))

            # Avoid useless rendering if called in ajax
            if post.get('xhr'):
                return 'ok'

        return request.render("good_shop.checkout", values)

    # ------------------------------------------------------
    # Checkout
    # ------------------------------------------------------

    def checkout_redirection(self, order):
        ''' 重定向 '''
        # must have a draft sale order with lines at this point, otherwise reset
        if not order or order.state != 'draft':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        # ？？？？？？？？？？？
        # if transaction pending / done: redirect to confirmation
        tx = request.env.context.get('website_sale_transaction')
        if tx and tx.state != 'draft':
            return request.redirect('/shop/payment/confirmation/%s' % order.id)

    def prepare_checkout_values(self, **kw):
        order = request.website.sale_get_order(force_create=1)
        # get all partner address
        shippings = []
        if order.partner_id != request.website.user_id.sudo().gooderp_partner_id:
            shippings = request.env['partner.address'].search([('partner_id', '=', order.partner_id.id)], order='id')

        # get all payment methods
        acquirers = request.env['payment.acquirer'].search(
            [('environment', '=', 'prod'), ('company_id', '=', order.company_id.id)]
        )

        values = {
            'order': order,
            'shippings': shippings,
            'acquirers': [],
            'only_services': order and order.only_services or False
        }

        for acquirer in acquirers:
            acquirer_button = acquirer.with_context(submit_class='btn btn-primary', submit_txt='支付').sudo().render(
                '/',
                order.amount_total,
                request.env.user.company_id.currency_id.id,
                values={
                    'return_url': '/shop/payment/validate',
                    'billing_partner_id': order.partner_id.id,
                }
            )
            acquirer.button = acquirer_button
            values['acquirers'].append(acquirer)

        values['tokens'] = request.env['payment.token'].search([('partner_id', '=', order.partner_id.id), ('acquirer_id', 'in', acquirers.ids)])

        return values

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True)
    def address(self, **kw):
        Partner = request.env['partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().gooderp_partner_id.id:
            mode = ('new', 'billing')

        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                else:
                    shippings = Partner.search(
                        [('id', '=', order.partner_id.id)])
                    if partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else:  # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(
                mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(
                order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)

                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.onchange_partner_id()
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/checkout')

        country = request.env.ref('partner_address.cn')
        render_values = {
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'country': country,
            "states": request.env['country.state'].sudo().search([('country_id', '=', country.id)]),
            'error': errors,
            'callback': kw.get('callback'),
        }
        return request.render("good_shop.address", render_values)

    def values_preprocess(self, order, mode, values):
        return values

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values = {}
        for k, v in values.items():
            # don't drop empty value, it could be a field to reset
            new_values[k] = v

        new_values['customer'] = True

#         if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
#             new_values['type'] = 'other'
#         if mode[1] == 'shipping':
#             new_values['parent_id'] = order.partner_id.commercial_partner_id.id
#             new_values['type'] = 'delivery'

        return new_values, errors, error_msg

    def checkout_form_validate(self, mode, all_form_values, data):
        # mode: tuple ('new|edit', 'billing|shipping')
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []

        # Required fields from form
        required_fields = filter(
            None, (all_form_values.get('field_required') or '').split(','))
        # Required fields from mandatory field function
        required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields(
        ) or self._get_mandatory_billing_fields()

        # error message for empty required fields
        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(u'请输入有效的邮箱地址！')

        if [err for err in error.values() if err == 'missing']:
            error_message.append(u'必输字段不能为空')

        return error, error_message

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().create(checkout)
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                if partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
                order.address = checkout['address']
                order.mobile = checkout['mobile']
        return partner_id

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()
        #request.website.complete_sell_order()

        # 订单创建成功，清空购物车
        redirection = self.checkout_redirection(order)
        if redirection:
            # return request.render("good_shop.success")
            return redirection

        # order.onchange_partner_shipping_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        # extra_step = request.env.ref('website_sale.extra_info_option')
        # if extra_step.active:
        #     return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment")

    # ------------------------------------------------------
    # Payment
    # ------------------------------------------------------

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sale order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        SellOrder = request.env['sell.order']
        values = {'website_sale_order': order, 'errors': SellOrder._get_errors(order)}
        values.update(SellOrder._get_website_data(order))
        if not values['errors']:
            acquirers = request.env['payment.acquirer'].search(
                [('website_published', '=', True), ('company_id', '=', order.company_id.id)]
            )
            values['acquirers'] = []
            for acquirer in acquirers:
                acquirer_button = acquirer.with_context(submit_class='btn btn-primary', submit_txt=_('Pay Now')).sudo().render(
                    '/',
                    order.amount_total,
                    order.pricelist_id.currency_id.id,
                    values={
                        'return_url': '/shop/payment/validate',
                        'billing_partner_id': order.partner_invoice_id.id,
                    }
                )
                acquirer.button = acquirer_button
                values['acquirers'].append(acquirer)

            values['tokens'] = request.env['payment.token'].search([('partner_id', '=', order.partner_id.id), ('acquirer_id', 'in', acquirers.ids)])

        return request.render("good_shop.payment", values)

    @http.route(['/shop/payment/transaction_token/confirm'], type='json', auth="public", website=True)
    def payment_transaction_token_confirm(self, tx, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(int(tx))
        if (tx and request.website.sale_get_transaction() and
                tx.id == request.website.sale_get_transaction().id and
                tx.payment_token_id and
                tx.partner_id == tx.sale_order_id.partner_id):
            try:
                s2s_result = tx.s2s_do_transaction()
                valid_state = 'authorized' if tx.acquirer_id.auto_confirm == 'authorize' else 'done'
                if not s2s_result or tx.state != valid_state:
                    return dict(success=False, error=_("Payment transaction failed (%s)") % tx.state_message)
                else:
                    # Auto-confirm SO if necessary
                    tx._confirm_so()
                    return dict(success=True, url='/shop/payment/validate')
            except Exception, e:
                _logger.warning(_("Payment transaction (%s) failed : <%s>") % (tx.id, str(e)))
                return dict(success=False, error=_("Payment transaction failed (Contact Administrator)"))
        return dict(success=False, error='Tx missmatch')

    @http.route(['/shop/payment/transaction_token'], type='http', methods=['POST'], auth="public", website=True)
    def payment_transaction_token(self, tx_id, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(int(tx_id))
        if (tx and request.website.sale_get_transaction() and
                tx.id == request.website.sale_get_transaction().id and
                tx.payment_token_id and
                tx.partner_id == tx.sale_order_id.partner_id):
            return request.render("good_shop.payment_token_form_confirm", dict(tx=tx))
        else:
            return request.redirect("/shop/payment?error=no_token_or_missmatch_tx")

    @http.route(['/shop/payment/transaction/<int:acquirer_id>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id, tx_type='form', token=None, **kwargs):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
        Transaction = request.env['payment.transaction'].sudo()

        # In case the route is called directly from the JS (as done in Stripe payment method)
        so_id = kwargs.get('so_id')
        so_token = kwargs.get('so_token')
        if so_id and so_token:
            order = request.env['sell.order'].sudo().search([('id', '=', so_id), ('access_token', '=', so_token)])
        elif so_id:
            order = request.env['sell.order'].search([('id', '=', so_id)])
        else:
            order = request.website.sale_get_order()
        if not order or not order.order_line or acquirer_id is None:
            return request.redirect("/shop/checkout")

        assert order.partner_id.id != request.website.partner_id.id

        # find an already existing transaction
        tx = request.website.sale_get_transaction()
        if tx:
            if tx.sale_order_id.id != order.id or tx.state in ['error', 'cancel'] or tx.acquirer_id.id != acquirer_id:
                tx = False
            elif token and tx.payment_token_id and token != tx.payment_token_id.id:
                # new or distinct token
                tx = False
            elif tx.state == 'draft':  # button cliked but no more info -> rewrite on tx or create a new one ?
                tx.write(dict(Transaction.on_change_partner_id(order.partner_id.id).get('value', {}), amount=order.amount_total, type=tx_type))
        if not tx:
            tx_values = {
                'acquirer_id': acquirer_id,
                'type': tx_type,
                'amount': order.amount_total,
                'currency_id': order.pricelist_id.currency_id.id,
                'partner_id': order.partner_id.id,
                'partner_country_id': order.partner_id.country_id.id,
                'reference': Transaction.get_next_reference(order.name),
                'sale_order_id': order.id,
            }
            if token and request.env['payment.token'].sudo().browse(int(token)).partner_id == order.partner_id:
                tx_values['payment_token_id'] = token

            tx = Transaction.create(tx_values)
            request.session['sale_transaction_id'] = tx.id

        # update quotation
        order.write({
            'payment_acquirer_id': acquirer_id,
            'payment_tx_id': request.session['sale_transaction_id']
        })
        if token:
            return request.env.ref('good_shop.payment_token_form').render(dict(tx=tx), engine='ir.qweb')

        return tx.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=_('Pay Now')).sudo().render(
            tx.reference,
            order.amount_total,
            order.pricelist_id.currency_id.id,
            values={
                'return_url': '/shop/payment/validate',
                'partner_id': order.partner_shipping_id.id or order.partner_invoice_id.id,
                'billing_partner_id': order.partner_invoice_id.id,
            },
        )

    @http.route('/shop/payment/get_status/<int:sale_order_id>', type='json', auth="public", website=True)
    def payment_get_status(self, sale_order_id, **post):
        order = request.env['sell.order'].sudo().browse(sale_order_id)
        assert order.id == request.session.get('sale_last_order_id')

        values = {}
        flag = False
        if not order:
            values.update({'not_order': True, 'state': 'error'})
        else:
            tx = request.env['payment.transaction'].sudo().search(
                ['|', ('sale_order_id', '=', order.id), ('reference', '=', order.name)], limit=1
            )

            if not tx:
                if order.amount_total:
                    values.update({'tx_ids': False, 'state': 'error'})
                else:
                    values.update({'tx_ids': False, 'state': 'done', 'validation': None})
            else:
                state = tx.state
                flag = state == 'pending'
                values.update({
                    'tx_ids': True,
                    'state': state,
                    'acquirer_id': tx.acquirer_id,
                    'validation': tx.acquirer_id.auto_confirm == 'none',
                    'tx_post_msg': tx.acquirer_id.post_msg or None
                })

        return {'recall': flag, 'message': request.env['ir.ui.view'].render_template("good_shop.order_state_message", values)}

    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if transaction_id is None:
            tx = request.website.sale_get_transaction()
        else:
            tx = request.env['payment.transaction'].browse(transaction_id)

        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sell.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if (not order.amount_total and not tx) or tx.state in ['pending', 'done', 'authorized']:
            if (not order.amount_total and not tx):
                # Orders are confirmed by payment transactions, but there is none for free orders,
                # (e.g. free events), so confirm immediately
                order.with_context(send_email=True).action_confirm()
        elif tx and tx.state == 'cancel':
            # cancel the quotation
            order.action_cancel()

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        return request.redirect('/shop/confirmation')


