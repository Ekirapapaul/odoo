# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class internal_requisition(models.Model):
    _name = "purchase.internal.requisition"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Internal Requisition"

    ir_dept_id = fields.Many2one('purchase.department', 'Department', required=True)
    ir_dept_code = fields.Char('Department Code', readonly=True, store=True)
    ir_dept_head_id = fields.Char('Department Head', readonly=True, store=True)
    ir_req_date = fields.Datetime(
        string='Date', required=True, index=True, default=fields.Datetime.now)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'IRF Sent'),
        ('to approve', 'WH Manager'),
        ('purchase', 'Approved'),
        ('done', 'Approved & Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    name = fields.Char('Reference', required=True,
                       index=True, copy=False, default='New')
    item_ids = fields.One2many(
        'purchase.internal.requisition.item', 'ir_item_id')
    notes = fields.Text('Terms and Conditions')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id, index=1)
    date_approve = fields.Date(
        'Approval Date', readonly=1, index=True, copy=False)
    

    @api.onchange('ir_dept_id')
    def _populate_dep_code(self):
        self.ir_dept_code = self.ir_dept_id.dep_code
        self.ir_dept_head_id = self.ir_dept_id.dep_head_id.name
        return {}

    @api.model
    def create(self, vals):
        department = self.env["purchase.department"].search(
            [['id', '=', vals['ir_dept_id']]])

        vals['ir_dept_code'] = department.dep_code
        vals['ir_dept_head_id'] = department.dep_head_id.name

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'purchase.internal.requisition') or '/'
        return super(internal_requisition, self).create(vals)

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state in ['draft', 'sent']:
                self.write({'state': 'to approve',
                            'date_approve': fields.Date.context_today(self)})
                self.notifyUserInGroup(
                    "stock.group_stock_manager")
        return True

    @api.multi
    def button_approve(self, force=False):
        self.write(
            {'state': 'purchase', 'date_approve': fields.Date.context_today(self)})
        self.filtered(
            lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})
        return {}
    
    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}

    # deal with notification
    @api.multi
    def notifyUserInGroup(self, group_ext_id):
        group = self.env.ref(group_ext_id)
        for user in group.users:
            _logger.error("Notify User `%s` In Group `%s`" %
                          (str(user.login), group.name))
            self.sendToManager(user.login, self[0].name, user.name)
        return True

    @api.multi
    def sendToManager(self, recipient, po, name):
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        mail_pool = self.env['mail.mail']
        values = {}
        values.update({'subject': 'Internal Requisition Order #' +
                       po + ' waiting your approval'})
        values.update({'email_from': "odoomail.service@gmail.com"})
        values.update({'email_to': recipient})
        values.update({'body_html':
                       'To Manager ' + name + ',<br>'
                       + 'IRF No. ' + po + ' has been created and requires your approval. You can find the details to approve here. '+url})

        self.env['mail.mail'].create(values).send()
        return True

    @api.multi
    def notifyInitiator(self, approver):
        user = self.env["res.users"].search(
            [['id', '=', self[0].create_uid.id]])
        self.sendToInitiator(user.login, self[0].name, user.name, approver)
        return True

    @api.multi
    def sendToInitiator(self, recipient, po, name, approver):
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        mail_pool = self.env['mail.mail']
        values = {}
        values.update({'subject': 'Internal Requisition order #' +
                       po + ' approved'})
        values.update({'email_from': "odoomail.service@gmail.com"})
        values.update({'email_to': recipient})
        values.update({'body_html':
                       'To ' + name + ',<br>'
                       + 'IRF No. ' + po + ' has been Approved by ' + str(approver)+'. You can find the details: '+url})

        self.env['mail.mail'].create(values).send()
        return True


class purchase_internal_requisition_items(models.Model):
    _name = "purchase.internal.requisition.item"
    ir_item_id = fields.Many2one('purchase.internal.requisition')
    item_id = fields.Many2one('product.template', string='Item')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision(
        'Product Unit of Measure'), required=True)
    comment = fields.Text("Comment")
