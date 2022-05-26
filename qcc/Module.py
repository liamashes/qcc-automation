from multiprocessing import Process

from util.Verfication import login
from util import Persistence, Verfication, Config
import uuid

from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException, \
    StaleElementReferenceException, NoSuchWindowException
from util.CommonUtils import *
import util.Config as config

# 基本数据
common_replace_dict = {" 至 ": "至"}
common_filter = {
    'equal': [''],
    '2': [],
    'SUBSTR': [],
    'replace': {}
}
cur_name = "current"
his_name = "history"
div_class_tab = "tablist"
div_class_sub = "sublist"
div_class_app = "app-ntable"


# chrome
data_refresh_interval = config.job_params.data_refresh_interval
page_load_interval = config.job_params.page_load_interval
operate_interval = config.job_params.operate_interval
job_interval = config.job_params.job_interval
tolerance = config.job_params.tolerance
print_result = config.job_params.print_result
retry_times = config.job_params.retry_times
retry_interval = config.job_params.retry_interval
task_dict = Config.job_params.task_dict
CHROME_EXE = config.chrome_script.exe_path
CHROME_INSTANCE_DIR = config.chrome_script.instance_dir


class TaskType(Enum):
    # table： CUR：当前；CUR_HIS：当前/历史
    TABLE_CUR = '1'
    TABLE_CUR_HIS = '2'
    # map: key-value
    MAP = '3'


def qccRunJobs(company, jobs, persistence, batch_id):
    for job_name in jobs.keys():
        time.sleep(job_interval)
        cur_job_name = "COMPANY:【" + company + "】 JOB:【" + job_name + "】"
        # 寻找页面元素
        if not qccFindingJob(company, job_name):
            return False
        tasks = jobs.get(job_name)
        for task in tasks:
            task_name = task.get("task_name")
            cur_task_name = cur_job_name + " TASK:【" + task_name + "】"
            sub_tasks = task.get("task_list")
            sub_task_index = 0
            for sub_task in sub_tasks:
                sub_task_index = sub_task_index + 1
                sub_task_name = cur_task_name + " 【 SUBTASK --- " + str(sub_task_index) + " 】"
                printInfo("处理" + sub_task_name)
                printInfo(sub_task)
                st_type = sub_task.get("task_type")
                st_ele_id = sub_task.get("ele_id")
                st_data_filter = sub_task.get("data_filter")
                if st_data_filter is None:
                    st_data_filter = common_filter
                st_source_deli = sub_task.get("source_deli")
                if st_source_deli is None:
                    st_source_deli = common_source_element_deli
                st_target_deli = sub_task.get("target_deli")
                if st_target_deli is None:
                    st_target_deli = common_target_element_deli
                # 数据库
                st_db_info = sub_task.get("db_info")
                if qccMatchTABLE_CUR(st_type) or qccMatchTABLE_CUR_HIS(st_type):
                    st_div_class_type = sub_task.get("div_class_type")
                    st_item_count = sub_task.get("item_count")
                    st_element_x = sub_task.get("element_x")

                    if qccMatchTABLE_CUR(st_type):
                        result_table = qccCurTable(st_ele_id, st_div_class_type, task_name, st_item_count,
                                                   element_x=st_element_x,
                                                   list_filter=st_data_filter,
                                                   source_deli=st_source_deli,
                                                   target_deli=st_target_deli)
                        qccSaveTable(persistence, result_table, st_db_info, st_item_count, batch_id, False, company)
                    if qccMatchTABLE_CUR_HIS(st_type):
                        result_table = qccCurHisTable(st_ele_id, st_div_class_type, task_name, st_item_count,
                                                      element_x=st_element_x,
                                                      list_filter=st_data_filter,
                                                      source_deli=st_source_deli,
                                                      target_deli=st_target_deli)
                        qccSaveTable(persistence, result_table, st_db_info, st_item_count, batch_id, True, company)
                if qccMatchMAP(st_type):
                    st_mid_xpath = sub_task.get("mid_xpath")
                    st_items = sub_task.get("items")
                    st_column_names = sub_task.get("column_names")
                    result_map = qccMap(st_ele_id, st_mid_xpath, task_name, st_items, data_filter=st_data_filter
                                        , column_names=st_column_names, source_deli=st_source_deli,
                                        target_deli=st_target_deli)
                    qccSaveMap(persistence, result_map, st_db_info, st_items, st_column_names, batch_id, company)
    return True


