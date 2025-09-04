from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Products
from .redis import ProductCache
import json

class ProductListView(APIView):
    """商品列表API"""
    
    def get(self, request):
        """获取商品列表，支持分页和搜索"""
        try:
            # 获取查询参数
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 12))
            search = request.GET.get('search', '')
            category = request.GET.get('category', '')
            brand = request.GET.get('brand', '')
            
            # 构建查询条件
            queryset = Products.objects.all()
            
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | 
                    Q(description__icontains=search)
                )
            
            if category:
                queryset = queryset.filter(category=category)
                
            if brand:
                queryset = queryset.filter(brand=brand)
            
            # 按更新时间排序
            queryset = queryset.order_by('-updated_at')
            
            # 分页处理
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # 序列化数据
            products_data = []
            for product in page_obj:
                products_data.append({
                    'id': product.id,
                    'product_id': product.product_id,
                    'name': product.name,
                    'price': float(product.price),
                    'category': product.category,
                    'brand': product.brand,
                    'specifications': product.specifications,
                    'description': product.description,
                    'stock': product.stock,
                    'is_hot': product.is_hot,
                    'updated_at': product.updated_at.isoformat()
                })
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'products': products_data,
                    'pagination': {
                        'current_page': page,
                        'total_pages': paginator.num_pages,
                        'total_count': paginator.count,
                        'has_next': page_obj.has_next(),
                        'has_previous': page_obj.has_previous()
                    }
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductDetailView(APIView):
    """商品详情API"""
    
    def get(self, request, product_id):
        """获取商品详情，优先从Redis缓存获取"""
        try:
            # 先从Redis缓存获取
            cached_data = ProductCache.get_product_detail(product_id)
            if cached_data:
                return Response({
                    'code': 200,
                    'message': '获取成功(缓存)',
                    'data': cached_data
                })
            
            # 缓存中没有，从数据库获取
            product = get_object_or_404(Products, product_id=product_id)
            
            product_data = {
                'id': product.id,
                'product_id': product.product_id,
                'name': product.name,
                'price': float(product.price),
                'category': product.category,
                'brand': product.brand,
                'specifications': product.specifications,
                'description': product.description,
                'stock': product.stock,
                'is_hot': product.is_hot,
                'updated_at': product.updated_at.isoformat()
            }
            
            # 将详情存入Redis缓存
            ProductCache.set_product_detail(product_id, product_data)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': product_data
            })
            
        except Products.DoesNotExist:
            return Response({
                'code': 404,
                'message': '商品不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HotProductsView(APIView):
    """热门商品API"""
    
    def get(self, request):
        """获取热门商品，优先从Redis缓存获取"""
        try:
            # 从Redis获取热门商品
            hot_products = ProductCache.get_hot_products()
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': hot_products
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductCategoriesView(APIView):
    """商品分类API"""
    
    def get(self, request):
        """获取所有商品分类"""
        try:
            categories = Products.objects.values('category').distinct()
            category_list = [item['category'] for item in categories]
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': category_list
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductBrandsView(APIView):
    """商品品牌API"""
    
    def get(self, request):
        """获取所有商品品牌"""
        try:
            brands = Products.objects.values('brand').distinct()
            brand_list = [item['brand'] for item in brands]
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': brand_list
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)