import redis
import json
import time
from datetime import datetime
from config import REDIS_CONFIG

# Redis连接 - 使用专门的数据库存储RAG对话
redis_client = redis.Redis(
    host=REDIS_CONFIG['host'], 
    port=REDIS_CONFIG['port'], 
    db=REDIS_CONFIG['rag_db'], 
    decode_responses=True
)

class RAGConversationCache:
    """RAG对话缓存管理类"""
    
    # Redis键前缀定义
    USER_CONVERSATIONS_PREFIX = "user_conversations:"  # 用户对话列表键前缀
    CONVERSATION_DETAIL_PREFIX = "conversation_detail:"  # 对话详情键前缀
    POPULAR_QUESTIONS_KEY = "popular_questions"  # 热门问题键
    
    @classmethod
    def save_conversation(cls, user_id, question, answer, sources=None, session_id=None):
        """
        保存RAG对话记录到Redis
        
        Args:
            user_id: 用户ID（可选，支持匿名用户）
            question: 用户问题
            answer: AI回答
            sources: 知识来源列表
            session_id: 会话ID（用于匿名用户）
        
        Returns:
            str: 对话ID，如果保存失败则返回None
        """
        try:
            # 生成对话ID
            conversation_id = f"conv_{int(time.time() * 1000)}"
            current_time = datetime.now()
            timestamp = int(time.time())
            
            # 构建对话数据
            conversation_data = {
                'conversation_id': conversation_id,
                'user_id': user_id or 'anonymous',
                'session_id': session_id or '',
                'question': question,
                'answer': answer,
                'sources': sources or [],
                'timestamp': timestamp,
                'created_at': current_time.isoformat(),
                'question_length': len(question),
                'answer_length': len(answer),
                'source_count': len(sources) if sources else 0
            }
            
            # 保存对话详情
            detail_key = f"{cls.CONVERSATION_DETAIL_PREFIX}{conversation_id}"
            redis_client.setex(
                detail_key,
                REDIS_CONFIG['default_expire'],
                json.dumps(conversation_data,ensure_ascii= False)
            )
            
            # 添加到用户对话列表（使用ZSET按时间排序）
            list_key = f"{cls.USER_CONVERSATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 对话简要信息，用于列表显示
            conversation_summary = {
                'conversation_id': conversation_id,
                'question': question[:100] + "..." if len(question) > 100 else question,
                'timestamp': timestamp,
                'created_at': current_time.isoformat()
            }
            
            # 使用ZADD添加到有序集合，时间戳作为分数
            redis_client.zadd(
                list_key,
                {json.dumps(conversation_summary): timestamp}
            )
            
            # 只保留最近的N条对话
            redis_client.zremrangebyrank(
                list_key, 
                0, 
                -(REDIS_CONFIG['max_conversations'] + 1)
            )
            
            # 设置用户对话列表过期时间
            redis_client.expire(list_key, REDIS_CONFIG['default_expire'])
            
            # 更新热门问题统计
            cls._update_popular_questions(question)
            
            print(f"RAG对话已保存: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            print(f"保存RAG对话失败: {str(e)}")
            return None
    
    @classmethod
    def get_conversation_detail(cls, conversation_id):
        """
        获取对话详情
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            dict: 对话详情数据，如果不存在则返回None
        """
        try:
            detail_key = f"{cls.CONVERSATION_DETAIL_PREFIX}{conversation_id}"
            cached_data = redis_client.get(detail_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"获取对话详情失败: {str(e)}")
            return None
    
    @classmethod
    def get_user_conversations(cls, user_id=None, session_id=None, limit=20):
        """
        获取用户的对话历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（匿名用户）
            limit: 返回数量限制
            
        Returns:
            list: 对话历史列表
        """
        try:
            list_key = f"{cls.USER_CONVERSATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 按时间倒序获取对话列表
            conversations = redis_client.zrevrange(list_key, 0, limit - 1)
            
            conversation_list = []
            for conv_data in conversations:
                try:
                    conv_info = json.loads(conv_data)
                    conversation_list.append(conv_info)
                except json.JSONDecodeError:
                    continue
            
            return conversation_list
            
        except Exception as e:
            print(f"获取用户对话历史失败: {str(e)}")
            return []
    
    @classmethod
    def _update_popular_questions(cls, question):
        """
        更新热门问题统计（私有方法）
        
        Args:
            question: 用户问题
        """
        try:
            # 简化问题（去除标点符号，转为小写）
            simplified_question = question.lower().strip()[:50]
            
            # 使用ZSET存储热门问题，分数为出现次数
            redis_client.zincrby(cls.POPULAR_QUESTIONS_KEY, 1, simplified_question)
            
            # 只保留前100个热门问题
            redis_client.zremrangebyrank(cls.POPULAR_QUESTIONS_KEY, 0, -101)
            
            # 设置过期时间（30天）
            redis_client.expire(cls.POPULAR_QUESTIONS_KEY, 30 * 24 * 3600)
            
        except Exception as e:
            print(f"更新热门问题失败: {str(e)}")
    
    @classmethod
    def get_popular_questions(cls, limit=10):
        """
        获取热门问题列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            list: 热门问题列表，按热度排序
        """
        try:
            # 按分数倒序获取热门问题
            popular_questions = redis_client.zrevrange(
                cls.POPULAR_QUESTIONS_KEY, 
                0, 
                limit - 1,
                withscores=True
            )
            
            questions_list = []
            for question, score in popular_questions:
                questions_list.append({
                    'question': question,
                    'count': int(score)
                })
            
            return questions_list
            
        except Exception as e:
            print(f"获取热门问题失败: {str(e)}")
            return []
    
    @classmethod
    def search_conversations(cls, user_id=None, session_id=None, keyword="", limit=10):
        """
        搜索用户的对话记录
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（匿名用户）
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            list: 匹配的对话记录
        """
        try:
            # 获取用户所有对话
            conversations = cls.get_user_conversations(user_id, session_id, 100)
            
            if not keyword:
                return conversations[:limit]
            
            # 简单的关键词匹配
            matched_conversations = []
            keyword_lower = keyword.lower()
            
            for conv in conversations:
                if (keyword_lower in conv.get('question', '').lower() or 
                    (len(matched_conversations) < limit)):
                    matched_conversations.append(conv)
                
                if len(matched_conversations) >= limit:
                    break
            
            return matched_conversations
            
        except Exception as e:
            print(f"搜索对话记录失败: {str(e)}")
            return []
    
    @classmethod
    def delete_conversation(cls, conversation_id, user_id=None, session_id=None):
        """
        删除指定对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 删除对话详情
            detail_key = f"{cls.CONVERSATION_DETAIL_PREFIX}{conversation_id}"
            redis_client.delete(detail_key)
            
            # 从用户对话列表中移除（需要遍历找到匹配的记录）
            list_key = f"{cls.USER_CONVERSATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            conversations = redis_client.zrange(list_key, 0, -1)
            
            for conv_data in conversations:
                try:
                    conv_info = json.loads(conv_data)
                    if conv_info.get('conversation_id') == conversation_id:
                        redis_client.zrem(list_key, conv_data)
                        break
                except json.JSONDecodeError:
                    continue
            
            print(f"对话已删除: {conversation_id}")
            return True
            
        except Exception as e:
            print(f"删除对话失败: {str(e)}")
            return False
    
    @classmethod
    def clear_user_conversations(cls, user_id=None, session_id=None):
        """
        清空用户所有对话记录
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            bool: 清空是否成功
        """
        try:
            list_key = f"{cls.USER_CONVERSATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 获取所有对话ID并删除详情
            conversations = redis_client.zrange(list_key, 0, -1)
            for conv_data in conversations:
                try:
                    conv_info = json.loads(conv_data)
                    conversation_id = conv_info.get('conversation_id')
                    if conversation_id:
                        detail_key = f"{cls.CONVERSATION_DETAIL_PREFIX}{conversation_id}"
                        redis_client.delete(detail_key)
                except json.JSONDecodeError:
                    continue
            
            # 删除对话列表
            redis_client.delete(list_key)
            
            print(f"用户对话记录已清空: {user_id or session_id or 'anonymous'}")
            return True
            
        except Exception as e:
            print(f"清空用户对话记录失败: {str(e)}")
            return False
    
    @classmethod
    def get_conversation_statistics(cls, user_id=None, session_id=None):
        """
        获取对话统计信息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            dict: 统计信息
        """
        try:
            list_key = f"{cls.USER_CONVERSATIONS_PREFIX}{user_id or session_id or 'anonymous'}"
            
            # 获取对话数量
            total_conversations = redis_client.zcard(list_key)
            
            # 获取最近的对话
            recent_conversations = redis_client.zrevrange(list_key, 0, 9)
            
            # 统计总字数等信息
            total_questions = 0
            total_answers = 0
            
            for conv_data in recent_conversations:
                try:
                    conv_info = json.loads(conv_data)
                    conversation_id = conv_info.get('conversation_id')
                    if conversation_id:
                        detail = cls.get_conversation_detail(conversation_id)
                        if detail:
                            total_questions += detail.get('question_length', 0)
                            total_answers += detail.get('answer_length', 0)
                except json.JSONDecodeError:
                    continue
            
            return {
                'total_conversations': total_conversations,
                'total_question_chars': total_questions,
                'total_answer_chars': total_answers,
                'user_id': user_id or session_id or 'anonymous'
            }
            
        except Exception as e:
            print(f"获取对话统计失败: {str(e)}")
            return {
                'total_conversations': 0,
                'total_question_chars': 0,
                'total_answer_chars': 0,
                'user_id': user_id or session_id or 'anonymous'
            }

# 导出主要的缓存管理类
__all__ = ['RAGConversationCache']