def qccSaveBatch(persistence, batch_id, task_param, company_names):
    head_sql = Persistence.get_insert_head("qcc_batch_info", "batch_id, task_param, company_names, process, thread")
    body_sql = Persistence.get_insert_body([batch_id, task_param, company_names, getProcessInfo(),
                                            threading.current_thread()])
    persistence.execute(head_sql + body_sql)


def qccSaveTable(persistence, result_table, db_info, item_count, batch_id, has_his, query_company):
    if result_table is None or len(result_table) == 0 or db_info is None:
        return
    table_name = db_info.get("table_name")
    item_fields = db_info.get("item_fields")
    real_item_count = item_count
    if has_his:
        # 需要包含标签
        real_item_count = real_item_count + 1
    if len(item_fields) != real_item_count:
        printErrorList(["数据保存失败，items数量不匹配", real_item_count, item_fields])
        return
    real_fields = ["batch_id", "query_company"] + item_fields
    values_list = []
    if not has_his:
        values_list = qccSaveTableGenValues(result_table, batch_id, query_company, real_item_count, values_list)
    else:
        # cur
        values_list = qccSaveTableGenValues(result_table.get(cur_name), batch_id, query_company, real_item_count, values_list)
        # his
        values_list = qccSaveTableGenValues(result_table.get(his_name), batch_id, query_company, real_item_count, values_list)
    if len(values_list) > 0:
        head_sql = Persistence.get_insert_head(table_name, real_fields)
        body_sql = Persistence.get_insert_bodies(values_list)

        persistence.execute(head_sql + body_sql)


def qccSaveTableGenValues(result_table, batch_id, query_company, item_count, values_list):
    if result_table is None or len(result_table) == 0:
        return values_list
    for result_obj in result_table:
        values = [batch_id, query_company]
        _obj_field_count = 0
        for key, value in result_obj.items():
            values.append(value)
            _obj_field_count = _obj_field_count + 1
            if _obj_field_count == item_count:
                break
        values_list.append(values)
    return values_list


def qccSaveMap(persistence, result_map, db_info, items, column_names, batch_id, query_company):
    if result_map is None or len(result_map) == 0 or db_info is None:
        return
    has_column = column_names is not None
    table_name = db_info.get("table_name")
    item_fields = db_info.get("item_fields")
    real_fields = ["batch_id", "query_company"]
    values = [batch_id, query_company]
    # check param
    if len(item_fields) != len(items):
        printErrorList(["数据保存失败，items数量不匹配", items, item_fields])
        return
    if has_column:
        column_fields = db_info.get("column_fields")
        if len(column_fields) != len(column_names):
            printErrorList(["数据保存失败，column_names数量不匹配", column_names, column_fields])
            return
        # { item: { column: value } }
        item_len = len(items)
        column_len = len(column_names)

        for i in range(item_len):
            item = items[i]
            item_obj = result_map.get(item)
            for j in range(column_len):
                column_name = column_names[j]
                # 字段名
                real_fields.append("{0}_{1}".format(item_fields[i], column_fields[j]))
                # 值
                value = item_obj.get(column_name)
                values.append(if_none(value))
    else:
        real_fields = real_fields + item_fields
        for item in items:
            _tmp_value = result_map.get(item)
            values.append(if_none(_tmp_value))

    head_sql = Persistence.get_insert_head(table_name, real_fields)
    body_sql = Persistence.get_insert_body(values)

    persistence.execute(head_sql + body_sql)


def qccMatchTABLE_CUR(st_type):
    if st_type.upper() == TaskType.TABLE_CUR.name or st_type == TaskType.TABLE_CUR.value:
        return True
    return False


def qccMatchTABLE_CUR_HIS(st_type):
    if st_type.upper() == TaskType.TABLE_CUR_HIS.name or st_type == TaskType.TABLE_CUR_HIS.value:
        return True
    return False


def qccMatchMAP(st_type):
    if st_type.upper() == TaskType.MAP.name or st_type == TaskType.MAP.value:
        return True
    return False


