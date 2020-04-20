# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint
from .views import ClientView, ModuleView
from .auth import AuthUserModuleView
from .variety import VarietyView
from .files import ModelFilesView


basic_blp = Blueprint(name='client', import_name=__name__, url_prefix='/')
basic_blp.add_url_rule('client/', view_func=ClientView.as_view(name="client"))
basic_blp.add_url_rule('module/', view_func=ModuleView.as_view(name="module"))
basic_blp.add_url_rule('module/<int:mid>/', view_func=AuthUserModuleView.as_view(name="authmodule"))
basic_blp.add_url_rule('variety/', view_func=VarietyView.as_view(name='variety'))
basic_blp.add_url_rule('model_files/', view_func=ModelFilesView.as_view(name='modelfiles'))


