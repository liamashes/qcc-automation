from util.ConfigUtils import load_resource, AutomationConfig

config: AutomationConfig = load_resource()

mysql_info = config.mysql_info
chrome_script = config.chrome_script
job_params = config.job_params
log_params = config.log_params
task_params = config.task_params