def qccFindingJob(company, job_name):
    job_xpath = "//a[contains(@class,'nav-tab')]/h2[contains(text(), '" + job_name + "')]"
    try:
        clickElement(job_xpath)
    except NoSuchElementException:
        printWarn("COMPANY:【" + company + "】 JOB【" + job_name + "】未找到，尝试切换tab页寻找")
        if switchTab(".*qcc.com/(firm|cfengxian)/.*html", is_regex=True) == 2:
            return False
        try:
            clickElement(job_xpath)
        except NoSuchElementException:
            printError("COMPANY:【" + company + "】 JOB【" + job_name + "】未找到，请检查页面")
    return True


def qccQuery(company_name):
    global driver
    main_page = "https://www.qcc.com/"
    result = switchTab(main_page, substr=False)
    if result == 1:
        driver.get(main_page)
    if result == 2:
        return False
    read_count = 0
    while read_count < retry_times:
        try:
            sendValue2Element("//input[@id='searchKey']", company_name)
            read_count = retry_times
        except NoSuchElementException as e:
            printWarn("failed to find search button in web browser, reason: {}". format(e.msg))
            time.sleep(retry_interval)
            read_count = read_count + 1
            if read_count == retry_times:
                return False
    element = driver.find_element(By.XPATH, "//button[text()='查一下']")
    element.click()
    return True


def qccClickFirst():
    clickElements("//tr[contains(@class, 'tsd0')]//a[contains(@class, 'title') and "
                  "contains(@class, 'copy-value')]", 0)


def qccMap(ele_id, mid_xpath, task_name, items, data_filter=common_filter, column_names=None
           , source_deli=common_source_element_deli
           , target_deli=common_target_element_deli):
    time.sleep(data_refresh_interval)
    elements_xpath = generateSectionXpathCommon(ele_id, mid_xpath)
    if not ("table" in mid_xpath or "tr" in mid_xpath):
        elements_xpath = elements_xpath + "//table//tr"
    raw_list = elements2List(getElements(elements_xpath), replace_dict=common_replace_dict, source_deli=source_deli,
                             target_deli=target_deli)
    # 清洗信息
    raw_list = filterList(raw_list, data_filter)
    # 基本信息重排序
    raw_items = sortItem(items, raw_list)
    # 提取信息
    item_dict = extractItemsByTag(raw_items, raw_list, column_names)
    display(item_dict, task_name)
    return item_dict


def qccCurTable(ele_id, div_class_type, task_name, item_count, element_x="tr", list_filter=common_filter
                , source_deli=common_source_element_deli
                , target_deli=common_target_element_deli):
    return qccCommonTable(ele_id, div_class_type, task_name, item_count, element_x=element_x, list_filter=list_filter
                          , source_deli=source_deli
                          , target_deli=target_deli)


def qccCurHisTable(ele_id, div_class_type, task_name, item_count, element_x="tr", list_filter=common_filter
                   , source_deli=common_source_element_deli
                   , target_deli=common_target_element_deli):
    his_xpath = generateSectionXpath(ele_id,
                                     div_class_type) + "//span[a[span[contains(text(), '历史" + task_name + "')]]]"
    try:
        # 当前
        cur_table = qccCommonTable(ele_id, div_class_type, task_name, item_count, element_x=element_x,
                                   list_filter=list_filter,
                                   _cur_name=cur_name, source_deli=source_deli, target_deli=target_deli)
        # 历史
        his_table = qccCommonTable(ele_id, div_class_type, task_name + "-历史", item_count, element_x=element_x,
                                   list_filter=list_filter,
                                   _cur_name=his_name, click_xpath=his_xpath, click_index=0, source_deli=source_deli,
                                   target_deli=target_deli)
        return {cur_name: cur_table, his_name: his_table}
    except NoSuchElementException:
        printError("【" + task_name + "】信息不存在")


