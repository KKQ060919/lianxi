from django.urls import path
from .views import (
    UserBehaviorView,
    UserRecentViewsView,
    UserBehaviorStatsView
)

app_name = 'users'

urlpatterns = [
    # 记录用户行为
    path('behavior/', UserBehaviorView.as_view(), name='user_behavior'),
    
    # 获取用户最近浏览记录
    path('recent-views/<str:user_id>/', UserRecentViewsView.as_view(), name='user_recent_views'),
    
    # 获取用户行为统计
    path('behavior-stats/<str:user_id>/', UserBehaviorStatsView.as_view(), name='user_behavior_stats'),
]