# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class division(models.Model):
    _name = "purchase.division"
    name = fields.Char('Name')
    div_code = fields.Char("Code")
    department_ids = fields.One2many('purchase.department', 'dep_id')


class department(models.Model):
    _name = "purchase.department"
    dep_id = fields.Many2one('purchase.division')
    name = fields.Char('Name')
    dep_code = fields.Char('Code')
