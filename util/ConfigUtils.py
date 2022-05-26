# -*- coding: utf-8 -*-
import os
import json
import yaml
from util.ConfigClass import *

process_resource = {}


class AutomationConfig:
    def __init__(self):
        self.mysql_info = MysqlInfo()
        self.chrome_script = ChromeScript()
        self.job_params = JobParams()
        self.log_params = LogParams()
        self.task_params = TaskParams()


encoding = 'utf-8'


def load_yaml(file_path):
    f = open(file_path, 'r', encoding=encoding)
    y = yaml.load(f)
    return y


def load_resource():
    config = AutomationConfig()
    config = load_process_yaml(config)
    return config


def load_process_yaml(config):
    global process_resource
    process_path = os.path.split(os.path.realpath(__file__))[0] + '/../resource/'
    process_resource = load_yaml(process_path + 'process.yaml')
    config = init_persistence(config)
    config = init_service(config)
    config = init_param(config)
    return config


def init_persistence(config):
    return init_sub_mysql(config)


def init_sub_mysql(config):
    global process_resource
    info = process_resource.get('persistence').get('database').get('mysql')
    config.mysql_info.db_name = info.get('db')
    config.mysql_info.username = info.get('user')
    config.mysql_info.password = info.get('pass')
    config.mysql_info.port = info.get('port')
    config.mysql_info.host = info.get('host')
    return config


def init_service(config):
    return init_sub_chrome_script(config)


def init_sub_chrome_script(config):
    global process_resource
    info = process_resource.get('service').get('chrome_server').get('script')
    config.chrome_script.exe_path = info.get('exe_path')
    config.chrome_script.instance_dir = info.get('instance_dir')
    return config


def init_param(config):
    global process_resource
    process_param = process_resource.get('param')
    config = init_sub_job(config, process_param.get('job'))
    config = init_sub_log(config, process_param.get('utils').get('log'))
    config = init_sub_task(config, process_param.get('task'))
    return config


def init_sub_job(config, info):
    config.job_params.data_refresh_interval = info.get('data_refresh_interval')
    config.job_params.page_load_interval = info.get('page_load_interval')
    config.job_params.operate_interval = info.get('operate_interval')
    config.job_params.job_interval = info.get('job_interval')
    config.job_params.tolerance = info.get('tolerance')
    config.job_params.print_result = info.get('print_result')
    config.job_params.retry_times = info.get('retry_times')
    config.job_params.retry_interval = info.get('retry_interval')
    config.job_params.task_dict = handle_json_config(info.get('task_dict'))
    config.job_params.max_page = info.get('max_page')
    return config


def init_sub_log(config, info):
    config.log_params.method_name_len = info.get('method_name_len')
    config.log_params.debug = info.get('debug')
    config.log_params.show_image_process = info.get('show_image_process')
    config.log_params.save_other_match = info.get('save_other_match')
    return config


def init_sub_task(config, info):
    config.task_params.process_interval = info.get('process_interval')
    config.task_params.run_config = handle_json_config(info.get('run_config'))
    config.task_params.company_group = handle_json_config(info.get('company_group'))
    config.task_params.mode = info.get('mode')
    config.task_params.monitor_interval = info.get('monitor_interval')
    return config


def handle_json_config(info):
    json_files = info.split(",")
    result_dict = {}
    for json_file in json_files:
        file_name = get_actual_json_file(json_file.strip())
        with open(file_name, 'r', encoding=encoding) as file:
            _child_dict = json.load(file)
            result_dict.update(_child_dict)
    return result_dict


def get_actual_json_file(name=""):
    if name is None or len(name) == 0:
        return None
    name = name.strip()
    if not name.endswith(".json"):
        name = name + ".json"
    s_count = name.count("/")
    if s_count == 0 or (s_count > 0 and not name.startswith("/")):
        name = os.path.split(os.path.realpath(__file__))[0] + "/../resource/" + name
    return name


if __name__ == '__main__':
    load_resource()
    print("task finished")
