from flask import Flask, render_template, request, jsonify
import pyotp
import subprocess
import time
import os
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
        'digits': int(params.get('digits', ['6'])[0]),
        'issuer': issuer,
        'name': name,
        'period': int(params.get('period', ['30'])[0]),
        'secret': params.get('secret', [''])[0]
    }

def run_otpauth(code):
    # 根据操作系统选择适当的命令
    if os.name == 'nt':  # Windows
        command = f'otpauth.exe -link "{code}"'
    else:  # Linux / macOS
        command = f'./otpauth -link "{code}"'
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()
    except FileNotFoundError:
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import_google_auth', methods=['POST'])
def import_google_auth():
    data = request.get_json()
    codes = data.get('uris', [])

    all_otps = []
    for code in codes:
        otp_uris = run_otpauth(code)
        if otp_uris:
            for uri in otp_uris:
                otp_data = parse_otp_uri(uri)
                if otp_data:
                    all_otps.append(otp_data)

    # 添加到历史记录，附加当前时间戳
    timestamp = datetime.now().strftime('%Y/%m/%d %H:%M')
    history_records.append({
        'timestamp': timestamp,
        'otps': all_otps
    })

    return jsonify(all_otps)

@app.route('/import_otp', methods=['POST'])
def import_otp():
    data = request.get_json()
    uris = data.get('uris')
    if not uris or not isinstance(uris, list):
        return jsonify({'error': 'No OTP URIs provided'}), 400

    otp_data_list = []
    for uri in uris:
        otp_data = parse_otp_uri(uri)
        if not otp_data:
            return jsonify({'error': f'Invalid OTP URI: {uri}'}), 400
        otp_data_list.append(otp_data)

    # 添加到历史记录，附加当前时间戳
    timestamp = datetime.now().strftime('%Y/%m/%d %H:%M')
    history_records.append({
        'timestamp': timestamp,
        'otps': otp_data_list
    })

    return jsonify(otp_data_list)

@app.route('/get_totp', methods=['POST'])
def get_totp():
    data = request.get_json()
    secret = data.get('secret')
    digits = data.get('digits', 6)
    period = data.get('period', 30)
    if not secret:
        return jsonify({'error': 'No secret provided'}), 400

    totp = pyotp.TOTP(secret, digits=digits, interval=period)
    return jsonify({
        'code': totp.now(),
        'remaining': period - (int(time.time()) % period)
    })

@app.route('/get_history', methods=['GET'])
def get_history():
    return jsonify(history_records)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    history_records.clear()
    return jsonify({'message': 'History cleared successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
