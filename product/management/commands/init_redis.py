from django.core.management.base import BaseCommand
from product.redis import ProductCache

class Command(BaseCommand):
    help = '初始化Redis缓存，预热热门商品数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化Redis缓存...')
        
        # 预热热门商品
        success = ProductCache.init_hot_products()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('Redis缓存初始化成功！')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Redis缓存初始化失败！')
            )

