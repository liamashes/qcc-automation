import cv2

from util.CommonUtils import printInfo, printDebug, printInfoList
from util.CvCommonUtils import Canny, apply_mask, get_mask, crop_image
from util.CvFeaturePointMatching import diff_image
import util.Config as config

DEBUG = config.log_params.debug
SAVE_OTHER_MATCH = config.log_params.save_other_match


def match_slice(slice_bg_path, crop_bg_path, local_path="./files/",
                bg_width=300, slice_width=80):
    """
    对于背景条图片（裁剪后）进行逐帧比对，图片处理流程如下：
        * 根据滑块获得滤波mask，并应用于滑块和对应桢的数据，以减少图片外信息对于目标块信息的影响；
        * 分别对滑块、桢应用canny算法，检测到边缘；此处不使用**滤波算法
        * 使用surf、orb做匹配度评估，优先采用surf进行评估，对于匹配度最高的块进行数据保留，相同匹配度的使用数组留存
    :param slice_width: 滑块图片宽度
    :param bg_width: 背景图片宽度
    :param slice_bg_path: 滑块图片存储路径
    :param crop_bg_path: 裁剪后的图片存放路径
    :param local_path: 本地存储路径
    :return:
    """
    # 初始化存储路径
    frame_name_template = "{}/{}.png"
    tmp_frame_name = frame_name_template.format(local_path, "cur_frame")
    tmp_slice_edge_name = frame_name_template.format(local_path, "edge_slice_frame")
    tmp_frame_edge_name = frame_name_template.format(local_path, "edge_cur_frame")
    best_frame_name = frame_name_template.format(local_path, "best_frame")
    baddest_frame_name = frame_name_template.format(local_path, "baddest_frame")
    slice_mask_name = frame_name_template.format(local_path, "slice_mask")
    best_diff_result_name = frame_name_template.format(local_path, "best_diff_result")
    baddest_diff_result_name = frame_name_template.format(local_path, "baddest_diff_result")
    # 初始化匹配结果的相关参数
    fi_index = 0
    first_best_sim, second_best_sim = 0, 0
    fi_baddest_index = 0
    fi_baddest_similarity = 1
    best_possible_match = []
    # 获取滤波模版
    mask = get_mask(slice_bg_path)
    # 对于滑块先做处理
    edge_slice_bg = Canny(apply_mask(slice_bg_path, mask), "slice_bg", is_blurred=False)
    # 横向遍历桢，此处因为背景是已经切割过的，因此不考虑纵向的偏移量
    for i in range(bg_width - slice_width + 1):
        _tmp_image = crop_image(crop_bg_path, 0, i, 80, 80, return_path=False)
        cur_frame = apply_mask(_tmp_image, mask)

        # 弃用：基于像素点、直方图：问题在于两边都有蒙版，效果很差
        # 基于边缘、特征点匹配的检测
        edge_cur_frame = Canny(cur_frame, "cur_frame", is_blurred=False)
        cur_result, sur_matches, orb_matches = diff_image(edge_slice_bg, edge_cur_frame)
        first_sim = len(sur_matches)
        second_sim = len(orb_matches)

        # 根据surf、orb匹配结果进行数据持久化、更新匹配结果
        if first_sim > first_best_sim or (first_sim == first_best_sim and second_sim > second_best_sim):
            best_possible_match = []
            cv2.imwrite(best_frame_name, _tmp_image)
            cv2.imwrite(best_diff_result_name, cur_result)
            fi_index, first_best_sim, second_best_sim = i, first_sim, second_sim
        else:
            # 备选数据存储策略：
            #   与最优解有相同surf的信息进行存储及桢的存储，以便于问题定位
            #   注意：这里有效的桢数和存储数组的大小一致，没有对无效的桢进行清理
            if SAVE_OTHER_MATCH:
                if first_sim > 0 and first_sim == first_best_sim:
                    best_possible_match.append(i)
                    # 名称_当前序号_全局序号
                    cv2.imwrite("{}/{}_{}.png".format(local_path, "cur_frame", len(best_possible_match), i), _tmp_image)
                    cv2.imwrite("{}/{}_{}.png".format(local_path, "best_diff_result", len(best_possible_match), i),
                                cur_result)
        if first_sim < fi_baddest_similarity:
            cv2.imwrite(baddest_frame_name, _tmp_image)
            cv2.imwrite(baddest_diff_result_name, cur_result)
            fi_baddest_index, fi_baddest_similarity = i, first_sim
        printDebug("cur frame index: {}, surf similarity: {}, orb similarity: {}".format(i, first_sim, second_sim))

    # 打印结果
    printInfo("best match frame[index: {}, surf similarity: {}, orb similarity: {}]".format(fi_index, first_best_sim
                                                                                            , second_best_sim))
    printInfoList(["other best match index: ", best_possible_match])
    printInfo("baddest match frame[index: {}, similarity:{}]".format(fi_baddest_index, fi_baddest_similarity))
    return fi_index, first_best_sim, second_best_sim
