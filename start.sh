#!/bin/bash

echo "=== INSTALLING DEPENDENCIES ==="
pip install -r requirements.txt
pip install supabase-py==2.3.5 postgrest-py==0.15.0 realtime-py==0.1.3 storage3==0.7.0 gotrue-py==1.2.0 supafunc==0.3.1

echo "=== VERIFYING SUPABASE INSTALLATION ==="
pip list | grep supabase
pip list | grep postgrest
pip list | grep realtime
pip list | grep storage3
pip list | grep gotrue
pip list | grep supafunc

echo "=== STARTING BOT ==="
python main.py 