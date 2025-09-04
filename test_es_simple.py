"""
简单的Elasticsearch连接测试
"""
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, AuthenticationException
from config import ELASTICSEARCH_CONFIG
import requests
import warnings
warnings.filterwarnings("ignore")

def test_basic_connection():
    """测试基本连接"""
    print("🔍 测试Elasticsearch连接...")
    
    config = ELASTICSEARCH_CONFIG
    
    # 先测试HTTPS访问
    try:
        response = requests.get('https://localhost:9200', verify=False, timeout=10)
        print(f"✅ HTTPS访问成功: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS访问失败: {e}")
        return False
    
    # 测试ES客户端连接（使用认证）
    try:
        client = Elasticsearch(
            f"https://{config['host']}:{config['port']}",
            basic_auth=(config['username'], config['password']),
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30
        )
        
        if client.ping():
            print("✅ Elasticsearch连接成功！")
            info = client.info()
            print(f"ES版本: {info['version']['number']}")
            print(f"集群名称: {info['cluster_name']}")
            return True
        else:
            print("❌ ES ping失败")
            return False
            
    except AuthenticationException:
        print("❌ 认证失败 - 请检查用户名和密码")
        return False
    except ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_connection()
    if success:
        print("\n🎉 ES连接测试成功！可以开始使用RAG功能了。")
    else:
        print("\n❌ ES连接测试失败，请检查配置。")

