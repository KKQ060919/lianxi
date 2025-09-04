from django.urls import path
from .views import (
    RecommendationView,
    UserProfileView,
    RecommendationHistoryView,
    PopularRequirementsView
)

app_name = 'agents'

urlpatterns = [
    # 智能推荐
    path('recommend/', RecommendationView.as_view(), name='recommendation'),
    
    # 用户画像管理
    path('profile/', UserProfileView.as_view(), name='user_profile_create'),
    path('profile/<str:user_id>/', UserProfileView.as_view(), name='user_profile_detail'),
    
    # 推荐历史管理
    path('history/', RecommendationHistoryView.as_view(), name='recommendation_history'),
    
    # 热门需求
    path('popular-requirements/', PopularRequirementsView.as_view(), name='popular_requirements'),
]