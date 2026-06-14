import yaml
import urllib.request
import os
import sys
from datetime import datetime

# 1. 动态从 GitHub Secrets / 环境变量中读取订阅地址
# 如果本地测试，可以在系统环境变量中添加 SUB_URL，或者在此处填入备用地址
SOURCE_URL = os.environ.get("SUB_URL", "").strip()

OUTPUT_FILE = "my_subscription.yaml"
TRAFFIC_FILE = "traffic_info.txt"

def safe_int(value_str):
    """安全地将字符串转换为整数，如果为空或非法则返回 0"""
    clean_val = value_str.strip()
    if not clean_val or not clean_val.isdigit():
        return 0
    return int(clean_val)

def parse_traffic(headers):
    """从响应头中解析流量信息"""
    lowercased_headers = {k.lower(): v for k, v in headers.items()}
    
    info = lowercased_headers.get('subscription-userinfo', '')
    if not info:
        return None

    data = {}
    for item in info.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            data[key.strip()] = safe_int(value)

    upload = data.get('upload', 0)
    download = data.get('download', 0)
    total = data.get('total', 0)
    expire = data.get('expire', 0)

    used = upload + download
    remaining = total - used if total > used else 0

    def format_bytes(b):
        if b >= 1073741824:
            return f"{b / 1073741824:.2f} GB"
        elif b >= 1048576:
            return f"{b / 1048576:.2f} MB"
        else:
            return f"{b / 1024:.2f} KB"

    expire_str = "永久有效"
    if expire > 0:
        if expire < 4102444800: 
            try:
                expire_str = datetime.fromtimestamp(expire).strftime('%Y-%m-%d')
            except Exception:
                expire_str = "自定义时间格式"

    percentage = f"{(used / total * 100):.1f}%" if total > 0 else "未知"

    return {
        'used': format_bytes(used),
        'total': format_bytes(total),
        'remaining': format_bytes(remaining),
        'percentage': percentage,
        'expire': expire_str
    }

def main():
    global SOURCE_URL
    
    # ⭐【关键防护】：检查是否成功读取到了 Secret
    if not SOURCE_URL:
        print("❌ 错误：未能从环境变量中读取到 'SUB_URL'。请检查 GitHub Secrets 是否配置正确！")
        sys.exit(1)
        
    # ⭐【动态拼接】：自动在 Secret 链接后面附加上 Mihomo 专属的 Meta 标记
    if "flag=" not in SOURCE_URL:
        connector = "&" if "?" in SOURCE_URL else "?"
        SOURCE_URL = f"{SOURCE_URL}{connector}flag=meta"

    try:
        print("正在下载源配置文件...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        req = urllib.request.Request(SOURCE_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            resp_headers = dict(response.headers)

        # 2. 解析流量信息
        traffic = parse_traffic(resp_headers)
        if traffic:
            print(f"📊 已用: {traffic['used']} / {traffic['total']} ({traffic['percentage']})")
            print(f"📊 剩余: {traffic['remaining']}")
            print(f"📅 到期: {traffic['expire']}")

            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write(f"已用: {traffic['used']} / {traffic['total']} ({traffic['percentage']})\n")
                f.write(f"剩余: {traffic['remaining']}\n")
                f.write(f"到期: {traffic['expire']}\n")
        else:
            print("⚠️ 未检测到流量信息头。当前机场返回的全部响应头如下：")
            for k, v in resp_headers.items():
                print(f"  {k}: {v}")
                
            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write("暂无流量信息(机场未返回数据)\n")

        # 3. 解析节点
        print("正在解析节点信息...")
        source_data = yaml.safe_load(content)
        
        if not isinstance(source_data, dict):
            print("\n❌ 严重错误：机场返回的内容不是合法的 YAML 配置文件！")
            raise ValueError("机场订阅接口被防火墙拦截，未能正确获取到 YAML 节点数据。")

        proxies = source_data.get('proxies', [])
        print(f"成功提取到 {len(proxies)} 个节点！")

        # 4. 写入自己的订阅文件
        my_sub = {'proxies': proxies}
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(my_sub, f, allow_unicode=True, default_flow_style=False)
        print(f"订阅文件 {OUTPUT_FILE} 已成功生成。")

    except Exception as e:
        print(f"\n运行出错: {e}")
        with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
            f.write("流量数据获取失败\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