def qccCommonTable(section_id, div_class, title, item_count, element_x="tr", list_filter=common_filter, _cur_name=""
                   , click_xpath=None, click_index=None, raw_list=[]
                   , source_deli=common_source_element_deli
                   , target_deli=common_target_element_deli):
    section_xpath = generateSectionXpath(section_id, div_class)
    next_page_xpath = section_xpath + "//li/a[text()='>']"
    last_page_xpath = section_xpath + "//li/a[text()='<']"
    elements_xpath = section_xpath
    if not ("table/tr" in element_x or "table//tr" in element_x):
        elements_xpath = elements_xpath + "//table[@class='ntable']/" + element_x
    else:
        elements_xpath = elements_xpath + element_x
    detail_raw_list = qccGetRawList(elements_xpath, title, next_page_xpath=next_page_xpath
                                    , last_page_xpath=last_page_xpath, item_count=item_count
                                    , click_xpath=click_xpath, click_index=click_index, raw_list=raw_list
                                    , source_deli=source_deli, target_deli=target_deli)
    # 清洗信息
    item_table = extractTable(filterList(detail_raw_list, list_filter), item_count, tag=_cur_name, _table=[])
    display(item_table, title)
    return item_table


def qccGetRawList(elements_xpath, name, next_page_xpath=None, last_page_xpath=None, click_xpath=None, click_index=None
                  , raw_list=[], item_count=0
                  , source_deli=common_source_element_deli
                  , target_deli=common_target_element_deli):
    """
    流程： 点击（可选）-> 获取元素 -> 翻页获取
    说明： 点击中可能会遇到vip弹窗，需要自动关闭
    翻页： 翻页策略：如果有上一页，那么点到没有为止
    """
    if click_xpath is not None:
        click_finished = False
        click_count = 0
        while not click_finished and click_count < 3:
            try:
                if click_index is None:
                    clickElement(click_xpath)
                else:
                    clickElements(click_xpath, click_index)
                    click_finished = True
                    if closeVipPoppedWindow():
                        printError("【" + name + "】需要付费才可以查看，请使用会员账号")
                        return raw_list
            except WebDriverException:
                printError("【" + name + "】需要付费才可以查看，请使用会员账号")
                closeVipPoppedWindow()
                return raw_list
            except IndexError:
                click_count = click_count + 1
                printWarn("页面尚未加载完成，重试 " + str(click_count) + " 次")
                time.sleep(operate_interval)
        if not click_finished:
            printWarn("未点击到【" + name + "】，默认数据不存在，返回")
            return raw_list
    closeVipPoppedWindow()
    # 翻到第一页
    if last_page_xpath is not None:
        is_first_page = False
        while not is_first_page:
            try:
                clickElement(last_page_xpath)
                time.sleep(operate_interval)
            except (NoSuchElementException, StaleElementReferenceException):
                printInfo("已切换为第一页")
                is_first_page = True
    # 开始遍历
    has_page = True
    _raw_list = raw_list
    _last_page_content = []
    try_one_more = False
    while has_page or try_one_more:
        if try_one_more:
            try_one_more = False
        try:
            # 页面加载需要时间
            retry_time = 3
            success = False
            repeat_content_read = 0
            while not success and retry_time > 0:
                # 此处等待，待数据刷新出来是必要的
                time.sleep(data_refresh_interval)
                _tmp_raw_list = elements2List(getElements(elements_xpath), replace_dict=common_replace_dict,
                                              source_deli=source_deli, target_deli=target_deli)
                if len(_tmp_raw_list) == 0 or len(_tmp_raw_list) < item_count:
                    retry_time = retry_time - 1
                else:
                    if checkRepeatPage(_last_page_content, _tmp_raw_list):
                        repeat_content_read = repeat_content_read + 1
                        if repeat_content_read >= tolerance:
                            printDebug(str(repeat_content_read) + "次读到重复数据，遇到特殊问题，结束翻页")
                            # has_page = False
                            break
                        else:
                            printDebug("读到重复数据，可能翻页未成功，重试")
                    else:
                        _raw_list = _raw_list + _tmp_raw_list
                        _last_page_content = _tmp_raw_list
                        success = True
        except WebDriverException:
            # printWarn("VIP提示，关闭后重新尝试")
            _raw_list = elements2List(getElements(elements_xpath), raw_list=_raw_list, replace_dict=common_replace_dict
                                      , source_deli=source_deli
                                      , target_deli=target_deli)
        if next_page_xpath is not None:
            try:
                clickElement(next_page_xpath)
            except NoSuchElementException:
                printInfo("当前为最后一页，结束遍历")
                has_page = False
            except ElementNotVisibleException:
                has_page = False
                try_one_more = True
        else:
            has_page = False
    closeVipPoppedWindow()
    return _raw_list


