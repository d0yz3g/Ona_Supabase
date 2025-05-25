#!/bin/bash

echo "Installing Supabase dependencies..."
pip install supabase-py==2.3.5 postgrest-py==0.15.0 realtime-py==0.1.3 storage3==0.7.0 gotrue-py==1.2.0 supafunc==0.3.1

echo "Verifying installation..."
pip list | grep supabase
pip list | grep postgrest
pip list | grep realtime
pip list | grep storage3
pip list | grep gotrue
pip list | grep supafunc

echo "Supabase dependencies installation completed." 