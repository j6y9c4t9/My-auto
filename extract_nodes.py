import yaml
import urllib.request
import os

# 1. 定义源 URL 和输出文件名
SOURCE_URL = "https://liangxin.xyz/api/v1/liangxin?OwO=4bfe667383e6019a0b004e78bb91d059"
OUTPUT_FILE = "my_subscription.yaml"
TRAFFIC_FILE = "traffic_info.txt"

def parse_traffic(headers):
    """从响应头中解析流量信息"""
    info = headers.get('subscription-userinfo', '')
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

    from datetime import datetime
    expire_str = ""
    if expire > 0:
        expire_str = datetime.fromtimestamp(expire).strftime('%Y-%m-%d')

    percentage = f"{(used / total * 100):.1f}%" if total > 0 else "未知"

    return {
        'used': format_bytes(used),
        'total': format_bytes(total),
        'remaining': format_bytes(remaining),
        'percentage': percentage,
        'expire': expire_str,
        'raw_remaining': remaining
    }

def main():
    try:
        print("正在下载源配置文件...")
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'ClashMetaForAndroid/2.8.9'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            headers = dict(response.headers)

        # 解析流量信息
        traffic = parse_traffic(headers)
        if traffic:
            print(f"📊 已用: {traffic['used']} / {traffic['total']} ({traffic['percentage']})")
            print(f"📊 剩余: {traffic['remaining']}")
            if traffic['expire']:
                print(f"📅 到期: {traffic['expire']}")

            # 写入流量信息文件，供 GitHub Actions 读取
            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write(f"已用: {traffic['used']} / {traffic['total']} ({traffic['percentage']})\n")
                f.write(f"剩余: {traffic['remaining']}\n")
                if traffic['expire']:
                    f.write(f"到期: {traffic['expire']}\n")
        else:
            print("⚠️ 未检测到流量信息头")
            with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
                f.write("无法获取流量信息\n")

        # 解析节点
        print("正在解析节点信息...")
        source_data = yaml.safe_load(content)
        proxies = source_data.get('proxies', [])
        print(f"成功提取到 {len(proxies)} 个节点！")

        # 写入订阅文件
        my_sub = {'proxies': proxies}
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(my_sub, f, allow_unicode=True, default_flow_style=False)
        print(f"自己的订阅文件 {OUTPUT_FILE} 已生成成功。")

    except Exception as e:
        print(f"运行出错: {e}")
        # 即使失败也写入文件，避免 Actions 读取报错
        with open(TRAFFIC_FILE, 'w', encoding='utf-8') as f:
            f.write("获取失败\n")

if __name__ == "__main__":
    main()
