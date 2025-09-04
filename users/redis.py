import redis
import json
import time
from django.conf import settings
from datetime import datetime, timedelta

# Redis连接
redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

class UserBehaviorCache:
    """用户行为缓存管理类"""
    
    USER_RECENT_VIEWS_PREFIX = "user_recent_views:"  # 用户最近浏览键前缀
    USER_BEHAVIOR_STATS_PREFIX = "user_behavior_stats:"  # 用户行为统计键前缀
    MAX_RECENT_VIEWS = 10  # 最多保存的最近浏览记录数
    
    @classmethod
    def add_user_behavior(cls, user_id, product_id, product_name, action_type='view'):
        """添加用户行为记录到Redis"""
        try:
            # 构建浏览记录键
            key = f"{cls.USER_RECENT_VIEWS_PREFIX}{user_id}"
            
            # 构建记录数据
            behavior_data = {
                'product_id': product_id,
                'product_name': product_name,
                'action_type': action_type,
                'timestamp': int(time.time()),
                'viewed_at': datetime.now().isoformat()
            }
            
            # 使用ZSET存储，时间戳作为分数，确保按时间排序
            redis_client.zadd(
                key,
                {json.dumps(behavior_data): behavior_data['timestamp']}
            )
            
            # 只保留最近的N条记录
            redis_client.zremrangebyrank(key, 0, -(cls.MAX_RECENT_VIEWS + 1))
            
            # 设置过期时间：30天
            redis_client.expire(key, 30 * 24 * 3600)
            
            # 更新用户行为统计
            cls._update_behavior_stats(user_id, action_type)
            
            return True
            
        except Exception as e:
            print(f"添加用户行为记录失败: {str(e)}")
            return False
    
    @classmethod
    def get_user_recent_views(cls, user_id, limit=10):
        """获取用户最近浏览记录"""
        try:
            key = f"{cls.USER_RECENT_VIEWS_PREFIX}{user_id}"
            
            # 按分数倒序获取最近的记录
            records = redis_client.zrevrange(key, 0, limit - 1)
            
            recent_views = []
            for record in records:
                try:
                    data = json.loads(record)
                    recent_views.append(data)
                except json.JSONDecodeError:
                    continue
            
            return recent_views
            
        except Exception as e:
            print(f"获取用户最近浏览失败: {str(e)}")
            return []
    
    @classmethod
    def _update_behavior_stats(cls, user_id, action_type):
        """更新用户行为统计"""
        try:
            stats_key = f"{cls.USER_BEHAVIOR_STATS_PREFIX}{user_id}"
            
            # 增加对应行为类型的计数
            redis_client.hincrby(stats_key, f"total_{action_type}s", 1)
            redis_client.hincrby(stats_key, "total_behaviors", 1)
            
            # 更新最后活跃时间
            redis_client.hset(stats_key, "last_active", datetime.now().isoformat())
            
            # 设置过期时间：30天
            redis_client.expire(stats_key, 30 * 24 * 3600)
            
            return True
            
        except Exception as e:
            print(f"更新用户行为统计失败: {str(e)}")
            return False
    
    @classmethod
    def get_user_behavior_stats(cls, user_id):
        """获取用户行为统计"""
        try:
            stats_key = f"{cls.USER_BEHAVIOR_STATS_PREFIX}{user_id}"
            
            stats_data = redis_client.hgetall(stats_key)
            
            if not stats_data:
                return None
            
            # 转换数据类型
            stats = {}
            for key, value in stats_data.items():
                if key.startswith('total_'):
                    stats[key] = int(value) if value.isdigit() else 0
                else:
                    stats[key] = value
            
            return stats
            
        except Exception as e:
            print(f"获取用户行为统计失败: {str(e)}")
            return None
    
    @classmethod
    def set_user_behavior_stats(cls, user_id, stats):
        """设置用户行为统计"""
        try:
            stats_key = f"{cls.USER_BEHAVIOR_STATS_PREFIX}{user_id}"
            
            # 清除旧数据
            redis_client.delete(stats_key)
            
            # 设置新数据
            for key, value in stats.items():
                redis_client.hset(stats_key, key, str(value))
            
            # 设置过期时间：30天
            redis_client.expire(stats_key, 30 * 24 * 3600)
            
            return True
            
        except Exception as e:
            print(f"设置用户行为统计失败: {str(e)}")
            return False
    
    @classmethod
    def get_user_category_preferences(cls, user_id, days=30):
        """获取用户分类偏好分析"""
        try:
            key = f"{cls.USER_RECENT_VIEWS_PREFIX}{user_id}"
            
            # 获取指定天数内的记录
            cutoff_time = int(time.time()) - (days * 24 * 3600)
            records = redis_client.zrangebyscore(key, cutoff_time, '+inf')
            
            category_counts = {}
            for record in records:
                try:
                    data = json.loads(record)
                    # 这里需要从product_name推断分类，或者在记录时包含分类信息
                    # 简化处理：从商品名称推断
                    category = cls._infer_category_from_name(data.get('product_name', ''))
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            # 按浏览次数排序
            sorted_preferences = sorted(
                category_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return dict(sorted_preferences)
            
        except Exception as e:
            print(f"获取用户分类偏好失败: {str(e)}")
            return {}
    
    @classmethod
    def _infer_category_from_name(cls, product_name):
        """从商品名称推断分类"""
        if not product_name:
            return None
        
        # 简单的分类推断逻辑
        name_lower = product_name.lower()
        if any(word in name_lower for word in ['iphone', '手机', 'phone', 'mate', 'galaxy']):
            return '手机'
        elif any(word in name_lower for word in ['airpods', '耳机', 'buds', 'headphone']):
            return '耳机'
        elif any(word in name_lower for word in ['macbook', '电脑', 'laptop', 'computer']):
            return '电脑'
        elif any(word in name_lower for word in ['ipad', '平板', 'tablet']):
            return '平板'
        else:
            return '其他'
    
    @classmethod
    def clear_user_cache(cls, user_id):
        """清除用户所有缓存"""
        try:
            # 清除用户浏览记录
            views_key = f"{cls.USER_RECENT_VIEWS_PREFIX}{user_id}"
            redis_client.delete(views_key)
            
            # 清除用户行为统计
            stats_key = f"{cls.USER_BEHAVIOR_STATS_PREFIX}{user_id}"
            redis_client.delete(stats_key)
            
            return True
            
        except Exception as e:
            print(f"清除用户缓存失败: {str(e)}")
            return False
    
    @classmethod
    def get_all_users_recent_activity(cls, limit=100):
        """获取所有用户的最近活动（用于推荐系统）"""
        try:
            # 使用SCAN命令遍历所有用户浏览记录键
            pattern = f"{cls.USER_RECENT_VIEWS_PREFIX}*"
            all_activities = []
            
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    user_id = key.replace(cls.USER_RECENT_VIEWS_PREFIX, '')
                    recent_views = cls.get_user_recent_views(user_id, 5)  # 获取最近5条
                    
                    if recent_views:
                        all_activities.append({
                            'user_id': user_id,
                            'recent_views': recent_views
                        })
                
                if cursor == 0:
                    break
                    
                if len(all_activities) >= limit:
                    break
            
            return all_activities[:limit]
            
        except Exception as e:
            print(f"获取所有用户活动失败: {str(e)}")
            return []

