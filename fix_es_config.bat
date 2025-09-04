@echo off
echo 🔧 Elasticsearch配置修复工具
echo =====================================

echo.
echo 📍 查找Elasticsearch配置文件...
set CONFIG_FILE=""

REM 检查常见位置
if exist "C:\ProgramData\Elastic\Elasticsearch\config\elasticsearch.yml" (
    set CONFIG_FILE="C:\ProgramData\Elastic\Elasticsearch\config\elasticsearch.yml"
    echo ✅ 找到配置文件: %CONFIG_FILE%
) else if exist "C:\elasticsearch\config\elasticsearch.yml" (
    set CONFIG_FILE="C:\elasticsearch\config\elasticsearch.yml"
    echo ✅ 找到配置文件: %CONFIG_FILE%
) else (
    echo ❌ 未找到elasticsearch.yml配置文件
    echo.
    echo 请手动查找elasticsearch.yml文件位置，通常在以下位置：
    echo - C:\ProgramData\Elastic\Elasticsearch\config\elasticsearch.yml
    echo - [ES安装目录]\config\elasticsearch.yml
    echo.
    pause
    exit /b 1
)

echo.
echo 📋 当前配置文件内容:
echo =====================================
type %CONFIG_FILE%

echo.
echo =====================================
echo.
echo 🚨 需要在配置文件中添加以下设置:
echo.
echo # 禁用安全功能
echo xpack.security.enabled: false
echo xpack.security.enrollment.enabled: false
echo.
echo # 网络设置
echo network.host: 0.0.0.0
echo http.port: 9200
echo discovery.type: single-node
echo.
echo =====================================
echo.
echo ⚠️  请手动编辑配置文件或运行以下命令:
echo.
echo 1. 打开管理员命令提示符
echo 2. 运行: notepad %CONFIG_FILE%
echo 3. 在文件末尾添加上述配置
echo 4. 保存文件
echo 5. 重启ES服务: sc stop "Elasticsearch 8.11.1" ^&^& sc start "Elasticsearch 8.11.1"
echo.
pause


