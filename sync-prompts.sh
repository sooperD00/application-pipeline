#!/bin/bash
# sync-prompts.sh
rm -rf ../application-pipeline-prompts/*
cp -r prompts/. ../application-pipeline-prompts/
cd ../application-pipeline-prompts && git add -A && git commit -m "prompt update $(date +%Y-%m-%d)" && git push
ls -l -a
cd ../application-pipeline