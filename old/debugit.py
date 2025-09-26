from abstract_utilities import *
import os
import re
from abstract_utilities.cmd_utils import get_cmd_out
COMMAND = """#!/bin/bash

echo -e "\n🔧 TypeScript type check starting...\n"

# Run the TypeScript compiler directly first
npx tsc --noEmit 2>&1 | tee tsc.log

if grep -q "error TS" tsc.log; then
  echo -e "\n❌ TypeScript errors detected:\n"
  grep -A5 -B2 "error TS" tsc.log
  exit 1
fi

echo -e "\n✅ TypeScript check passed. Starting build...\n"

# Now run actual build with CI=true
CI=true yarn build 2>&1 | tee build.log

if grep -q "Failed to compile" build.log; then
  echo -e "\n❌ Build failed. Summary:"
  grep -A5 -B2 "Failed to compile" build.log
  exit 1
else
  echo -e "\n✅ Build completed successfully."
  exit 0
fi"""

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)
def run_tsc_log():
    os.system(COMMAND)
get_cmd_out(COMMAND)
build_log_path = os.path.join(os.getcwd(),'build.log')
build_log_content = read_from_file(build_log_path)
input(strip_ansi(build_log_content))
tsc_log_path = os.path.join(os.getcwd(),'tsc.log')
strip_ansi(build_log_contents)
