{
    'name': 'KIJABE-PURCHASE-EXT',
    'description': 'Extend purchase module to add custom modifications for Kijabe odoo implementation',
    'author': 'Mupagasi Jean Paul',
    'depends': ['purchase'],
    'summary':'Extension of Purchase module',
    'website':'https://cure.org/',
    'data': 
        [
            'security/purchase_groups.xml',
            'views/kijabe_purchase_ext_view.xml'
        ],
}