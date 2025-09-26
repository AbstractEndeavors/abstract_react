from abstract_utilities import *
import os
import re
from abstract_utilities.cmd_utils import get_cmd_out
PROJECT_PATH  = '/var/www/html/abstractendeavors/abstract_react'
COMMAND = """#!/bin/bash

echo -e "\n🔧 TypeScript type check starting...\n"

# Run the TypeScript compiler directly first
npx tsc --noEmit 2>&1 | tee tsc.log

# Now run actual build with CI=true
CI=true yarn build 2>&1 | tee build.log
if grep -q "error TS" tsc.log; then
  echo -e "\n❌ TypeScript errors detected:\n"
  grep -A5 -B2 "error TS" tsc.log
  exit 1
fi

echo -e "\n✅ TypeScript check passed. Starting build...\n"


if grep -q "Failed to compile" build.log; then
  echo -e "\n❌ Build failed. Summary:"
  grep -A5 -B2 "Failed to compile" build.log
  exit 1
else
  echo -e "\n✅ Build completed successfully."
  exit 0
fi"""
def remove_parentheses(string,path=None):
    path = path or PROJECT_PATH
    
    lists = [':',')','"',"'",',','(',' ','\n','\t']+list('1234567890')
    string = eatAll(string,lists)
    return os.path.join(path,string)
def run_ssh_cmd(name, command,path=None):
    path = path or PROJECT_PATH
    if path:
        command = "cd {path} && {command}"
    ssh_cmd = f"ssh {name} '{command}'"
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr
def find_file(file_path,lines):
   found_lines = []
   
   breakit = False
   for line in lines['lines']:
      
       string = line.get('string')
       key = int(line.get("key"))
       content = read_from_file(file_path)
       if string in content:
           contents = content.split('\n')
           if len(contents) >= key:
               
               for item in contents:

           
                   if string in item:
                       found_lines.append(file_path)
                       return found_lines

   return found_lines   


def strip_ansi(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)
def run_tsc_log():
    os.system(COMMAND)
def get_file_path(path,build_log={}):

    tsc_log_content = read_from_file(path)
    files = set()
    for line in tsc_log_content.split('\n'):
        if line.startswith('src/'):
            string = line.split(' ')[0]
            
            if os.path.splitext(string)[-1]:
                file_path = remove_parentheses(string)
                files.add(file_path)
           
    return list(files)
def get_build_log_pretty(path):
    build_log_content = read_from_file(path)
    build_log_stripped = strip_ansi(build_log_content)
    lines = {"build_log":build_log_stripped,"lines":[]}
    for line in build_log_stripped.split('\n'):
        line_spl = [li for li in line.split(' ') if li]
        if line_spl and  line_spl[0] == '>' and is_number(line_spl[1]):
            string = eatAll(' '.join(line_spl[2:]),['\n',' ','\t','','|'])
            lines["lines"].append({"key":line_spl[1],"string":string})
    
    return lines

run_ssh_cmd('solcatcher', command = COMMAND,path=PROJECT_PATH)

build_log_path = os.path.join(PROJECT_PATH,'build.log')
tsc_log_path = os.path.join(PROJECT_PATH,'tsc.log')
read_logs = {"tsc_log":tsc_log_path,"build_log":build_log_path}
found_logs = {"tsc_log":None,"build_log":None}
while True:
    for key,value in read_logs.items():
      
        if os.path.exists(value):
            if key == "build_log":
                found_logs[key] = get_build_log_pretty(value)
            if key == 'tsc_log' and found_logs.get("build_log"):
                found_logs[key] = get_file_path(path=value,build_log=found_logs.get("build_log"))
                break
    if None not in list(found_logs.values()):
        break
    

build_log = found_logs["build_log"]
build_log_pretty = build_log["build_log"]
file_paths = found_logs['tsc_log']
input(found_logs)
lines = build_log['lines']
i = 0
for file_path in file_paths:
    
    found_files = find_file(file_path,build_log)
    for found_file in found_files:
       print(build_log_pretty)
       os.system(f"code {found_file}")
       input(found_file)

os.remove(build_log_path)  
os.remove(tsc_log_path)  
