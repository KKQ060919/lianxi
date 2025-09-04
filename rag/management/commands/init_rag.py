from django.core.management.base import BaseCommand
from rag.RAG封装 import rag_system
import os
import shutil

class Command(BaseCommand):
    help = '初始化或重新初始化RAG系统向量数据库'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新初始化，删除现有数据',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清空Chroma数据库目录',
        )
    
    def handle(self, *args, **options):
        """执行RAG系统初始化"""
        
        force = options['force']
        clear = options['clear']
        
        self.stdout.write(self.style.SUCCESS('开始RAG系统初始化...'))
        
        # 如果需要清空数据库目录
        if clear:
            chroma_dir = "./chroma_product_knowledge"
            if os.path.exists(chroma_dir):
                try:
                    shutil.rmtree(chroma_dir)
                    self.stdout.write(
                        self.style.WARNING(f'已删除Chroma数据库目录: {chroma_dir}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'删除Chroma目录失败: {str(e)}')
                    )
                    return
        
        try:
            # 重置初始化状态
            rag_system.is_initialized = False
            
            # 执行初始化
            success = rag_system.initialize_vector_store(force_reload=force or clear)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('RAG系统初始化成功！')
                )
                
                # 测试系统是否正常工作
                test_question = "测试问题"
                result = rag_system.ask_question(test_question)
                
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS('RAG系统测试通过！')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'RAG系统测试失败: {result["answer"]}')
                    )
                    
            else:
                self.stdout.write(
                    self.style.ERROR('RAG系统初始化失败！')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'初始化过程中出现错误: {str(e)}')
            )

