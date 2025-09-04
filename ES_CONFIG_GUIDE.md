# Elasticsearch 配置指南

## 问题状态
✅ **已完成**：更新了项目中的 `config.py`，设置为HTTP模式  
🔄 **进行中**：需要修改ES配置文件禁用安全功能  
⏳ **待完成**：重启ES服务并测试连接  

## 当前问题
Elasticsearch 8.x默认启用了安全功能，需要认证。您的浏览器可以访问 `https://localhost:9200`，但Python客户端连接失败。

## 解决步骤

### 步骤1：找到ES配置文件
Elasticsearch配置文件 `elasticsearch.yml` 通常位于：
- **Windows**: `C:\ProgramData\Elastic\Elasticsearch\config\elasticsearch.yml`
- **或者**: `[ES安装目录]\config\elasticsearch.yml`

### 步骤2：编辑配置文件
在 `elasticsearch.yml` 文件中添加或修改以下设置：

```yaml
# 禁用安全功能
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# 网络设置
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# 可选：禁用HTTPS，使用HTTP
xpack.security.http.ssl:
  enabled: false
```

### 步骤3：重启ES服务
1. 打开Windows服务管理器（`services.msc`）
2. 找到 "Elasticsearch 8.11.1" 服务
3. 右键点击 → 重新启动

### 步骤4：测试连接
配置完成后，运行测试脚本：
```bash
python test_es_simple.py
```

## 预期结果
- ES将在 `http://localhost:9200` 运行（注意是HTTP，不是HTTPS）
- 无需认证即可连接
- Python客户端能够正常连接

## 验证成功的标志
1. `python test_es_simple.py` 显示 "✅ Elasticsearch连接成功！"
2. 可以通过浏览器访问 `http://localhost:9200`（HTTP）
3. 项目的RAG功能可以正常使用ES存储

## 如果仍有问题
1. 检查ES服务是否正常启动
2. 查看ES日志文件排查启动问题
3. 确认配置文件格式正确（YAML格式对缩进敏感）

## 备注
这个配置适合开发环境。生产环境建议保持安全功能启用并配置适当的认证。


