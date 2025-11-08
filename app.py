from flask import Flask, render_template, request, jsonify
import time
import random
import requests

app = Flask(__name__)

print("✅ Flask app starting...")

# Simple in-memory storage
attack_status = {
    'is_running': False,
    'requests_sent': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'current_method': '',
    'start_time': None,
    'test_logs': []
}

proxies_list = []

print("✅ Global variables initialized...")

class SimpleNetworkTester:
    def __init__(self):
        self.is_testing = False
        print("✅ NetworkTester initialized...")
        
    def log_message(self, message):
        """Add message to test logs"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            attack_status['test_logs'].append(log_entry)
            # Keep only last 20 log entries
            attack_status['test_logs'] = attack_status['test_logs'][-20:]
        except Exception as e:
            print(f"Logging error: {e}")

    def simple_http_flood(self, target, ports, duration, threads_count, max_requests, use_proxies):
        """Simple HTTP Flood attack"""
        print(f"✅ Starting HTTP flood: {target}, {ports}")
        
        end_time = time.time() + min(duration, 10)  # Max 10 seconds for serverless
        request_count = 0
        start_time = time.time()
        
        self.log_message(f"🚀 STARTING STRESS TEST: HTTP_FLOOD")
        self.log_message(f"🎯 Target: {target}")
        self.log_message(f"🔢 Ports: {ports}")
        self.log_message(f"⏱️ Duration: {duration}s")
        self.log_message("=" * 50)
        
        try:
            # Simple sequential requests (no threading for serverless stability)
            while (time.time() < end_time and self.is_testing and 
                   (max_requests == 0 or request_count < max_requests)):
                try:
                    port = random.choice(ports)
                    
                    # Simple HTTP request
                    response = requests.get(
                        f"http://{target}:{port}/", 
                        timeout=2,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    
                    if response.status_code == 200:
                        attack_status['successful_requests'] += 1
                    else:
                        attack_status['failed_requests'] += 1
                    
                    request_count += 1
                    attack_status['requests_sent'] += 1
                    
                    # Log progress
                    if request_count % 10 == 0:
                        self.log_message(f"📨 Requests sent: {request_count}")
                    
                except Exception as e:
                    attack_status['failed_requests'] += 1
                    request_count += 1
                    attack_status['requests_sent'] += 1
            
            # Log results
            end_time_actual = time.time()
            elapsed = end_time_actual - start_time
            rps = request_count / elapsed if elapsed > 0 else 0
            
            self.log_message("=" * 50)
            self.log_message("📊 HTTP FLOOD COMPLETED:")
            self.log_message(f"   ✅ Total Requests: {request_count}")
            self.log_message(f"   ⏱️ Duration: {elapsed:.2f}s")
            self.log_message(f"   🚀 Average RPS: {rps:.2f}")
            
            if rps > 50:
                self.log_message("   🔥 GOOD PERFORMANCE")
            else:
                self.log_message("   🔧 LIGHT LOAD")
                
        except Exception as e:
            self.log_message(f"❌ Attack error: {str(e)}")

# Initialize tester
tester = SimpleNetworkTester()

print("✅ Tester object created...")

@app.route('/')
def index():
    """Main page"""
    print("✅ Serving index page...")
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
            'active_count': len(proxies_list),
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
                            imported += 1
            except:
                continue
        
        return jsonify({
            'status': 'success', 
            'message': f'Imported {imported} proxies'
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
        
        # Safety limits for serverless
        duration = min(duration, 10)  # Max 10 seconds
        max_requests = min(max_requests, 100)  # Max 100 requests
        
        # Reset status
        attack_status.update({
            'is_running': True,
            'requests_sent': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'current_method': method,
            'start_time': time.time(),
            'test_logs': []
        })
        
        # Start attack
        def run_attack():
            tester.is_testing = True
            try:
                if method == 'http_flood':
                    tester.simple_http_flood(target, ports, duration, threads, max_requests, use_proxies)
                elif method == 'udp_flood':
                    # Simple UDP simulation
                    tester.log_message("📦 UDP Flood: Basic simulation mode")
                    time.sleep(2)
                    attack_status['requests_sent'] = 50
                    attack_status['successful_requests'] = 45
                    attack_status['failed_requests'] = 5
                    tester.log_message("📊 UDP SIMULATION: 50 packets sent")
            except Exception as e:
                tester.log_message(f"❌ Attack error: {str(e)}")
            finally:
                tester.is_testing = False
                attack_status['is_running'] = False
        
        # Run in main thread for simplicity
        run_attack()
        
        return jsonify({'status': 'Attack completed'})
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

print("✅ All routes defined...")

# Vercel serverless handler
def handler(request):
    return app(request)

if __name__ == '__main__':
    print("✅ Starting Flask server...")
    app.run(debug=True)
