from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView, 
    HotProductsView,
    ProductCategoriesView,
    ProductBrandsView
)

app_name = 'product'

urlpatterns = [
    # 商品列表 - 支持分页和搜索
    path('list/', ProductListView.as_view(), name='product_list'),
    
    # 商品详情
    path('detail/<str:product_id>/', ProductDetailView.as_view(), name='product_detail'),
    
    # 热门商品
    path('hot/', HotProductsView.as_view(), name='hot_products'),
    
    # 商品分类列表
    path('categories/', ProductCategoriesView.as_view(), name='product_categories'),
    
    # 商品品牌列表
    path('brands/', ProductBrandsView.as_view(), name='product_brands'),
]