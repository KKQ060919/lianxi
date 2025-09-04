from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from product.models import Products
from users.models import UserBehavior
from users.redis import UserBehaviorCache
from .models import UserProfile
from rag.RAG封装 import rag_system
from config import API_CONFIG, AGENT_CONFIG

class IntelligentRecommendationAgent:
    """智能商品推荐Agent系统"""
    
    def __init__(self):
        """初始化推荐Agent"""
        # 初始化大语言模型
        self.llm = ChatOpenAI(
            api_key=API_CONFIG['qwen_api_key'],
            base_url=API_CONFIG['qwen_base_url'],
            model=API_CONFIG['qwen_model'],
            temperature=0.7
        )
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 创建prompt模板
        self.prompt = self._create_prompt()
        
        # 创建agent
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        
        # 创建agent执行器 - 修复最大迭代次数问题
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=AGENT_CONFIG['verbose'],
            max_iterations=AGENT_CONFIG['max_iterations'],
            handle_parsing_errors=AGENT_CONFIG['handle_parsing_errors']
        )
    
    def _create_tools(self):
        """创建Agent工具"""
        
        @tool
        def get_user_analysis(user_id: str):
            """
            综合分析用户画像和行为历史
            :param user_id: 用户ID
            :return: 用户综合分析结果
            """
            try:
                # 获取用户画像
                profile_data = {'error': '用户画像不存在'}
                try:
                    profile = UserProfile.objects.get(user_id=user_id)
                    profile_data = {
                        'preferred_categories': profile.preferred_categories,
                        'price_preference': profile.price_preference,
                    }
                except UserProfile.DoesNotExist:
                    pass
                
                # 获取行为历史
                behaviors = UserBehavior.objects.filter(user_id=user_id)
                recent_views = UserBehaviorCache.get_user_recent_views(user_id, 10)
                
                # 分析偏好
                category_stats = behaviors.values('product__category').annotate(
                    count=Count('id')
                ).order_by('-count')[:3]
                
                return {
                    'user_id': user_id,
                    'profile': profile_data,
                    'recent_views': recent_views[:3],
                    'favorite_categories': [item['product__category'] for item in category_stats],
                    'total_behaviors': behaviors.count()
                }
            except Exception as e:
                return {'error': f'用户分析失败: {str(e)}'}
        
        @tool
        def get_smart_recommendations(user_id: str, category: str = None, max_price: float = None):
            """
            智能推荐商品（整合多种推荐策略）
            :param user_id: 用户ID
            :param category: 可选分类筛选
            :param max_price: 可选最高价格
            :return: 推荐商品列表
            """
            try:
                recommendations = []
                
                # 1. 获取热门商品
                recent_date = timezone.now() - timedelta(days=7)
                query = UserBehavior.objects.filter(viewed_at__gte=recent_date)
                
                if category:
                    query = query.filter(product__category=category)
                
                trending = query.values('product_id').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]
                
                # 2. 协同过滤推荐
                user_products = set(UserBehavior.objects.filter(user_id=user_id).values_list('product_id', flat=True))
                if user_products:
                    similar_users = UserBehavior.objects.filter(
                        product_id__in=user_products
                    ).exclude(user_id=user_id).values('user_id').annotate(
                        common_count=Count('product_id')
                    ).filter(common_count__gte=1)[:3]
                    
                    similar_user_ids = [item['user_id'] for item in similar_users]
                    collaborative = UserBehavior.objects.filter(
                        user_id__in=similar_user_ids
                    ).exclude(product_id__in=user_products).values('product_id').annotate(
                        score=Count('user_id')
                    ).order_by('-score')[:5]
                else:
                    collaborative = []
                
                # 3. 获取商品详情
                all_product_ids = set()
                for item in trending:
                    all_product_ids.add(item['product_id'])
                for item in collaborative:
                    all_product_ids.add(item['product_id'])
                
                query = Products.objects.filter(id__in=all_product_ids)
                if max_price:
                    query = query.filter(price__lte=max_price)
                
                products = query[:10]
                
                for product in products:
                    recommendations.append({
                        'product_id': product.product_id,
                        'name': product.name,
                        'brand': product.brand,
                        'category': product.category,
                        'price': float(product.price),
                        'is_hot': product.is_hot
                    })
                
                return {
                    'recommendations': recommendations,
                    'total_count': len(recommendations)
                }
                
            except Exception as e:
                return {'error': f'智能推荐失败: {str(e)}'}
        
        @tool
        def get_product_knowledge(product_name: str):
            """
            获取商品知识（简化版）
            :param product_name: 商品名称
            :return: 商品知识信息
            """
            try:
                result = rag_system.ask_question(f"关于{product_name}的特点", return_source=False)
                return {
                    'product_name': product_name,
                    'knowledge': result.get('answer', '暂无相关信息'),
                    'success': result.get('success', False)
                }
            except Exception as e:
                return {'error': f'获取商品知识失败: {str(e)}'}
        
        return [
            get_user_analysis,
            get_smart_recommendations,
            get_product_knowledge
        ]
    
    def _create_prompt(self):
        """创建简化的Agent提示模板"""
        prompt = ChatPromptTemplate.from_messages([
            ('system', '''你是智能商品推荐专家。可用工具：
            - get_user_analysis: 分析用户偏好和行为
            - get_smart_recommendations: 获取智能推荐商品
            - get_product_knowledge: 获取商品详细信息

            推荐策略：
            1. 先分析用户偏好
            2. 获取智能推荐
            3. 补充商品知识
            4. 给出个性化建议

            回答格式简洁明了，包含推荐理由。'''),
            
            ('user', '用户ID: {user_id}, 需求: {requirement}'),
            
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def get_recommendations(self, user_id, requirement="推荐适合的商品"):
        """
        为用户生成个性化推荐（简化版）
        """
        try:
            result = self.agent_executor.invoke({
                "user_id": user_id,
                "requirement": requirement
            })
            
            return {
                'success': True,
                'user_id': user_id,
                'requirement': requirement,
                'recommendation': result["output"],
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            print(f"推荐失败: {str(e)}")
            return {
                'success': False,
                'user_id': user_id,
                'requirement': requirement,
                'error': str(e),
                'recommendation': '抱歉，推荐系统暂时不可用，请稍后重试。',
                'timestamp': timezone.now().isoformat()
            }
    
    def update_user_preference(self, user_id, preferred_categories, price_preference):
        """更新用户偏好"""
        try:
            profile, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'preferred_categories': preferred_categories,
                    'price_preference': price_preference
                }
            )
            
            if not created:
                profile.preferred_categories = preferred_categories
                profile.price_preference = price_preference
                profile.save()
            
            return {'success': True, 'message': '用户偏好更新成功'}
            
        except Exception as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}

# 创建全局推荐Agent实例
recommendation_agent = IntelligentRecommendationAgent()

# 测试函数
def test_recommendation_agent():
    """测试推荐Agent"""
    try:
        print("=== 测试智能推荐Agent ===")
        
        test_user_id = "U0001"
        
        # 测试基础推荐
        print(f"\n为用户 {test_user_id} 生成推荐...")
        result = recommendation_agent.get_recommendations(test_user_id)
        
        print(f"推荐成功: {result['success']}")
        if result['success']:
            print(f"推荐内容: {result['recommendation'][:200]}...")
        else:
            print(f"推荐失败: {result['error']}")
        
        # 测试分类推荐
        print(f"\n测试手机分类推荐...")
        category_result = recommendation_agent.get_recommendations(test_user_id, "推荐手机类商品")
        print(f"分类推荐成功: {category_result['success']}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == '__main__':
    test_recommendation_agent()
