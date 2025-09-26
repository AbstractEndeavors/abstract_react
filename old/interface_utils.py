from .replace_utils import *
from abstract_webserver import *
def extract_values(content,split_string,splitbacks,split_nums=None):
    split_nums = split_nums or [0]
    splitbacks = make_list(splitbacks)
    values = []
    strings = content.split(split_string)
    for string in strings[1:]:
        
        for i,splitback in enumerate(splitbacks):
            split_num = split_nums[-1]
            if len(split_nums)>i:
                split_num = split_nums[i]
            string = string.split(splitback)[split_num]
        values.append(string)
    return values
def replace_it(string,replace_var,replace_var2):
    while True:
        if replace_var in string:
            string = string.replace(replace_var,replace_var2)
        else:
            return string
    
def infinate_replace(string,replace_vars):
    for replace_var in replace_vars:
        string = replace_it(string,*replace_var)
    return string
def extract_variables_from_interfaces(file_path):
    datas = read_from_file(file_path)
    interfaces = []
    variables = []
    for data in datas.split('interface ')[1:]:
        interface = eatAll(data,' ').split('{')[0].split(' ')[0]
        interfaces.append(interface)
    for data in datas.split('{')[1:]:
        data = data.split('}')[0]
        for line in data.split(';'):
            variable = line.split(':')[0].split('?')[0]
            variable = eatAll(variable,[' ','\n'])
            if variable:
                variables.append(variable)
    return interfaces,variables
ALPHAS = list('abcdefghijlmnopqrstuvwxyz')+list('abcdefghijlmnopqrstuvwxyz'.upper())
def get_only_alphas(string):
    return ''.join([char for char in string if char in ALPHAS])
def get_lowered_alphad(*strings):
    strings = [get_only_alphas(string).lower() for string in strings]
    return strings
def compare_strings(*strings):
    for i,string in enumerate(strings):
        string = get_only_alphas(string).lower()
        if i == 0:
            comp_string = string
        else:
            if comp_string != string:
                return False
            comp_string = string
    return True
def compare_comp_strings(string,variables):
    if string in variables:
        return string
    for variable in variables:
        if compare_strings(string,variable):
            return variable
def convert_variables(strings,file_path,to_dict=False):
    strings_js = {}
    interfaces,interface_variables = extract_variables_from_interfaces(file_path)
    for i,string in enumerate(strings):
        strings_js[string]=string
        comp_string = compare_comp_strings(string,interface_variables)
        if comp_string:
            strings_js[string]=comp_string
            strings[i] = comp_string
    if to_dict:
        return strings_js
    return strings
def get_main_dir_from_file_path(file_path):
    if 'src/' in file_path:
        main_dir = file_path.split('src/')[0]
    return main_dir
def get_src_dir_from_file_path(file_path):
    main_dir = get_main_dir_from_file_path(file_path)
    src_dir = join_paths(main_dir,'src')
    return src_dir
def make_temp_dir(file_path):
    main_dir = get_main_dir_from_file_path(file_path)
    tmp_dir = join_paths(main_dir,'tmp')
    os.makedirs(tmp_dir,exist_ok=True)
    new_backup_dir = get_new_backup_dir(backup_dir=tmp_dir)
    os.makedirs(new_backup_dir,exist_ok=True)
    return new_backup_dir
def convert_variables_files(strings,interface_file,react_file):
    if isinstance(strings,str):
        strings = [eatAll(string,[',',' ','\n','\t']) for string in strings]
    variables = convert_variables(strings,interface_file,True)
    react_data = read_from_file(react_file)
    for key,value in variables.items():
        react_data = react_data.replace(key,value)
    temp_dir = make_temp_dir(react_file)
    src_dir = get_src_dir_from_file_path(react_file)
    react_basename = os.path.basename(react_file)
    replacement_file_path = join_paths(temp_dir,react_basename)
    write_to_file(data=react_data,file_path=replacement_file_path)
    
    write_to_file(contents=react_data,file_path=replacement_file_path)
    replace_react_files(src_dir=src_dir,
                        paths=[replacement_file_path])
    
