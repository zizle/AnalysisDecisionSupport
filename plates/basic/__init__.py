# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint
from .views import ClientView, ModuleView, SortModuleView, get_user_access_module
from .auth import AuthUserModuleView
from .variety import VarietyView
from .files import ModelFilesView
from .update import UpdatingClientView, DownloadingClientView, UpdatingDeliveryView, DownloadingDeliveryView


basic_blp = Blueprint(name='client', import_name=__name__, url_prefix='/')
basic_blp.add_url_rule('update/', view_func=UpdatingClientView.as_view(name='update'))
basic_blp.add_url_rule('update_delivery/', view_func=UpdatingDeliveryView.as_view(name='updatedry'))
basic_blp.add_url_rule('downloading/', view_func=DownloadingClientView.as_view(name='download'))
basic_blp.add_url_rule('downloading_delivery/', view_func=DownloadingDeliveryView.as_view(name='downloaddry'))
basic_blp.add_url_rule('client/', view_func=ClientView.as_view(name="client"))

basic_blp.add_url_rule('module_access/', view_func=get_user_access_module, methods=['POST'])  # 20200827修改用户可否进入模块

basic_blp.add_url_rule('module/', view_func=ModuleView.as_view(name="module"))
basic_blp.add_url_rule('module/<int:mid>/', view_func=AuthUserModuleView.as_view(name="authmodule"))
basic_blp.add_url_rule('module/sort/', view_func=SortModuleView.as_view(name="sortmodule"))  # 排序模块

basic_blp.add_url_rule('variety/', view_func=VarietyView.as_view(name='variety'))
basic_blp.add_url_rule('model_files/', view_func=ModelFilesView.as_view(name='modelfiles'))  # 模板文件



