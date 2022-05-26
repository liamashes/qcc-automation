import argparse
import math
import multiprocessing
import platform
import threading
import time
from multiprocessing import Process

from deprecated.sphinx import deprecated

from qcc.Module import qccProcess, startChrome, qccFrequentVisit, shutdownChrome, qccStartBrowser
from util import Persistence
from util.CommonUtils import printInfo, printWarn
import util.Config as config

process_interval = config.task_params.process_interval
run_config = config.task_params.run_config
process_infos = list(run_config.values())
company_group = config.task_params.company_group
start_modes = str(config.task_params.mode)
task_list = []


def init_task_list():
    global task_list
    persistence = Persistence.create_connection()
    for group_info in company_group.values():
        group_1 = group_info.get("group_1")
        group_2 = group_info.get("group_2")
        group_3 = group_info.get("group_3")
        select_sql = "SELECT query_company FROM qcc_param_company_info " \
                     "WHERE group_1='{}' and group_2='{}' and group_3='{}'".format(group_1, group_2, group_3)
        company_infos = persistence.execute(select_sql)
        for company_info in company_infos:
            task_list.append(company_info[0])


@deprecated(reason="线程启动后不释放GIL锁，导致第二个线程拿不到锁，无法执行", version="0.1")
def qccMultiThreadRun(company_names):
    """
    线程数：端口数 * 2 （每个端口启动 一个浏览器线程 和 一个获取数据的线程）
    每个线程的公司数量：math.ceil( 公司数量 / 端口数 ）
    :param company_names: 公司名称列表
    :return: 无
    """
    ports = ['4396', '4391', '4390']
    company_count = len(company_names)
    port_count = len(ports)
    job_thread_nums = port_count
    company_each_thread_count_max = math.ceil(company_count / port_count)
    threads = []
    for i in range(0, job_thread_nums):
        start_index = i * company_each_thread_count_max
        if i == job_thread_nums - 1:
            end_index = company_count
        else:
            end_index = (i + 1) * company_each_thread_count_max
        company_each_thread = company_names[start_index:end_index]
        thread_name = "Thread-" + str(i + 1) + "-"

        chrome_thread = threading.Thread(target=startChrome, args=(ports[i],), name=thread_name + "chrome")
        qcc_job_thread = threading.Thread(target=qccProcess, args=(ports[i], company_each_thread,)
                                          , name=thread_name + "qcc_job")
        threads.append(chrome_thread)
        threads.append(qcc_job_thread)
        chrome_thread.start()
        qcc_job_thread.start()


def qccMultiProcessRun(s_process_infos, company_names, jobs_only=False):
    """
    进程数：端口数 * 2 （每个端口启动 一个浏览器进程 和 一个获取数据的进程）
    每个进程的公司数量：math.ceil( 公司数量 / 端口数 ）
    :param s_process_infos: 进程信息
    :param jobs_only: 是否仅跑任务
    :param company_names: 公司名称列表
    :return: 无
    """
    company_count = len(company_names)
    port_count = len(s_process_infos)
    job_process_nums = port_count
    company_each_process_count_max = math.ceil(company_count / port_count)
    processes = []
    for i in range(0, job_process_nums):
        time.sleep(process_interval)
        start_index = i * company_each_process_count_max
        if i == job_process_nums - 1:
            end_index = company_count
        else:
            end_index = (i + 1) * company_each_process_count_max
        company_each_process = company_names[start_index:end_index]
        if jobs_only:
            printInfo("only start jobs")
            qccStartProcessJob(s_process_infos[i], company_each_process)
        else:
            printInfo("start jobs and chrome")
            qccSingleProcess(s_process_infos[i], company_each_process, i)


def qccMultiProcessStartBrowser(s_process_infos):
    for s_process_info in s_process_infos:
        qccStartBrowser(s_process_info)


def qccSingleProcess(process_info, company_names, i):
    qccStartBrowser(process_info)
    qccStartProcessJob(process_info, company_names)
    # qccStartThreadJob(port, company_names, i)


def qccStartProcessJob(process_info, company_names):
    qcc_job_process = Process(target=qccProcess, args=(process_info, company_names,))
    qcc_job_process.start()


def qccStartProcessVerification(s_process_infos):
    for process_info in s_process_infos:
        qcc_side_job_process = Process(target=qccFrequentVisit, args=(process_info,))
        qcc_side_job_process.start()


def start_process():
    started_modes = []
    for sub_mode in start_modes:
        if started_modes.count(sub_mode):
            printWarn("found repeated mode {}, ignored".format(sub_mode))
            continue
        else:
            started_modes.append(sub_mode)
        # 1：仅浏览器；
        if sub_mode == '1':
            qccMultiProcessStartBrowser(process_infos)
        # 2：仅job；
        if sub_mode == '2':
            qccMultiProcessRun(process_infos, task_list, jobs_only=True)
        # 3：监控进程
        if sub_mode == '3':
            qccStartProcessVerification(process_infos)


# 解析输入参数
# parser = argparse.ArgumentParser(description='Qcc unit dev')
# args = parser.parse_args()

if __name__ == '__main__':
    if platform.system() == "Darwin":
        multiprocessing.set_start_method('spawn')

    init_task_list()

    # 指定进程需要的信息
    start_process()
