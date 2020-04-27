# _*_ coding:utf-8 _*_
# Author: zizle
from flask import Blueprint
from .advise import ShortMessageView,UserShortMessageView,MarketAnalysisView,UserMarketAnalysisView,\
    UserRetrieveMarketAnalysisView,TopicSearchView,UserTopicSearchView,UserRetrieveTopicSearchView,SearchReportView,\
    UserSearchReportView,UserRetrieveSearchReportView
from .consult import PersonTrainView,DptBuildView,RulExamine
from .strategy import InvestmentPlan, UserInvestmentPlan,UserRetrieveInvestmentPlan,HedgePlanView,UserHedgePlanView,\
    UserRetrieveHedgePlanView
from .train import VarietyIntroductionView



pserver_blp = Blueprint(name='pserver', import_name=__name__, url_prefix='/')

# 咨询服务advise
pserver_blp.add_url_rule('advise/shortmessage/', view_func=ShortMessageView.as_view(name='short_message'))
pserver_blp.add_url_rule('user/<int:uid>/shortmessage/', view_func=UserShortMessageView.as_view(name='usersms'))

pserver_blp.add_url_rule('advise/marketanalysis/', view_func=MarketAnalysisView.as_view(name='market_analysis'))
pserver_blp.add_url_rule('user/<int:uid>/marketanalysis/', view_func=UserMarketAnalysisView.as_view(name='umk_analysis'))
pserver_blp.add_url_rule('user/<int:uid>/marketanalysis/<int:mid>/', view_func=UserRetrieveMarketAnalysisView.as_view(name='uvrmk_analysis'))

pserver_blp.add_url_rule('advise/topicsearch/', view_func=TopicSearchView.as_view(name='topicsearch'))
pserver_blp.add_url_rule('user/<int:uid>/topicsearch/', view_func=UserTopicSearchView.as_view(name='utp_search'))
pserver_blp.add_url_rule('user/<int:uid>/topicsearch/<int:tid>/', view_func=UserRetrieveTopicSearchView.as_view(name='uvrtp_search'))

pserver_blp.add_url_rule('advise/searchreport/', view_func=SearchReportView.as_view(name='searchreport'))
pserver_blp.add_url_rule('user/<int:uid>/searchreport/', view_func=UserSearchReportView.as_view(name='ushreport'))
pserver_blp.add_url_rule('user/<int:uid>/searchreport/<int:sid>/', view_func=UserRetrieveSearchReportView.as_view(name='uvrreport'))

# 顾问服务consult
pserver_blp.add_url_rule('consult/persontrain/', view_func=PersonTrainView.as_view(name='persontrain'))
pserver_blp.add_url_rule('consult/deptbuild/', view_func=DptBuildView.as_view(name='dptbuild'))
pserver_blp.add_url_rule('consult/rulexamine/', view_func=RulExamine.as_view(name='rulexamine'))

# 策略服务strategy
pserver_blp.add_url_rule('strategy/investmentplan/', view_func=InvestmentPlan.as_view(name='investmentplan'))
pserver_blp.add_url_rule('user/<int:uid>/investmentplan/', view_func=UserInvestmentPlan.as_view(name='userinvestmentplan'))
pserver_blp.add_url_rule('user/<int:uid>/investmentplan/<int:iid>/', view_func=UserRetrieveInvestmentPlan.as_view(name='uvrinvestmentplan'))

pserver_blp.add_url_rule('strategy/hedgeplan/', view_func=HedgePlanView.as_view(name='hedgeplan'))
pserver_blp.add_url_rule('user/<int:uid>/hedgeplan/', view_func=UserHedgePlanView.as_view(name='userhedgeplan'))
pserver_blp.add_url_rule('user/<int:uid>/hedgeplan/<int:hid>/', view_func=UserRetrieveHedgePlanView.as_view(name='uvrhedgeplan'))

# 培训服务train
pserver_blp.add_url_rule('train/varietyintro/', view_func=VarietyIntroductionView.as_view(name='varietyintro'))
