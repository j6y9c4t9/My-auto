import yaml
import urllib.request

# 1. 定义源 URL 和输出文件名
SOURCE_URL = "https://liangxin.xyz/api/v1/liangxin?OwO=4bfe667383e6019a0b004e78bb91d059"
OUTPUT_FILE = "my_subscription.yaml"

def main():
    try:
        print("正在下载源配置文件...")
        # 伪装 User-Agent
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'ClashMetaForAndroid/2.8.9'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')

        # 2. 解析 YAML
        print("正在解析节点信息...")
        source_data = yaml.safe_load(content)

        # 提取 proxies 节点列表（如果不存在则默认为空列表）
        proxies = source_data.get('proxies', [])
        print(f"成功提取到 {len(proxies)} 个节点！")

        # 3. 构建纯节点订阅结构
        my_sub = {
            'proxies': proxies
        }

        # 4. 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(my_sub, f, allow_unicode=True, default_flow_style=False)
        print(f"自己的订阅文件 {OUTPUT_FILE} 已生成成功。")

    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    main()
