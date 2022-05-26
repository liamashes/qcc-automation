import math
import time
import urllib.request

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

from util.CommonUtils import *
from util.CvUtils import crop_image, match_slice

port = "5001"
driver = None

SLICE_BG_SIZE = 80
BG_WIDTH = 300
BG_HEIGHT = 200
RETRY_TIMES = 3


def init():
    global driver
    driver = appUnitInit(url="127.0.0.1:" + port)


def captcha_demo():
    global driver
    main_page = "https://www.geetest.com/en/adaptive-captcha-demo"
    result = switchTab(main_page, substr=False)
    if result == 1:
        driver.get(main_page)
    else:
        driver.refresh()
    # 切换滑块验证页面
    clickElement("//button[text()='Slide CAPTCHA']")
    time.sleep(0.5)
    clickElement("//div[@class='geetest_btn_click']")


def geetest_slide_captcha(save_path=None):
    global driver
    slice_bg_img = None
    if save_path is None:
        save_path = os.path.split(os.path.realpath(__file__))[0] + "/../files/"
    while slice_bg_img is None:
        # 获取滑块
        slice_bg_img, image_id = down_bg_by_xpath("//div[@class='geetest_slice_bg']", "slice_bg", local_path=save_path)
        if slice_bg_img is None:
            return False
            # clickElement("//a[@class='geetest_refresh']")
            # time.sleep(1)

    bg_img, image_id = down_bg_by_xpath("//div[@class='geetest_bg']", "bg", local_path=save_path)

    slice_top, ratio = get_top_pixel_height()
    crop_bg_img = crop_image(bg_img, slice_top, 0, SLICE_BG_SIZE+1, BG_WIDTH, save_file=True)
    slice_distance, f_b_s, s_b_s = match_slice(slice_bg_img, crop_bg_img, save_path+image_id,
                                               bg_width=BG_WIDTH, slice_width=SLICE_BG_SIZE)

    # 滑动滑块
    slice_button = getElement("//div[@class='geetest_btn']")
    ActionChains(driver).click_and_hold(slice_button).perform()
    ActionChains(driver).move_by_offset(xoffset=slice_distance/ratio, yoffset=0).perform()
    ActionChains(driver).release().perform()
    return True


def down_bg_by_xpath(xpath, tag, local_path="./files"):
    try:
        element = getElement(xpath)
        if element is None:
            return None, None
    except NoSuchElementException:
        printWarn(xpath + " is not exists")
        return None, None
    element_style = element.get_attribute("style")
    if element_style is None:
        return None, None
    # 图片信息
    image_url = element_style.split('"')[1]
    src_image_name = image_url.rsplit("/", 1)[1]
    image_id = src_image_name.split(".")[0]
    # 创建路径
    save_path = local_path + "/" + image_id
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    image_name = "{}/{}.png".format(save_path, tag)
    # 下载并保存
    urllib.request.urlretrieve(image_url, filename=image_name)
    printInfo("remote url: {}, save to: {}".format(image_url, image_name))
    return image_name, image_id


def get_top_pixel_height():
    """
    获取滑块上边界
    :return: 上边界
    """
    element = getElement("//div[@class='geetest_slice']")
    if element is None:
        return None
    element_style = element.get_attribute("style")
    if element_style is None:
        return None
    width = parse_slice_style(element_style, 0)
    top = parse_slice_style(element_style, 2)
    ratio = SLICE_BG_SIZE / width
    real_top = math.floor(top * ratio)
    printInfo("width: {}, top: {}, real_top: {}, ratio: {}".format(width, top, real_top, ratio))
    return real_top, ratio


def parse_slice_style(style, index):
    return float(style.split(";")[index].split(": ")[1].replace("px", ""))


def captcha_test():
    while True:
        captcha_demo()
        geetest_slide_captcha()
        time.sleep(5)


def login(username, s_password, need_switch=True):
    global driver
    main_page = "https://qcc.com/weblogin?back=%2F"
    if need_switch:
        result = switchTab(main_page, substr=False)
        if result == 1:
            driver.get(main_page)
        else:
            driver.refresh()
    else:
        driver.refresh()
    time.sleep(1)
    password_div_prefix = "//div[@class='password-login_wrapper']"
    try:
        clickElement("//div[@class='login-tab' and a[text()='密码登录']]")
    except NoSuchElementException as e:
        # 自动跳转主页，即是已经登录了
        if driver.current_url == "https://www.qcc.com/":
            printInfo("用户: {} 已经登录".format(username))
            return True
        else:
            printErrorList(["用户: {} 登录失败，切换登录页失败，原因不详".format(username), e.msg])
            return False
    send_count = 0
    while not sendValue2Element(password_div_prefix + "//input[@name='phone-number']", username) \
            and send_count < RETRY_TIMES:
        clickElement("//div[@class='login-change']/img")
        send_count = send_count + 1
        time.sleep(1)
    time.sleep(0.5)
    pass_xpath = password_div_prefix + "//input[@name='password']"
    # clearElement(pass_xpath)
    sendValue2Element(pass_xpath, s_password)
    time.sleep(0.5)
    clickElement(password_div_prefix + "//button[@class='btn btn-primary login-btn']")
    time.sleep(2)
    while True:
        try:
            geetest_box = getElement("//div[@class='geetest_box']")
        except NoSuchElementException as e:
            printDebug(e.msg)
            break
        if geetest_box is None:
            break
        if not geetest_slide_captcha():
            login(username, s_password, need_switch=False)
            break
        else:
            time.sleep(3)
    printInfo("用户: {} 登录成功".format(username))
    return True


def frequent_visit():
    first = True
    finished = False
    while not finished:
        if first:
            first = False
        else:
            driver.refresh()
            time.sleep(1)
        target = getElement("//iframe[contains(@src, 'verify.qcc.com')]")
        driver.switch_to.frame(target)
        clickElement("//a[@class='btn btn-primary captcha-btn' and text()='验证一下']")
        time.sleep(2)
        while True:
            try:
                geetest_box = getElement("//div[@class='geetest_box']")
            except NoSuchElementException as e:
                finished = True
                printDebug(e.msg)
                break
            if geetest_box is None:
                finished = True
                break
            if not geetest_slide_captcha():
                break
            else:
                time.sleep(3)
        driver.switch_to.default_content()


if __name__ == '__main__':
    init()
    # captcha_test()
    login("19951652853", "cL220427!1")
    # clean_shadow(slice_bg)
    # locate_1(slice_bg, bg)
    # MatchTemplate(slice_bg, bg)
