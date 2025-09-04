"""
Elasticsearch连接诊断工具
帮助识别连接问题的具体原因
"""
import requests
import socket
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, AuthenticationException
import json

def check_port_connectivity():
    """检查端口连通性"""
    print("🔍 检查端口连通性...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 9200))
        sock.close()
        
        if result == 0:
            print("✅ 端口9200可访问")
            return True
        else:
            print("❌ 端口9200不可访问")
            return False
    except Exception as e:
        print(f"❌ 端口检查失败: {e}")
        return False

def check_http_access():
    """检查HTTP访问"""
    print("\n🔍 检查HTTP访问...")
    
    # 测试HTTP
    try:
        response = requests.get('http://localhost:9200', timeout=10)
        print(f"✅ HTTP访问成功: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        return True, 'http'
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP访问失败: {e}")
    except Exception as e:
        print(f"❌ HTTP访问异常: {e}")
    
    # 测试HTTPS
    try:
        response = requests.get('https://localhost:9200', verify=False, timeout=10)
        print(f"✅ HTTPS访问成功: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        return True, 'https'
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTPS访问失败: {e}")
    except Exception as e:
        print(f"❌ HTTPS访问异常: {e}")
    
    return False, None

def test_elasticsearch_client():
    """测试ES客户端连接"""
    print("\n🔍 测试Elasticsearch客户端...")
    
    configs = [
        # HTTP无认证
        {
            'name': 'HTTP无认证',
            'config': {'hosts': ['http://localhost:9200'], 'timeout': 10}
        },
        # HTTPS无认证
        {
            'name': 'HTTPS无认证(忽略证书)',
            'config': {'hosts': ['https://localhost:9200'], 'verify_certs': False, 'ssl_show_warn': False, 'timeout': 10}
        },
        # HTTPS with elastic用户
        {
            'name': 'HTTPS with elastic用户',
            'config': {
                'hosts': ['https://localhost:9200'], 
                'basic_auth': ('elastic', 'changeme'),
                'verify_certs': False, 
                'ssl_show_warn': False, 
                'timeout': 10
            }
        }
    ]
    
    for test_case in configs:
        print(f"\n📋 测试: {test_case['name']}")
        try:
            client = Elasticsearch(**test_case['config'])
            if client.ping():
                print("✅ 连接成功!")
                info = client.info()
                print(f"ES版本: {info['version']['number']}")
                return client
            else:
                print("❌ ping失败")
        except AuthenticationException:
            print("❌ 认证失败")
        except ConnectionError as e:
            print(f"❌ 连接错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    return None

def main():
    """主诊断流程"""
    print("🔧 Elasticsearch连接诊断工具")
    print("=" * 50)
    
    # 1. 检查端口
    port_ok = check_port_connectivity()
    
    # 2. 检查HTTP访问
    http_ok, protocol = check_http_access()
    
    # 3. 测试ES客户端
    client = test_elasticsearch_client()
    
    # 4. 总结和建议
    print("\n" + "=" * 50)
    print("📊 诊断结果总结:")
    print(f"端口连通性: {'✅' if port_ok else '❌'}")
    print(f"HTTP/HTTPS访问: {'✅' if http_ok else '❌'}")
    print(f"ES客户端连接: {'✅' if client else '❌'}")
    
    if not port_ok:
        print("\n🚨 建议:")
        print("1. 检查Elasticsearch服务是否正在运行")
        print("2. 在Windows服务管理器中启动Elasticsearch服务")
        print("3. 检查ES日志文件查看启动错误")
    
    elif not http_ok:
        print("\n🚨 建议:")
        print("1. ES服务可能正在启动中，请等待几分钟")
        print("2. 检查ES配置文件中的网络设置")
        print("3. 查看ES日志文件")
    
    elif not client:
        print("\n🚨 建议:")
        print("1. ES可能需要认证，检查安全设置")
        print("2. 修改elasticsearch.yml禁用安全功能")
        print("3. 重启ES服务")

if __name__ == "__main__":
    main()


