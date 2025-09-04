from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .Agents封装 import recommendation_agent
from .models import UserProfile
from .redis import RecommendationCache
from django.shortcuts import get_object_or_404
import json

class RecommendationView(APIView):
    """智能推荐API"""
    
    def post(self, request):
        """获取个性化推荐"""
        try:
            data = request.data
            user_id = data.get('user_id', '')
            session_id = data.get('session_id', '')  # 支持匿名用户
            requirement = data.get('requirement', '推荐适合的商品')
            
            # 参数验证（允许匿名用户）
            if not user_id and not session_id:
                return Response({
                    'code': 400,
                    'message': '用户ID或会话ID不能同时为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 调用推荐Agent
            result = recommendation_agent.get_recommendations(user_id or 'anonymous', requirement)
            
            if result['success']:
                # 提取推荐的商品信息（如果有的话）
                recommended_products = []
                recommendation_text = result['recommendation']
                
                # 保存推荐记录到Redis
                recommendation_id = RecommendationCache.save_recommendation(
                    user_id=user_id if user_id else None,
                    requirement=requirement,
                    recommendation_text=recommendation_text,
                    products=recommended_products,
                    session_id=session_id if session_id else None
                )
                
                return Response({
                    'code': 200,
                    'message': '推荐成功',
                    'data': {
                        'recommendation_id': recommendation_id,  # 返回推荐记录ID
                        'user_id': user_id or 'anonymous',
                        'requirement': requirement,
                        'recommendation': recommendation_text,
                        'timestamp': result['timestamp']
                    }
                })
            else:
                # 即使失败也保存记录，便于分析问题
                recommendation_id = RecommendationCache.save_recommendation(
                    user_id=user_id if user_id else None,
                    requirement=requirement,
                    recommendation_text=result.get('recommendation', '推荐系统暂时不可用'),
                    products=[],
                    session_id=session_id if session_id else None
                )
                
                return Response({
                    'code': 500,
                    'message': '推荐失败',
                    'data': {
                        'recommendation_id': recommendation_id,
                        'user_id': user_id or 'anonymous',
                        'requirement': requirement,
                        'error': result.get('error', '未知错误'),
                        'recommendation': result.get('recommendation', '推荐系统暂时不可用')
                    }
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    """用户画像API"""
    
    def get(self, request, user_id):
        """获取用户画像"""
        try:
            profile = get_object_or_404(UserProfile, user_id=user_id)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'user_id': profile.user_id,
                    'preferred_categories': profile.preferred_categories,
                    'price_preference': profile.price_preference,
                    'update_time': profile.update_time.isoformat()
                }
            })
            
        except UserProfile.DoesNotExist:
            return Response({
                'code': 404,
                'message': '用户画像不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """创建或更新用户画像"""
        try:
            data = request.data
            user_id = data.get('user_id')
            preferred_categories = data.get('preferred_categories', [])
            price_preference = data.get('price_preference', '')
            
            # 参数验证
            if not user_id:
                return Response({
                    'code': 400,
                    'message': '用户ID不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新用户偏好
            result = recommendation_agent.update_user_preference(
                user_id=user_id,
                preferred_categories=preferred_categories,
                price_preference=price_preference
            )
            
            if result['success']:
                return Response({
                    'code': 200,
                    'message': '用户画像更新成功',
                    'data': {
                        'user_id': user_id,
                        'preferred_categories': preferred_categories,
                        'price_preference': price_preference
                    }
                })
            else:
                return Response({
                    'code': 500,
                    'message': result['message'],
                    'data': None
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecommendationHistoryView(APIView):
    """推荐历史管理API"""
    
    def get(self, request):
        """获取用户推荐历史"""
        try:
            user_id = request.GET.get('user_id', '')
            session_id = request.GET.get('session_id', '')
            limit = int(request.GET.get('limit', 20))
            
            # 获取推荐历史
            recommendations = RecommendationCache.get_user_recommendations(
                user_id=user_id if user_id else None,
                session_id=session_id if session_id else None,
                limit=limit
            )
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'recommendations': recommendations,
                    'total_count': len(recommendations),
                    'user_id': user_id or session_id or 'anonymous'
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取推荐历史失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """删除指定推荐记录"""
        try:
            data = request.data
            recommendation_id = data.get('recommendation_id')
            user_id = data.get('user_id', '')
            session_id = data.get('session_id', '')
            
            if not recommendation_id:
                return Response({
                    'code': 400,
                    'message': '推荐记录ID不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 删除推荐记录
            success = RecommendationCache.delete_recommendation(
                recommendation_id=recommendation_id,
                user_id=user_id if user_id else None,
                session_id=session_id if session_id else None
            )
            
            if success:
                return Response({
                    'code': 200,
                    'message': '推荐记录删除成功',
                    'data': {
                        'recommendation_id': recommendation_id
                    }
                })
            else:
                return Response({
                    'code': 404,
                    'message': '推荐记录不存在或删除失败',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'删除推荐记录失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PopularRequirementsView(APIView):
    """热门需求API"""
    
    def get(self, request):
        """获取热门需求列表"""
        try:
            limit = int(request.GET.get('limit', 10))
            
            popular_requirements = RecommendationCache.get_popular_requirements(limit)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'popular_requirements': popular_requirements,
                    'total_count': len(popular_requirements)
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取热门需求失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
