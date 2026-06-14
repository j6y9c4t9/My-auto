import yaml
import urllib.request
import os
import sys
from datetime import datetime

# 1. 定义源 URL 和输出文件名
SOURCE_URL = "https://liangxin.xyz/api/v1/liangxin?OwO=4bfe667383e6019a0b004e78bb91d059"
OUTPUT_FILE = "my_subscription.yaml"
TRAFFIC_FILE = "traffic_info.txt"

def parse_traffic(headers):
    """从响应头中解析流量信息（彻底解决大小写与UA带来的不一致问题）"""
    # 转换为全小写字典，消除 HTTP/2 或 CDN 带来的大小写敏感坑
    lowercased_headers = {k.lower(): v for k, v in headers.items()}
    
    info = lowercased_headers.get('subscription-userinfo', '')
    if not info:
        return None

    data = {}
    for item in info.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            data[key.strip()] = int(value.strip())

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
        # 大于 2099 年的时间戳通常是机场定义的永久有效标识
        if expire < 4102444800: 
            expire_str = datetime.fromtimestamp(expire).strftime('%Y-%m-%d')

    percentage = f"{(used / total * 100):.1f}%" if total > 0 else "未知"

    return {
        'used': format_bytes(used),
        'total': format_bytes(total),
        'remaining': format_bytes(remaining),
        'percentage': percentage,
        'expire': expire_str
    }

def main():
    try:
        print("正在下载源配置文件...")
        
        # ⭐【核心修改点】：伪装成浏览器请求，诱导机场后端老老实实返回流量头
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

            # 写入流量信息文件
            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write(f"已用: {traffic['used']} / {traffic['total']} ({traffic['percentage']})\n")
                f.write(f"剩余: {traffic['remaining']}\n")
                f.write(f"到期: {traffic['expire']}\n")
        else:
            # 调试防错：如果还是抓不到，直接把当前机场吐出的所有头打印在控制台/GitHub日志里
            print("⚠️ 未检测到流量信息头。当前机场返回的全部响应头如下：")
            for k, v in resp_headers.items():
                print(f"  {k}: {v}")
                
            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write("暂无流量信息(机场未返回数据)\n")

        # 3. 解析节点
        print("正在解析节点信息...")
        source_data = yaml.safe_load(content)
        proxies = source_data.get('proxies', [])
        print(f"成功提取到 {len(proxies)} 个节点！")

        # 4. 写入自己的订阅文件
        my_sub = {'proxies': proxies}
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(my_sub, f, allow_unicode=True, default_flow_style=False)
        print(f"订阅文件 {OUTPUT_FILE} 已成功生成。")

    except Exception as e:
        print(f"运行出错: {e}")
        with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
            f.write("流量数据获取失败\n")
        sys.exit(1) # 👈 让程序在这里崩溃，以便准确触发 GitHub Actions 的【失败通知】

if __name__ == "__main__":
    main()
