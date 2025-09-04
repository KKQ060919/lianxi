"""
Django管理命令：将ProductKnowledge数据导入到Elasticsearch
用法: python manage.py import_knowledge_to_es
"""
import os
import sys
import django

# 确保Django设置正确加载
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAY12.settings')

from django.core.management.base import BaseCommand, CommandError
from rag.models import ProductKnowledge
from product.models import Products
from rag.elasticsearch_service import es_service
from config import ELASTICSEARCH_CONFIG
import json

class Command(BaseCommand):
    help = '将ProductKnowledge数据导入到Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新索引，删除现有数据',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批量处理大小（默认100）',
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 开始导入ProductKnowledge数据到Elasticsearch...")
        
        # 检查ES连接
        if not es_service.is_available():
            raise CommandError("❌ Elasticsearch服务不可用，请检查连接配置")
        
        self.stdout.write(self.style.SUCCESS("✅ Elasticsearch连接正常"))
        
        # 获取配置
        knowledge_index = ELASTICSEARCH_CONFIG['indices']['knowledge']
        batch_size = options['batch_size']
        force = options['force']
        
        try:
            # 如果强制重建，先删除索引
            if force:
                self.stdout.write("🗑️ 删除现有索引...")
                if es_service.client.indices.exists(index=knowledge_index):
                    es_service.client.indices.delete(index=knowledge_index)
                    self.stdout.write("✅ 现有索引已删除")
            
            # 确保索引存在
            self.ensure_index_exists(knowledge_index)
            
            # 查询所有ProductKnowledge数据
            knowledge_items = ProductKnowledge.objects.select_related('product').all()
            total_count = knowledge_items.count()
            
            if total_count == 0:
                self.stdout.write(self.style.WARNING("⚠️ 没有找到ProductKnowledge数据"))
                return
            
            self.stdout.write(f"📊 找到 {total_count} 条知识记录，开始导入...")
            
            # 分批处理
            success_count = 0
            error_count = 0
            
            for i in range(0, total_count, batch_size):
                batch_items = knowledge_items[i:i + batch_size]
                batch_docs = []
                
                for item in batch_items:
                    try:
                        # 构建ES文档
                        doc = {
                            'knowledge_id': item.id,
                            'product_id': item.product.product_id,
                            'product_name': item.product.name,
                            'brand': item.product.brand,
                            'category': item.product.category,
                            'attribute': item.attribute,
                            'value': item.value,
                            'source_text': item.source_text or '',
                            'content': f"{item.attribute} {item.value} {item.source_text or ''}",
                            'indexed_at': django.utils.timezone.now().isoformat()
                        }
                        
                        batch_docs.append({
                            '_index': knowledge_index,
                            '_id': f"knowledge_{item.id}",
                            '_source': doc
                        })
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ 处理记录ID {item.id} 失败: {str(e)}")
                        )
                        error_count += 1
                
                # 批量索引到ES
                if batch_docs:
                    try:
                        from elasticsearch.helpers import bulk
                        
                        result = bulk(
                            es_service.client, 
                            batch_docs,
                            refresh=True
                        )
                        
                        batch_success = result[0]  # successful count
                        success_count += batch_success
                        
                        # 显示进度
                        progress = min(i + batch_size, total_count)
                        self.stdout.write(
                            f"✅ 批次完成: {progress}/{total_count} "
                            f"(成功: {batch_success}, 累计成功: {success_count})"
                        )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ 批量索引失败: {str(e)}")
                        )
                        error_count += len(batch_docs)
            
            # 最终统计
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 导入完成！\n"
                    f"   总记录数: {total_count}\n"
                    f"   成功导入: {success_count}\n"
                    f"   失败记录: {error_count}\n"
                    f"   索引名称: {knowledge_index}"
                )
            )
            
            # 验证导入结果
            self.verify_import(knowledge_index, total_count)
            
        except Exception as e:
            raise CommandError(f"❌ 导入过程发生错误: {str(e)}")

    def ensure_index_exists(self, index_name):
        """确保ES索引存在，如果不存在则创建"""
        if not es_service.client.indices.exists(index=index_name):
            # 创建索引映射
            mapping = {
                "mappings": {
                    "properties": {
                        "knowledge_id": {"type": "integer"},
                        "product_id": {"type": "keyword"},
                        "product_name": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "brand": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "attribute": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "value": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "source_text": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "indexed_at": {"type": "date"}
                    }
                }
            }
            
            es_service.client.indices.create(index=index_name, body=mapping)
            self.stdout.write(f"✅ 创建索引: {index_name}")

    def verify_import(self, index_name, expected_count):
        """验证导入结果"""
        try:
            # 刷新索引确保数据可见
            es_service.client.indices.refresh(index=index_name)
            
            # 获取索引中的文档数量
            result = es_service.client.count(index=index_name)
            actual_count = result['count']
            
            self.stdout.write(f"🔍 验证结果: ES中有 {actual_count} 条记录")
            
            if actual_count == expected_count:
                self.stdout.write(self.style.SUCCESS("✅ 数据完整性验证通过"))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ 数据数量不匹配，预期 {expected_count}，实际 {actual_count}"
                    )
                )
            
            # 示例查询测试
            sample_query = {
                "query": {"match_all": {}},
                "size": 3
            }
            
            search_result = es_service.client.search(
                index=index_name, 
                body=sample_query
            )
            
            self.stdout.write(f"\n📋 示例记录 (前3条):")
            for i, hit in enumerate(search_result['hits']['hits'][:3], 1):
                source = hit['_source']
                self.stdout.write(
                    f"  {i}. {source['product_name']} - {source['attribute']}: {source['value']}"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 验证过程出错: {str(e)}")
            )

