from django.core.management.base import BaseCommand
from django.utils import timezone
from product.models import Products
from Agents.models import UserProfile
from rag.models import ProductKnowledge
from users.models import UserBehavior
import random
from decimal import Decimal
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = '生成模拟数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=int,
            default=15,
            help='生成商品数量（默认15）'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='生成用户画像数量（默认10）'
        )
        parser.add_argument(
            '--knowledge',
            type=int,
            default=50,
            help='生成商品知识数量（默认50）'
        )
        parser.add_argument(
            '--behaviors',
            type=int,
            default=100,
            help='生成用户行为数量（默认100）'
        )

    def handle(self, *args, **options):
        self.stdout.write('开始生成模拟数据...')
        
        # 清空现有数据（可选）
        if input("是否清空现有数据？(y/N): ").lower() == 'y':
            UserBehavior.objects.all().delete()
            ProductKnowledge.objects.all().delete()
            UserProfile.objects.all().delete()
            Products.objects.all().delete()
            self.stdout.write('已清空现有数据')

        # 生成商品数据
        self.generate_products(options['products'])
        
        # 生成用户画像数据
        self.generate_user_profiles(options['users'])
        
        # 生成商品知识数据
        self.generate_product_knowledge(options['knowledge'])
        
        # 生成用户行为数据
        self.generate_user_behaviors(options['behaviors'])

        self.stdout.write(
            self.style.SUCCESS('模拟数据生成完成！')
        )

    def generate_products(self, count):
        """生成商品数据"""
        self.stdout.write(f'正在生成 {count} 条商品数据...')
        
        categories = ['手机', '耳机', '电脑', '平板', '智能手表', '音响']
        brands = ['苹果', '华为', '小米', '三星', 'OPPO', 'vivo', '索尼', '戴尔', 'HP']
        
        products_data = [
            # 手机类
            {'name': 'iPhone 15 Pro', 'category': '手机', 'brand': '苹果', 'price': '7999.00'},
            {'name': 'iPhone 15', 'category': '手机', 'brand': '苹果', 'price': '5999.00'},
            {'name': 'Mate 60 Pro', 'category': '手机', 'brand': '华为', 'price': '6999.00'},
            {'name': 'P60 Pro', 'category': '手机', 'brand': '华为', 'price': '5988.00'},
            {'name': '小米14 Pro', 'category': '手机', 'brand': '小米', 'price': '4999.00'},
            {'name': 'Galaxy S24 Ultra', 'category': '手机', 'brand': '三星', 'price': '9999.00'},
            
            # 耳机类
            {'name': 'AirPods Pro 2', 'category': '耳机', 'brand': '苹果', 'price': '1899.00'},
            {'name': 'FreeBuds Pro 3', 'category': '耳机', 'brand': '华为', 'price': '1199.00'},
            {'name': '小米FlipBuds Pro', 'category': '耳机', 'brand': '小米', 'price': '699.00'},
            {'name': 'WH-1000XM5', 'category': '耳机', 'brand': '索尼', 'price': '2399.00'},
            
            # 电脑类
            {'name': 'MacBook Pro 14', 'category': '电脑', 'brand': '苹果', 'price': '14999.00'},
            {'name': 'MateBook X Pro', 'category': '电脑', 'brand': '华为', 'price': '8999.00'},
            {'name': 'XPS 13', 'category': '电脑', 'brand': '戴尔', 'price': '7999.00'},
            
            # 平板类
            {'name': 'iPad Pro 12.9', 'category': '平板', 'brand': '苹果', 'price': '8999.00'},
            {'name': 'MatePad Pro', 'category': '平板', 'brand': '华为', 'price': '3999.00'},
        ]

        for i, product_info in enumerate(products_data[:count]):
            # 生成规格参数
            specs = {}
            if product_info['category'] == '手机':
                specs = {
                    '内存': random.choice(['128GB', '256GB', '512GB', '1TB']),
                    '颜色': random.choice(['黑色', '白色', '蓝色', '紫色', '金色']),
                    '运行内存': random.choice(['8GB', '12GB', '16GB']),
                    '屏幕尺寸': random.choice(['6.1英寸', '6.7英寸', '6.8英寸'])
                }
            elif product_info['category'] == '耳机':
                specs = {
                    '类型': random.choice(['入耳式', '头戴式', '颈挂式']),
                    '颜色': random.choice(['黑色', '白色', '银色']),
                    '降噪': random.choice(['主动降噪', '被动降噪', '无降噪'])
                }
            elif product_info['category'] == '电脑':
                specs = {
                    '处理器': random.choice(['M3 Pro', 'Intel i7', 'AMD R7']),
                    '内存': random.choice(['16GB', '32GB', '64GB']),
                    '存储': random.choice(['512GB SSD', '1TB SSD', '2TB SSD']),
                    '屏幕': random.choice(['13.3英寸', '14英寸', '15.6英寸'])
                }

            Products.objects.create(
                product_id=f'P{str(i+1).zfill(4)}',
                name=product_info['name'],
                price=Decimal(product_info['price']),
                category=product_info['category'],
                brand=product_info['brand'],
                specifications=specs,
                description=f'{product_info["brand"]}{product_info["name"]}，{product_info["category"]}类产品的优秀代表',
                stock=random.randint(50, 500),
                is_hot=random.choice([True, False])
            )

        self.stdout.write(f'已生成 {count} 条商品数据')

    def generate_user_profiles(self, count):
        """生成用户画像数据"""
        self.stdout.write(f'正在生成 {count} 条用户画像数据...')
        
        categories = ['手机', '耳机', '电脑', '平板', '智能手表', '音响']
        price_ranges = ['1000-3000', '3000-5000', '5000-8000', '8000-15000', '15000+']

        for i in range(count):
            UserProfile.objects.create(
                user_id=f'U{str(i+1).zfill(4)}',
                preferred_categories=random.sample(categories, random.randint(1, 3)),
                price_preference=random.choice(price_ranges)
            )

        self.stdout.write(f'已生成 {count} 条用户画像数据')

    def generate_product_knowledge(self, count):
        """生成商品知识数据"""
        self.stdout.write(f'正在生成 {count} 条商品知识数据...')
        
        products = list(Products.objects.all())
        if not products:
            self.stdout.write('没有商品数据，跳过知识数据生成')
            return

        # 知识属性模板
        knowledge_templates = {
            '手机': [
                ('支持网络', ['支持5G网络', '支持4G网络', '支持双卡双待']),
                ('充电功能', ['支持无线充电', '支持快充', '支持反向充电']),
                ('摄像功能', ['支持夜景模式', '支持人像模式', '支持超广角']),
                ('防护等级', ['IP68防水', 'IP67防水', '不支持防水']),
                ('生物识别', ['支持Face ID', '支持指纹识别', '支持虹膜识别'])
            ],
            '耳机': [
                ('降噪功能', ['主动降噪', '被动降噪', '环境音透传']),
                ('连接方式', ['蓝牙5.3连接', '有线连接', '无线连接']),
                ('电池续航', ['续航6小时', '续航8小时', '续航10小时']),
                ('音质特点', ['HiFi音质', '低音增强', '人声清晰']),
                ('佩戴方式', ['入耳式设计', '头戴式设计', '挂耳式设计'])
            ],
            '电脑': [
                ('性能特点', ['高性能处理器', '独立显卡', '集成显卡']),
                ('存储配置', ['SSD固态硬盘', '大容量内存', '扩展性强']),
                ('屏幕特性', ['高分辨率屏幕', 'IPS屏幕', 'OLED屏幕']),
                ('接口配置', ['多USB接口', 'Type-C接口', 'HDMI接口']),
                ('散热设计', ['双风扇散热', '液冷散热', '静音设计'])
            ],
            '平板': [
                ('屏幕特性', ['高刷新率', '防蓝光', '高亮度']),
                ('系统特点', ['多任务处理', '手写笔支持', '键盘支持']),
                ('存储扩展', ['支持存储卡', '云存储同步', '大容量存储']),
                ('娱乐功能', ['游戏性能优秀', '视频播放流畅', '阅读体验佳']),
                ('便携性', ['轻薄设计', '长续航', '快速充电'])
            ]
        }

        created_count = 0
        for _ in range(count):
            product = random.choice(products)
            category = product.category
            
            if category in knowledge_templates:
                templates = knowledge_templates[category]
                attribute, values = random.choice(templates)
                value = random.choice(values)
                
                # 避免重复的属性-商品组合
                existing = ProductKnowledge.objects.filter(
                    product=product, 
                    attribute=attribute
                ).exists()
                
                if not existing:
                    ProductKnowledge.objects.create(
                        product=product,
                        attribute=attribute,
                        value=value,
                        source_text=f'{product.name}产品说明书中关于{attribute}的描述：{value}'
                    )
                    created_count += 1
                    
                    if created_count >= count:
                        break

        self.stdout.write(f'已生成 {created_count} 条商品知识数据')

    def generate_user_behaviors(self, count):
        """生成用户行为数据"""
        self.stdout.write(f'正在生成 {count} 条用户行为数据...')
        
        products = list(Products.objects.all())
        user_profiles = list(UserProfile.objects.all())
        
        if not products:
            self.stdout.write('没有商品数据，跳过行为数据生成')
            return
            
        if not user_profiles:
            self.stdout.write('没有用户数据，跳过行为数据生成')
            return

        action_types = ['view', 'click', 'favorite', 'cart', 'purchase']
        
        for i in range(count):
            user_profile = random.choice(user_profiles)
            product = random.choice(products)
            
            # 根据用户偏好增加相关商品的浏览概率
            if product.category in user_profile.preferred_categories:
                # 偏好商品有更高概率被浏览
                if random.random() > 0.3:  # 70%概率选择偏好商品
                    pass
                else:
                    product = random.choice(products)
            
            # 生成随机的浏览时间（过去30天内）
            days_ago = random.randint(1, 30)
            viewed_time = timezone.now() - timedelta(days=days_ago)
            
            UserBehavior.objects.create(
                user_id=user_profile.user_id,
                product=product,
                viewed_at=viewed_time,
                action_type=random.choice(action_types)
            )

        self.stdout.write(f'已生成 {count} 条用户行为数据')

