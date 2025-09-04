import redis
import json
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from .models import Products

# Redis连接
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class ProductCache:
    """商品缓存管理类"""
    
    HOT_PRODUCTS_KEY = "hot_products"  # 热门商品缓存键
    PRODUCT_DETAIL_PREFIX = "product_detail:"  # 商品详情缓存键前缀
    
    @classmethod
    def init_hot_products(cls):
        """项目启动时预热热门商品到Redis"""
        try:
            # 获取所有热门商品
            hot_products = Products.objects.filter(is_hot=True).order_by('-updated_at')[:20]
            
            # 构建商品数据
            products_data = []
            for product in hot_products:
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
                products_data.append(product_data)
                
                # 同时缓存单个商品详情，过期时间1小时
                cls.set_product_detail(product.product_id, product_data, expire=3600)
            
            # 将热门商品列表存入Redis，过期时间30分钟
            redis_client.setex(
                cls.HOT_PRODUCTS_KEY, 
                1800,  # 30分钟
                json.dumps(products_data, cls=DjangoJSONEncoder)
            )
            
            print(f"已预热 {len(products_data)} 个热门商品到Redis")
            return True
            
        except Exception as e:
            print(f"Redis预热失败: {str(e)}")
            return False
    
    @classmethod
    def get_hot_products(cls):
        """获取热门商品，优先从Redis获取"""
        try:
            # 尝试从Redis获取
            cached_data = redis_client.get(cls.HOT_PRODUCTS_KEY)
            if cached_data:
                return json.loads(cached_data)
            
            # Redis中没有，从数据库获取并缓存
            cls.init_hot_products()
            cached_data = redis_client.get(cls.HOT_PRODUCTS_KEY)
            if cached_data:
                return json.loads(cached_data)
            
            return []
            
        except Exception as e:
            print(f"获取热门商品失败: {str(e)}")
            return []
    
    @classmethod
    def set_product_detail(cls, product_id, product_data, expire=3600):
        """缓存商品详情"""
        try:
            key = f"{cls.PRODUCT_DETAIL_PREFIX}{product_id}"
            redis_client.setex(
                key,
                expire,
                json.dumps(product_data, cls=DjangoJSONEncoder)
            )
            return True
        except Exception as e:
            print(f"缓存商品详情失败: {str(e)}")
            return False
    
    @classmethod
    def get_product_detail(cls, product_id):
        """获取商品详情，优先从Redis获取"""
        try:
            key = f"{cls.PRODUCT_DETAIL_PREFIX}{product_id}"
            cached_data = redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"获取商品详情失败: {str(e)}")
            return None
    
    @classmethod
    def clear_product_cache(cls, product_id=None):
        """清除商品缓存"""
        try:
            if product_id:
                # 清除指定商品缓存
                key = f"{cls.PRODUCT_DETAIL_PREFIX}{product_id}"
                redis_client.delete(key)
            else:
                # 清除所有商品相关缓存
                redis_client.delete(cls.HOT_PRODUCTS_KEY)
                # 清除所有商品详情缓存
                pattern = f"{cls.PRODUCT_DETAIL_PREFIX}*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"清除缓存失败: {str(e)}")
            return False

