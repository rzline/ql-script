import requests
import os
import time
import xml.etree.ElementTree as ET

def get_cookies(cookie_value):
    return {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie_value.split('; ')}

def create_headers(referer=None):
    cookie_value = os.getenv('SOUTHPLUSCOOKIE')
    if cookie_value:
        cookie_value = cookie_value.replace('\n', '').strip()
    cookies = get_cookies(cookie_value) if cookie_value else {}
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    }
    if referer:
        headers['referer'] = referer
    if cookies:
        headers['cookie'] = '; '.join([f'{key}={value}' for key, value in cookies.items()])
    return headers

def log_to_telegram(message):
    bot_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if bot_token and chat_id:
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"发送日志失败: {response.text}")

def create_params(action, cid):
    """创建请求参数"""
    try:
        response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC')
        response.raise_for_status()  # 检查请求是否成功
        nowtime = str(int(response.json()['unixtime'] * 1000))
    except requests.RequestException as e:
        error_message = f"获取当前时间失败: {e}"
        print(error_message)
        log_to_telegram(error_message)
        nowtime = str(int(time.time() * 1000))  # 使用本地时间作为备选

    return {
        'H_name': 'tasks',
        'action': 'ajax',
        'nowtime': nowtime,
        'verify': '5af36471',
        'actions': action,
        'cid': cid,
    }

def parse_response(data):
    root = ET.fromstring(data)
    cdata = root.text
    return cdata.split('\t')

def send_message_to_telegram(message):
    bot_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if bot_token and chat_id:
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"发送消息失败: {response.text}")

def tasks(url, action, cid, task_type):
    headers = create_headers(url + f'?H_name-tasks-actions-{action}.html.html')
    params = create_params(action, cid)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        values = parse_response(response.text)
        expected_length = 2 if '申请' in task_type else 3
        
        if len(values) == expected_length:
            message = values[1]
            log_message = f"{task_type} {message}"
            print(log_message)
            send_message_to_telegram(log_message)
            return "还没超过" not in message
        else:
            raise ValueError("XML格式不正确，请检查COOKIE设置")
    except ET.ParseError:
        log_message = f"解析XML失败: {response.text}"
        print(log_message)
        log_to_telegram(log_message)
        raise ValueError("解析XML时出错，请检查返回的数据格式")
    except requests.RequestException as e:
        log_message = f"请求失败: {e}"
        print(log_message)
        log_to_telegram(log_message)

if __name__ == "__main__":
    url = 'https://snow-plus.net/plugin.php'
    
    if tasks(url, 'job', '15', "申请-日常: "):
        tasks(url, 'job2', '15', "完成-日常: ")
    
    if tasks(url, 'job', '14', "申请-周常: "):
        tasks(url, 'job2', '14', "完成-周常: ")
