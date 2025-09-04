from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import UserBehavior
from .redis import UserBehaviorCache
from product.models import Products
import json

class UserBehaviorView(APIView):
    """用户行为记录API"""
    
    def post(self, request):
        """记录用户行为"""
        try:
            data = request.data
            user_id = data.get('user_id')
            product_id = data.get('product_id')
            action_type = data.get('action_type', 'view')
            
            # 参数验证
            if not user_id or not product_id:
                return Response({
                    'code': 400,
                    'message': '用户ID和商品ID不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证商品是否存在
            try:
                product = Products.objects.get(product_id=product_id)
            except Products.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '商品不存在',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 记录用户行为到数据库
            behavior = UserBehavior.objects.create(
                user_id=user_id,
                product=product,
                action_type=action_type,
                viewed_at=timezone.now()
            )
            
            # 将用户浏览记录添加到Redis
            UserBehaviorCache.add_user_behavior(
                user_id=user_id,
                product_id=product_id,
                product_name=product.name,
                action_type=action_type
            )
            
            return Response({
                'code': 200,
                'message': '行为记录成功',
                'data': {
                    'id': behavior.id,
                    'user_id': user_id,
                    'product_id': product_id,
                    'product_name': product.name,
                    'action_type': action_type,
                    'viewed_at': behavior.viewed_at.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserRecentViewsView(APIView):
    """用户最近浏览记录API"""
    
    def get(self, request, user_id):
        """获取用户最近浏览的商品"""
        try:
            # 优先从Redis获取
            recent_views = UserBehaviorCache.get_user_recent_views(user_id)
            
            if recent_views:
                return Response({
                    'code': 200,
                    'message': '获取成功(缓存)',
                    'data': recent_views
                })
            
            # Redis中没有，从数据库获取
            behaviors = UserBehavior.objects.filter(
                user_id=user_id
            ).select_related('product').order_by('-viewed_at')[:10]
            
            recent_data = []
            for behavior in behaviors:
                recent_data.append({
                    'product_id': behavior.product.product_id,
                    'product_name': behavior.product.name,
                    'price': float(behavior.product.price),
                    'category': behavior.product.category,
                    'brand': behavior.product.brand,
                    'action_type': behavior.action_type,
                    'viewed_at': behavior.viewed_at.isoformat()
                })
            
            # 更新Redis缓存
            for item in recent_data:
                UserBehaviorCache.add_user_behavior(
                    user_id=user_id,
                    product_id=item['product_id'],
                    product_name=item['product_name'],
                    action_type=item['action_type']
                )
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': recent_data
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserBehaviorStatsView(APIView):
    """用户行为统计API"""
    
    def get(self, request, user_id):
        """获取用户行为统计"""
        try:
            # 获取用户各类行为统计
            stats = UserBehaviorCache.get_user_behavior_stats(user_id)
            
            if not stats:
                # 从数据库计算统计
                behaviors = UserBehavior.objects.filter(user_id=user_id)
                
                stats = {
                    'total_views': behaviors.filter(action_type='view').count(),
                    'total_clicks': behaviors.filter(action_type='click').count(),
                    'total_favorites': behaviors.filter(action_type='favorite').count(),
                    'total_behaviors': behaviors.count(),
                    'most_viewed_category': self.get_most_viewed_category(user_id),
                    'recent_activity_days': self.get_recent_activity_days(user_id)
                }
                
                # 缓存统计结果
                UserBehaviorCache.set_user_behavior_stats(user_id, stats)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': stats
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_most_viewed_category(self, user_id):
        """获取用户最常浏览的商品类别"""
        try:
            from django.db.models import Count
            
            result = UserBehavior.objects.filter(
                user_id=user_id
            ).values(
                'product__category'
            ).annotate(
                count=Count('id')
            ).order_by('-count').first()
            
            return result['product__category'] if result else '未知'
        except:
            return '未知'
    
    def get_recent_activity_days(self, user_id):
        """获取用户最近活跃天数"""
        try:
            from django.db.models import Q
            from datetime import timedelta
            
            recent_date = timezone.now() - timedelta(days=7)
            recent_behaviors = UserBehavior.objects.filter(
                user_id=user_id,
                viewed_at__gte=recent_date
            ).dates('viewed_at', 'day')
            
            return len(list(recent_behaviors))
        except:
            return 0