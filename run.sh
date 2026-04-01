#!/bin/bash
cd /home/ilyaas/workspace/github.com/IlyaasK/plcscheduler
source .venv/bin/activate
python3 main.py >> scheduler.log 2>&1
