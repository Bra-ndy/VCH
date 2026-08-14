# gunicorn.conf.py 
import os 
import multiprocessing 
 
port = os.environ.get('PORT', '10000') 
bind = f"0.0.0.0:{port}" 
 
workers = multiprocessing.cpu_count() * 2 + 1 
worker_class = 'sync' 
threads = 2 
 
timeout = 120 
graceful_timeout = 30 
 
max_requests = 1000 
max_requests_jitter = 100 
 
accesslog = '-' 
errorlog = '-' 
loglevel = os.environ.get('LOG_LEVEL', 'info') 
 
preload_app = True 
worker_tmp_dir = '/dev/shm' 
forwarded_allow_ips = '*' 
