class MysqlInfo:
    def __int__(self):
        self.db_name = None
        self.username = None
        self.password = None
        self.port = None
        self.host = None


class ChromeScript:
    def __int__(self):
        self.exe_path = None
        self.instance_dir = None


class JobParams:
    def __int__(self):
        self.data_refresh_interval = 1
        self.page_load_interval = 3
        self.operate_interval = 0.7
        self.job_interval = 2
        self.tolerance = 2
        self.print_result = False
        self.retry_times = 3
        self.retry_interval = 10
        self.task_dict = 'all_task'
        self.max_page = 20


class LogParams:
    def __int__(self):
        self.method_name_len = 40
        self.debug = False
        self.show_image_process = False
        self.save_other_match = False


class TaskParams:
    def __int__(self):
        self.process_interval = 2
        self.run_config = 'task_run_config'
        self.company_group = 'company_group'
        self.mode = '123'
        self.monitor_interval = 20
