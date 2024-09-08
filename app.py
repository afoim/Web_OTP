from flask import Flask, render_template, request, jsonify
import pyotp
import subprocess
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime

app = Flask(__name__)

# 用于存储用户历史查询记录（每个记录存储时间戳和OTP数据）
history_records = []

def parse_otp_uri(uri):
    parsed_uri = urlparse(uri)
    if parsed_uri.scheme != 'otpauth':
        return None

    params = parse_qs(parsed_uri.query)
    path_parts = parsed_uri.path.split(':')

    otp_type = parsed_uri.netloc
    if len(path_parts) > 1:
        issuer = path_parts[0].lstrip('/')
        name = path_parts[1]
    else:
        issuer = params.get('issuer', [None])[0]
        name = path_parts[0].lstrip('/')

    return {
        'type': otp_type,
        'algorithm': params.get('algorithm', ['SHA1'])[0],
        'digits': int(params.get('digits', [6])[0]),
        'issuer': issuer,
        'name': name,
        'period': int(params.get('period', [30])[0]),
        'secret': params.get('secret', [''])[0]
    }

# 路由：渲染主页
@app.route('/')
def index():
    return render_template('index.html')

# 尝试使用 otpauth.exe 或 otpauth
def run_otpauth(command):
    try:
        # 首先尝试运行 otpauth.exe（适用于 Windows）
        result = subprocess.run([command], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()
        else:
            return None
    except FileNotFoundError:
        return None

# 路由：导入谷歌验证器的代码
@app.route('/import_google_auth', methods=['POST'])
def import_google_auth():
    data = request.get_json()
    codes = data.get('uris', [])

    all_otps = []
    for code in codes:
        # 尝试使用 otpauth.exe
        otp_uris = run_otpauth(f'otpauth.exe -link {code}')
        if not otp_uris:
            # 如果 otpauth.exe 失败，尝试使用 otpauth（适用于 Linux）
            otp_uris = run_otpauth(f'otpauth -link {code}')

        if otp_uris:
            for uri in otp_uris:
                otp_data = parse_otp_uri(uri)
                if otp_data:
                    all_otps.append(otp_data)
        else:
            return jsonify({'error': '解析谷歌验证器代码失败'})

    # 将解析结果保存到历史记录中
    if all_otps:
        history_records.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'otps': all_otps
        })

    # 返回解析后的 OTP 数据
    return jsonify(all_otps)

# 路由：从 URI 导入 OTP
@app.route('/import_otp', methods=['POST'])
def import_otp():
    data = request.get_json()
    uris = data.get('uris', [])

    otp_data_list = []
    for uri in uris:
        otp_data = parse_otp_uri(uri)
        if otp_data:
            otp_data_list.append(otp_data)
        else:
            return jsonify({'error': '无效的 OTP URI'})

    # 将导入的 OTP 保存到历史记录中
    if otp_data_list:
        history_records.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'otps': otp_data_list
        })

    return jsonify(otp_data_list)

# 路由：获取TOTP
@app.route('/get_totp', methods=['POST'])
def get_totp():
    data = request.get_json()
    secret = data.get('secret')
    digits = data.get('digits', 6)
    period = data.get('period', 30)

    totp = pyotp.TOTP(secret, digits=digits, interval=period)
    code = totp.now()
    remaining = period - (time.time() % period)

    return jsonify({'code': code, 'remaining': int(remaining)})

# 路由：获取历史记录
@app.route('/get_history', methods=['GET'])
def get_history():
    return jsonify(history_records)

# 路由：删除单个历史记录
@app.route('/delete_history_item', methods=['POST'])
def delete_history_item():
    data = request.get_json()
    index = data.get('index', -1)
    if 0 <= index < len(history_records):
        history_records.pop(index)
    return jsonify({'message': '历史记录已删除'})

# 路由：清除所有历史记录
@app.route('/clear_history', methods=['POST'])
def clear_history():
    global history_records
    history_records = []
    return jsonify({'message': '历史记录已清除'})

if __name__ == '__main__':
    app.run(debug=True)
