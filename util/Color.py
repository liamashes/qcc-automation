import operator
from functools import reduce
import util.Config as config

method_name_len = config.log_params.method_name_len
method_name_dict = {}


class Color:
    Black = 0
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    Magenta = 5
    Cyan = 6
    White = 7


class Mode:
    Foreground = 30
    Background = 40
    ForegroundBright = 90
    BackgroundBright = 100


def tagColor(tag, m=Mode.ForegroundBright, end=''):
    if tag == "DEBUG":
        _color = Color.Blue
    if tag == "INFO":
        _color = Color.Green
    if tag == "WARNING":
        _color = Color.Yellow
    if tag == "ERROR":
        _color = Color.Red
    print(t_color(_color, m), end='')
    print('{:7}'.format(tag), end='')
    print(tre_set(), end=end)


def pidColor(pid, m=Mode.ForegroundBright, end=''):
    print(t_color(Color.Magenta, m), end='')
    print('{:7}'.format(pid), end='')
    print(tre_set(), end=end)


def methodColor(method, m=Mode.ForegroundBright, end=''):
    print(t_color(Color.Cyan, m), end='')
    try:
        print(('{:'+str(method_name_len)+'}').format(reformatMethodName(method)), end='')
    except TypeError:
        print("类型错误:"+method, end='')
    print(tre_set(), end=end)


def reformatMethodName(method="UNKNOWN"):
    # print(str(len(method)) + "\t" + method)
    if method is None or method == "":
        method = "UNKNOWN"
    if method in method_name_dict.keys():
        return method_name_dict.get(method)
    if len(method) <= method_name_len:
        method_name_dict[method] = method
        return method
    items = method.split(".")
    result_pre = ""
    for i in range(1, len(items)):
        cur = items[i-1][:1]
        result_pre = result_pre + "." + cur
        _tmp_items = items[i:]
        _tmp_len_sum = reduce(operator.add, map(len, _tmp_items)) + 1
        if _tmp_len_sum <= method_name_len:
            result = result_pre[1:] + "." + ".".join(_tmp_items)
            method_name_dict[method] = result
            return result.strip()


def t_color(c, m=Mode.Foreground):
    return '\033[{}m'.format(m + c)


def tre_set():
    return '\033[0m'


def color_demo():
    import os

    os.system('')

    # usage
    print(t_color(Color.Red) + 'hello' + tre_set())
    print(t_color(Color.Green, Mode.Background) + 'color' + tre_set())
    print()

    COLOR_NAMES = ['Black', 'Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan', 'White']
    MODE_NAMES = ['Foreground', 'Background', 'ForegroundBright', 'BackgroundBright']

    fmt = '{:11}' * len(COLOR_NAMES)
    print(' ' * 20 + fmt.format(*COLOR_NAMES))

    for mode_name in MODE_NAMES:
        print('{:20}'.format(mode_name), end='')
        for color_name in COLOR_NAMES:
            mode = getattr(Mode, mode_name)
            color = getattr(Color, color_name)
            print(t_color(color, mode) + 'HelloColor' + tre_set(), end=' ')
        print()


def reformatMethodNameDemo():
    print(reformatMethodName("automation.UDF.switchTab"))
    print(reformatMethodName("automation.QCCUnitDev.qccGetBasicInfo"))
    print(reformatMethodName("automation.QCCUnitDev.qccGBRDebt"))
    print(reformatMethodName("automation.QCCUnitDev.qccGBRPledge"))


def func_test():
    print("sad", end='')


if __name__ == '__main__':
    # color_demo()
    # reformatMethodNameDemo()
    func_test()