def checkRepeatPage(page1, page2):
    return "".join(page1) == "".join(page2)


def generateSectionXpath(section_id, div_class):
    return generateSectionXpathCommon(section_id, "//div[contains(@class, '" + div_class + "')]")


def generateSectionXpathCommon(section_id, mid_xpath):
    return "//section[@id='" + section_id + "' and contains(@class, 'data-section')]" + mid_xpath


def closeVipPoppedWindow():
    try:
        clickElement("//div[contains(@class, 'vip-moda-dialog')]/div/button[contains(@class, 'close')]")
        return True
    except NoSuchElementException:
        printDebug("未检测到VIP弹窗")
        return False


def display(result, tag):
    if result is None or len(result) == 0:
        printWarn("未检查到【" + tag + "】")
    else:
        printInfo("【" + tag + "】如下：")
        if print_result:
            printJson(result)
        else:
            printJsonDebug(result)


def startChrome(port):
    # 启动浏览器
    start_cmd = "{0} --remote-debugging-port={1} --user-data-dir={2}/{1}".format(CHROME_EXE, port, CHROME_INSTANCE_DIR)
    printInfo("execute cmd: {}".format(start_cmd))
    os.system(start_cmd)


def shutdownChrome(port):
    # killShellCmd("start-chrome.sh {}".format(port))
    killShellCmd("remote-debugging-port={}".format(port), kill_all=True)


def restartChrome(process_info):
    # 关闭该端口对应的浏览器
    shutdownChrome(process_info.get('chrome-port'))
    # 启动该浏览器
    time.sleep(operate_interval)
    qccStartBrowser(process_info)


def qccStartBrowser(process_info):
    chrome_process = Process(target=startChrome, args=(process_info.get('chrome-port'),))
    chrome_process.start()


def qccProcess(process_info, company_names):
    global driver
    port, username, s_password = parse_process_info(process_info)
    qccInit(port)
    Verfication.driver = driver
    login(username, s_password)
    persistence = Persistence.create_connection()
    batch_id = str(uuid.uuid1()).replace("-", "")
    job_dict = task_dict
    qccSaveBatch(persistence, batch_id, job_dict, company_names)
    for company_name in company_names:
        while not qccRun(company_name, persistence, batch_id, job_dict):
            try:
                if driver:
                    driver.close()
            except WebDriverException as e:
                printWarn("shut down driver abnormally, reason: {}".format(e.msg))
            restartChrome(process_info)
            qccInit(port)
    persistence.close()


def qccFrequentVisit(process_info):
    global driver
    port, username, s_password = parse_process_info(process_info)
    qccInit(port)
    while True:
        handles = driver.window_handles
        for handle in handles:
            try:
                if handle_current_handle(handle, port):
                    break
            except WebDriverException:
                qccFrequentVisit(process_info)
        time.sleep(config.task_params.monitor_interval)


def handle_current_handle(handle, port):
    global driver
    try:
        printInfo("check frequent visit verification: {}".format(driver.current_url))
        driver.switch_to.window(handle)
        time.sleep(0.5)
        target = getElement("//iframe[contains(@src, 'verify.qcc.com')]")  #
        if target is None:
            printInfo("no frequent visit verification found: {}".format(driver.current_url))
        else:
            Verfication.driver = driver
            Verfication.frequent_visit()
            return True
    except NoSuchElementException:
        qccInit(port)
        printInfo("no frequent visit verification found: {}".format(driver.current_url))
    except NoSuchWindowException:
        qccInit(port)
        printWarn("window has been closed, ignore")
    return False


def parse_process_info(process_info):
    port = process_info.get('chrome-port')
    username = process_info.get('username')
    s_password = process_info.get('password')
    return port, username, s_password


def qccInit(port):
    # 初始化driver
    global driver
    driver = appUnitInit(url="127.0.0.1:" + port)


def qccRun(company, persistence, batch_id, job_dict):
    if not qccQuery(company):
        return False
    time.sleep(data_refresh_interval)
    qccClickFirst()
    time.sleep(data_refresh_interval)
    if not qccRunJobs(company, job_dict, persistence, batch_id):
        return False
    driver.close()
    return True
