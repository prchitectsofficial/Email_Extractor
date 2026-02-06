#!/usr/bin/env bash
cd /var/www/email-extractor
exec /var/www/email-extractor/.venv/bin/python3 -m streamlit run app.py \
  --server.address 127.0.0.1 \
  --server.port 9003 \
  --server.baseUrlPath /email-extractor \
  --browser.serverAddress apps.accunite.com \
  --browser.gatherUsageStats false
