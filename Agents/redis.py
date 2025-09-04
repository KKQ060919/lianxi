import redis
import json
import time
from datetime import datetime
from config import REDIS_CONFIG

# Redis连接 - 使用专门的数据库存储智能推荐
redis_client = redis.Redis(
    host=REDIS_CONFIG['host'], 
    port=REDIS_CONFIG['port'], 
    db=REDIS_CONFIG['agents_db'], 
    decode_responses=True
)

class RecommendationCache:
    """智能推荐缓存管理类"""
    
    # Redis键前缀定义
    USER_RECOMMENDATIONS_PREFIX = "user_recommendations:"  # 用户推荐历史键前缀
    RECOMMENDATION_DETAIL_PREFIX = "recommendation_detail:"  # 推荐详情键前缀
    POPULAR_REQUIREMENTS_KEY = "popular_requirements"  # 热门需求键
    USER_PREFERENCES_PREFIX = "user_preferences:"  # 用户偏好键前缀
    RECOMMENDATION_STATS_KEY = "recommendation_stats"  # 推荐统计键
    
    @classmethod
    def save_recommendation(cls, user_id, requirement, recommendation_text, products=None, session_id=None):
        """
        保存智能推荐记录到Redis
        
        Args:
            user_id: 用户ID
            requirement: 用户需求描述
            recommendation_text: AI推荐内容
            products: 推荐的商品列表
            session_id: 会话ID（用于匿名用户）
        
        Returns:
            str: 推荐记录ID，如果保存失败则返回None
        """
        try:
            # 生成推荐记录ID
            recommendation_id = f"rec_{int(time.time() * 1000)}"
            current_time = datetime.now()
            timestamp = int(time.time())
            
            # 构建推荐数据
            recommendation_data = {
                'recommendation_id': recommendation_id,
                'user_id': user_id or 'anonymous',
                'session_id': session_id or '',
                'requirement': requirement,
                'recommendation_text': recommendation_text,
                'products': products or [],
                'timestamp': timestamp,
                'created_at': current_time.isoformat(),
                'requirement_length': len(requirement),
                'recommendation_length': len(recommendation_text),
                'product_count': len(products) if products else 0
            }
            
            # 保存推荐详情
            detail_key = f"{cls.RECOMMENDATION_DETAIL_PREFIX}{recommendation_id}"
            redis_client.setex(
                detail_key,
                REDIS_CONFIG['default_expire'],
                json.dumps(recommendation_data,ensure_ascii= False)
            )
            
            # 添加到用户推荐列表（使用ZSET按时间排序）
            list_key = f"{cls.USER_RECOMMENDATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 推荐简要信息，用于列表显示
            recommendation_summary = {
                'recommendation_id': recommendation_id,
                'requirement': requirement[:50] + "..." if len(requirement) > 50 else requirement,
                'product_count': len(products) if products else 0,
                'timestamp': timestamp,
                'created_at': current_time.isoformat()
            }
            
            # 使用ZADD添加到有序集合，时间戳作为分数
            redis_client.zadd(
                list_key,
                {json.dumps(recommendation_summary): timestamp}
            )
            
            # 只保留最近的N条推荐
            redis_client.zremrangebyrank(
                list_key, 
                0, 
                -(REDIS_CONFIG['max_recommendations'] + 1)
            )
            
            # 设置用户推荐列表过期时间
            redis_client.expire(list_key, REDIS_CONFIG['default_expire'])
            
            # 更新热门需求统计
            cls._update_popular_requirements(requirement)
            
            # 更新推荐统计
            cls._update_recommendation_stats()
            
            print(f"智能推荐已保存: {recommendation_id}")
            return recommendation_id
            
        except Exception as e:
            print(f"保存智能推荐失败: {str(e)}")
            return None
    
    @classmethod
    def get_recommendation_detail(cls, recommendation_id):
        """
        获取推荐详情
        
        Args:
            recommendation_id: 推荐ID
            
        Returns:
            dict: 推荐详情数据，如果不存在则返回None
        """
        try:
            detail_key = f"{cls.RECOMMENDATION_DETAIL_PREFIX}{recommendation_id}"
            cached_data = redis_client.get(detail_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"获取推荐详情失败: {str(e)}")
            return None
    
    @classmethod
    def get_user_recommendations(cls, user_id=None, session_id=None, limit=20):
        """
        获取用户的推荐历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（匿名用户）
            limit: 返回数量限制
            
        Returns:
            list: 推荐历史列表
        """
        try:
            list_key = f"{cls.USER_RECOMMENDATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 按时间倒序获取推荐列表
            recommendations = redis_client.zrevrange(list_key, 0, limit - 1)
            
            recommendation_list = []
            for rec_data in recommendations:
                try:
                    rec_info = json.loads(rec_data)
                    recommendation_list.append(rec_info)
                except json.JSONDecodeError:
                    continue
            
            return recommendation_list
            
        except Exception as e:
            print(f"获取用户推荐历史失败: {str(e)}")
            return []
    
    @classmethod
    def save_user_preferences(cls, user_id, preferences):
        """
        保存用户偏好信息
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            prefs_key = f"{cls.USER_PREFERENCES_PREFIX}{user_id}"
            
            # 添加时间戳
            preferences['updated_at'] = datetime.now().isoformat()
            preferences['updated_timestamp'] = int(time.time())
            
            # 保存偏好信息
            redis_client.setex(
                prefs_key,
                REDIS_CONFIG['default_expire'],
                json.dumps(preferences)
            )
            
            print(f"用户偏好已保存: {user_id}")
            return True
            
        except Exception as e:
            print(f"保存用户偏好失败: {str(e)}")
            return False
    
    @classmethod
    def get_user_preferences(cls, user_id):
        """
        获取用户偏好信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户偏好，如果不存在则返回None
        """
        try:
            prefs_key = f"{cls.USER_PREFERENCES_PREFIX}{user_id}"
            cached_data = redis_client.get(prefs_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"获取用户偏好失败: {str(e)}")
            return None
    
    @classmethod
    def _update_popular_requirements(cls, requirement):
        """
        更新热门需求统计（私有方法）
        
        Args:
            requirement: 用户需求
        """
        try:
            # 简化需求描述（去除标点符号，转为小写）
            simplified_requirement = requirement.lower().strip()[:50]
            
            # 使用ZSET存储热门需求，分数为出现次数
            redis_client.zincrby(cls.POPULAR_REQUIREMENTS_KEY, 1, simplified_requirement)
            
            # 只保留前50个热门需求
            redis_client.zremrangebyrank(cls.POPULAR_REQUIREMENTS_KEY, 0, -51)
            
            # 设置过期时间（30天）
            redis_client.expire(cls.POPULAR_REQUIREMENTS_KEY, 30 * 24 * 3600)
            
        except Exception as e:
            print(f"更新热门需求失败: {str(e)}")
    
    @classmethod
    def get_popular_requirements(cls, limit=10):
        """
        获取热门需求列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            list: 热门需求列表，按热度排序
        """
        try:
            # 按分数倒序获取热门需求
            popular_requirements = redis_client.zrevrange(
                cls.POPULAR_REQUIREMENTS_KEY, 
                0, 
                limit - 1,
                withscores=True
            )
            
            requirements_list = []
            for requirement, score in popular_requirements:
                requirements_list.append({
                    'requirement': requirement,
                    'count': int(score)
                })
            
            return requirements_list
            
        except Exception as e:
            print(f"获取热门需求失败: {str(e)}")
            return []
    
    @classmethod
    def _update_recommendation_stats(cls):
        """
        更新推荐统计信息（私有方法）
        """
        try:
            # 增加总推荐数量
            redis_client.hincrby(cls.RECOMMENDATION_STATS_KEY, "total_recommendations", 1)
            
            # 更新今日推荐数量
            today = datetime.now().strftime('%Y-%m-%d')
            redis_client.hincrby(cls.RECOMMENDATION_STATS_KEY, f"daily_{today}", 1)
            
            # 更新最后推荐时间
            redis_client.hset(cls.RECOMMENDATION_STATS_KEY, "last_recommendation", datetime.now().isoformat())
            
            # 设置过期时间（30天）
            redis_client.expire(cls.RECOMMENDATION_STATS_KEY, 30 * 24 * 3600)
            
        except Exception as e:
            print(f"更新推荐统计失败: {str(e)}")
    
    @classmethod
    def get_recommendation_stats(cls):
        """
        获取推荐统计信息
        
        Returns:
            dict: 推荐统计数据
        """
        try:
            stats_data = redis_client.hgetall(cls.RECOMMENDATION_STATS_KEY)
            
            if not stats_data:
                return {
                    'total_recommendations': 0,
                    'daily_recommendations': 0,
                    'last_recommendation': None
                }
            
            # 获取今日推荐数量
            today = datetime.now().strftime('%Y-%m-%d')
            daily_count = stats_data.get(f"daily_{today}", "0")
            
            return {
                'total_recommendations': int(stats_data.get('total_recommendations', 0)),
                'daily_recommendations': int(daily_count),
                'last_recommendation': stats_data.get('last_recommendation')
            }
            
        except Exception as e:
            print(f"获取推荐统计失败: {str(e)}")
            return {
                'total_recommendations': 0,
                'daily_recommendations': 0,
                'last_recommendation': None
            }
    
    @classmethod
    def search_recommendations(cls, user_id=None, session_id=None, keyword="", limit=10):
        """
        搜索用户的推荐记录
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（匿名用户）
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            list: 匹配的推荐记录
        """
        try:
            # 获取用户所有推荐
            recommendations = cls.get_user_recommendations(user_id, session_id, 50)
            
            if not keyword:
                return recommendations[:limit]
            
            # 简单的关键词匹配
            matched_recommendations = []
            keyword_lower = keyword.lower()
            
            for rec in recommendations:
                if (keyword_lower in rec.get('requirement', '').lower() and 
                    len(matched_recommendations) < limit):
                    matched_recommendations.append(rec)
                
                if len(matched_recommendations) >= limit:
                    break
            
            return matched_recommendations
            
        except Exception as e:
            print(f"搜索推荐记录失败: {str(e)}")
            return []
    
    @classmethod
    def delete_recommendation(cls, recommendation_id, user_id=None, session_id=None):
        """
        删除指定推荐记录
        
        Args:
            recommendation_id: 推荐ID
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 删除推荐详情
            detail_key = f"{cls.RECOMMENDATION_DETAIL_PREFIX}{recommendation_id}"
            redis_client.delete(detail_key)
            
            # 从用户推荐列表中移除（需要遍历找到匹配的记录）
            list_key = f"{cls.USER_RECOMMENDATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            recommendations = redis_client.zrange(list_key, 0, -1)
            
            for rec_data in recommendations:
                try:
                    rec_info = json.loads(rec_data)
                    if rec_info.get('recommendation_id') == recommendation_id:
                        redis_client.zrem(list_key, rec_data)
                        break
                except json.JSONDecodeError:
                    continue
            
            print(f"推荐记录已删除: {recommendation_id}")
            return True
            
        except Exception as e:
            print(f"删除推荐记录失败: {str(e)}")
            return False
    
    @classmethod
    def clear_user_recommendations(cls, user_id=None, session_id=None):
        """
        清空用户所有推荐记录
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            bool: 清空是否成功
        """
        try:
            list_key = f"{cls.USER_RECOMMENDATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 获取所有推荐ID并删除详情
            recommendations = redis_client.zrange(list_key, 0, -1)
            for rec_data in recommendations:
                try:
                    rec_info = json.loads(rec_data)
                    recommendation_id = rec_info.get('recommendation_id')
                    if recommendation_id:
                        detail_key = f"{cls.RECOMMENDATION_DETAIL_PREFIX}{recommendation_id}"
                        redis_client.delete(detail_key)
                except json.JSONDecodeError:
                    continue
            
            # 删除推荐列表
            redis_client.delete(list_key)
            
            # 清除用户偏好
            prefs_key = f"{cls.USER_PREFERENCES_PREFIX}{user_id or session_id or 'anonymous'}"
            redis_client.delete(prefs_key)
            
            print(f"用户推荐记录已清空: {user_id or session_id or 'anonymous'}")
            return True
            
        except Exception as e:
            print(f"清空用户推荐记录失败: {str(e)}")
            return False
    
    @classmethod
    def get_user_recommendation_statistics(cls, user_id=None, session_id=None):
        """
        获取用户推荐统计信息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            dict: 统计信息
        """
        try:
            list_key = f"{cls.USER_RECOMMENDATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 获取推荐数量
            total_recommendations = redis_client.zcard(list_key)
            
            # 获取最近的推荐
            recent_recommendations = redis_client.zrevrange(list_key, 0, 9)
            
            # 统计详细信息
            total_requirements = 0
            total_responses = 0
            total_products = 0
            
            for rec_data in recent_recommendations:
                try:
                    rec_info = json.loads(rec_data)
                    recommendation_id = rec_info.get('recommendation_id')
                    if recommendation_id:
                        detail = cls.get_recommendation_detail(recommendation_id)
                        if detail:
                            total_requirements += detail.get('requirement_length', 0)
                            total_responses += detail.get('recommendation_length', 0)
                            total_products += detail.get('product_count', 0)
                except json.JSONDecodeError:
                    continue
            
            return {
                'total_recommendations': total_recommendations,
                'total_requirement_chars': total_requirements,
                'total_response_chars': total_responses,
                'total_recommended_products': total_products,
                'user_id': user_id or session_id or 'anonymous'
            }
            
        except Exception as e:
            print(f"获取用户推荐统计失败: {str(e)}")
            return {
                'total_recommendations': 0,
                'total_requirement_chars': 0,
                'total_response_chars': 0,
                'total_recommended_products': 0,
                'user_id': user_id or session_id or 'anonymous'
            }

# 导出主要的缓存管理类
__all__ = ['RecommendationCache']

