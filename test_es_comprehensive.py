"""
全面的Elasticsearch连接测试和修复工具
"""
import requests
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, AuthenticationException
import time
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_https_with_auth():
    """测试HTTPS连接（可能需要认证）"""
    print("🔍 测试HTTPS连接...")
    
    try:
        # 尝试HTTPS无认证
        response = requests.get('https://localhost:9200', 
                              verify=False, 
                              timeout=15)
        print(f"✅ HTTPS访问成功: {response.status_code}")
        data = response.json()
        print(f"ES版本: {data['version']['number']}")
        print(f"集群名称: {data['cluster_name']}")
        return True, data
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTPS连接失败: {e}")
    except Exception as e:
        print(f"❌ HTTPS访问异常: {e}")
    
    return False, None

def test_elasticsearch_clients():
    """测试不同配置的ES客户端"""
    print("\n🔍 测试Elasticsearch客户端连接...")
    
    configs = [
        {
            'name': 'HTTPS无认证',
            'client': Elasticsearch(
                ['https://localhost:9200'],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=15,
                max_retries=2
            )
        },
        {
            'name': 'HTTPS with elastic/changeme',
            'client': Elasticsearch(
                ['https://localhost:9200'],
                basic_auth=('elastic', 'changeme'),
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=15,
                max_retries=2
            )
        },
        {
            'name': 'HTTPS with elastic/elastic',
            'client': Elasticsearch(
                ['https://localhost:9200'],
                basic_auth=('elastic', 'elastic'),
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=15,
                max_retries=2
            )
        }
    ]
    
    for config in configs:
        print(f"\n📋 测试: {config['name']}")
        try:
            client = config['client']
            if client.ping():
                print("✅ 连接成功!")
                info = client.info()
                print(f"ES版本: {info['version']['number']}")
                print(f"集群名称: {info['cluster_name']}")
                return client, config['name']
            else:
                print("❌ ping失败")
        except AuthenticationException as e:
            print("❌ 认证失败")
        except ConnectionError as e:
            print(f"❌ 连接错误: {str(e)[:100]}...")
        except Exception as e:
            print(f"❌ 其他错误: {str(e)[:100]}...")
    
    return None, None

def get_es_password_from_keystore():
    """尝试获取ES的默认密码"""
    print("\n🔍 查找ES默认密码...")
    
    # 常见的密码位置和命令
    password_locations = [
        "C:\\ProgramData\\Elastic\\Elasticsearch\\config\\elasticsearch-keystore",
        "C:\\elasticsearch\\config\\elasticsearch-keystore"
    ]
    
    print("💡 提示：ES 8.x默认启用安全功能，需要密码")
    print("   可以在ES首次启动时的日志中找到自动生成的密码")
    print("   或者运行: elasticsearch-reset-password -u elastic")

def create_fixed_config():
    """创建修复配置的指导"""
    print("\n🛠️  创建ES配置修复指导...")
    
    config_content = """
# 添加到 elasticsearch.yml 文件中的配置
# 通常位于: C:\\ProgramData\\Elastic\\Elasticsearch\\config\\elasticsearch.yml

# 禁用安全功能（开发环境）
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# 网络设置
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# 禁用HTTPS，使用HTTP
xpack.security.http.ssl:
  enabled: false
"""
    
    with open('elasticsearch_config_fix.yml', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ 已创建配置修复文件: elasticsearch_config_fix.yml")
    print("\n📋 修复步骤:")
    print("1. 停止ES服务: Stop-Service -Name 'elasticsearch-service-x64'")
    print("2. 编辑配置文件，添加上述配置")
    print("3. 启动ES服务: Start-Service -Name 'elasticsearch-service-x64'")
    print("4. 等待30秒后重新测试")

def main():
    """主测试流程"""
    print("🔧 Elasticsearch全面连接测试")
    print("=" * 50)
    
    # 1. 测试HTTPS访问
    https_ok, es_info = test_https_with_auth()
    
    # 2. 测试ES客户端
    client, method = test_elasticsearch_clients()
    
    # 3. 结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"HTTPS访问: {'✅' if https_ok else '❌'}")
    print(f"ES客户端连接: {'✅ (' + method + ')' if client else '❌'}")
    
    if client:
        print("\n🎉 ES连接成功！")
        print(f"使用方法: {method}")
        
        # 更新项目配置
        if 'elastic' in method.lower():
            print("\n💡 建议更新config.py中的认证信息")
        else:
            print("\n✅ 当前配置应该可以正常工作")
    
    elif https_ok:
        print("\n🚨 ES运行正常但需要认证")
        get_es_password_from_keystore()
        create_fixed_config()
    
    else:
        print("\n🚨 ES连接完全失败")
        print("建议:")
        print("1. 检查ES服务是否正常启动")
        print("2. 查看ES日志文件")
        print("3. 等待更长时间让ES完全启动")

if __name__ == "__main__":
    main()


