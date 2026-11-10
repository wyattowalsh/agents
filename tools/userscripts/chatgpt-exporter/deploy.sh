#!/usr/bin/env bash
set -euo pipefail
rm -rf p t
mkdir -p p t
cat source/payload.part* | base64 --decode | tar -xJf - -C t
cp -R t/tools/userscripts/chatgpt-exporter/. p
FROM='raw.githubusercontent.com/wyattowalsh/agents/main/tools/userscripts/chatgpt-exporter'
TO='chatgpt-export-local.vercel.app'
sed -i "s#${FROM}#${TO}#g" p/*.js p/schemas/*.json
