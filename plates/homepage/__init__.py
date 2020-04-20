# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .bulletin import BulletinView
from .ad import AdView
from .report import ReportView, UserReportView,UserRetrieveReportView
from .exnotice import ExNoticeView, UserExNoticeView, UserRetrieveExNoticeView
from .spot import SpotView,UserSpotView,UserRetrieveSpotView
from .fecalendar import FeCalendarView,UserFeCalendarView,UserRetrieveFeCalendarView


homepage_blp = Blueprint(name='homepage', import_name=__name__, url_prefix='/')
homepage_blp.add_url_rule('bulletin/', view_func=BulletinView.as_view(name="bulletin"))
homepage_blp.add_url_rule('ad/', view_func=AdView.as_view(name="ad"))

homepage_blp.add_url_rule('report/', view_func=ReportView.as_view(name="report"))
homepage_blp.add_url_rule('user/<int:uid>/report/', view_func=UserReportView.as_view(name="userreport"))
homepage_blp.add_url_rule('user/<int:uid>/report/<int:rid>/', view_func=UserRetrieveReportView.as_view(name="urvrport"))

homepage_blp.add_url_rule('exnotice/', view_func=ExNoticeView.as_view(name='exnotice'))
homepage_blp.add_url_rule('user/<int:uid>/exnotice/', view_func=UserExNoticeView.as_view(name='userexnotice'))
homepage_blp.add_url_rule('user/<int:uid>/exnotice/<int:nid>/', view_func=UserRetrieveExNoticeView.as_view(name='urvrexnotice'))

homepage_blp.add_url_rule('spot/', view_func=SpotView.as_view(name='spot'))
homepage_blp.add_url_rule('user/<int:uid>/spot/', view_func=UserSpotView.as_view(name='userspot'))
homepage_blp.add_url_rule('user/<int:uid>/spot/<int:sid>/', view_func=UserRetrieveSpotView.as_view(name='urvrspot'))

homepage_blp.add_url_rule('fecalendar/', view_func=FeCalendarView.as_view(name='fecalendar'))
homepage_blp.add_url_rule('user/<int:uid>/fecalendar/', view_func=UserFeCalendarView.as_view(name='userfecalendar'))
homepage_blp.add_url_rule('user/<int:uid>/fecalendar/<int:fid>/', view_func=UserRetrieveFeCalendarView.as_view(name='urvrfecalendar'))