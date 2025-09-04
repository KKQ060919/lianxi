"""
等待ES启动并测试连接
"""
import time
import requests
import urllib3
from elasticsearch import Elasticsearch

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def wait_for_es(max_wait=120):
    """等待ES启动"""
    print("⏳ 等待Elasticsearch启动...")
    
    for i in range(max_wait):
        try:
            # 尝试简单的HTTP请求
            response = requests.get('https://localhost:9200', 
                                  verify=False, 
                                  timeout=5)
            if response.status_code in [200, 401]:
                print(f"✅ ES响应正常 (状态码: {response.status_code})")
                return True
        except:
            pass
        
        print(f"等待中... {i+1}/{max_wait}秒", end='\r')
        time.sleep(1)
    
    print("\n❌ ES启动超时")
    return False

def test_with_common_passwords():
    """使用常见密码测试"""
    passwords = ['changeme', 'elastic', 'password', '123456']
    
    for pwd in passwords:
        print(f"🔐 尝试密码: elastic/{pwd}")
        try:
            client = Elasticsearch(
                ['https://localhost:9200'],
                basic_auth=('elastic', pwd),
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=10
            )
            
            if client.ping():
                print(f"✅ 连接成功！用户名: elastic, 密码: {pwd}")
                return client, pwd
        except Exception as e:
            print(f"❌ 失败: {str(e)[:50]}...")
    
    return None, None

if __name__ == "__main__":
    # 等待ES启动
    if wait_for_es():
        # 测试连接
        client, password = test_with_common_passwords()
        
        if client:
            print(f"\n🎉 ES连接成功！")
            print(f"连接信息: elastic/{password}")
            
            # 获取ES信息
            info = client.info()
            print(f"ES版本: {info['version']['number']}")
            print(f"集群名称: {info['cluster_name']}")
        else:
            print("\n❌ 所有密码都失败了")
            print("建议修改ES配置禁用安全功能")
    else:
        print("ES启动失败，请检查服务和日志")


