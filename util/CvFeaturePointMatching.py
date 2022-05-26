import time

import cv2
import matplotlib.pyplot as plt

from util.CommonUtils import printInfo, if_true, printDebug
from util.CvCommonUtils import get_image, Canny, show_image_list, apply_mask, get_mask

TASK = "Feature Point Matching"


def time_cost(func):
    def _time_cost(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        printDebug("==> time-cost: %6f (s)     %s " % (time.time() - start, func.__name__))
        return ret

    return _time_cost


def bgr_rgb(img):
    (r, g, b) = cv2.split(img)
    return cv2.merge([b, g, r])


def orb_detect(image_a, image_b):
    # feature match
    orb = cv2.ORB_create()

    kp1, des1 = orb.detectAndCompute(image_a, None)
    kp2, des2 = orb.detectAndCompute(image_b, None)

    if des1 is None or des2 is None:
        return image_a, []

    # create BFMatcher object
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Match descriptors.
    matches = bf.match(des1, des2)

    # Sort them in the order of their distance.
    matches = sorted(matches, key=lambda x: x.distance)

    # Draw first 10 matches.
    img3 = cv2.drawMatches(image_a, kp1, image_b, kp2, matches[:100], None, flags=2)

    return bgr_rgb(img3), matches


@time_cost
def sift_detect(img1, img2, detector='surf'):
    if detector.startswith('si'):
        printDebug("sift detector......")
        sift = cv2.xfeatures2d.SIFT_create()
    else:
        printDebug("surf detector......")
        sift = cv2.xfeatures2d.SURF_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # BFMatcher with default params
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Apply ratio test
    good = [[m] for m, n in matches if m.distance < 0.5 * n.distance]

    # cv2.drawMatchesKnn expects list of lists as matches.
    img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, good, None, flags=2)

    return bgr_rgb(img3), good


def Surf(_image):
    img = get_image(_image, new_copy=True)
    gray = if_true(len(img.shape) == 3, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), img)
    surf = cv2.xfeatures2d.SURF_create()
    kp, dst = surf.detectAndCompute(gray, None)  # 第二个参数为mask区域
    surf_img = img.copy()
    cv2.drawKeypoints(gray, kp, surf_img)
    show_image_list([("surf", surf_img), ("source", gray)], fig_title="surf_result")


def Surf_compare(_source, _target):
    from util.CvUtils import get_image
    left_image = get_image(_source)
    right_image = get_image(_target)

    # 创造sift
    sift = cv2.xfeatures2d.SURF_create()
    kp1, des1 = sift.detectAndCompute(left_image, None)
    kp2, des2 = sift.detectAndCompute(right_image, None)  # 返回关键点信息和描述符

    flann_index_kdtree = 0
    index_params = dict(algorithm=flann_index_kdtree, trees=5)
    search_params = dict(checks=50)  # 指定索引树要被遍历的次数

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)
    matches_mask = [[0, 0] for i in range(len(matches))]
    print("matches", matches[0])
    for i, (m, n) in enumerate(matches):
        if m.distance < 0.07 * n.distance:
            matches_mask[i] = [1, 0]

    draw_params = dict(matchColor=(0, 255, 0), singlePointColor=None,
                       matchesMask=matches_mask, flags=2)  # flag=2只画出匹配点，flag=0把所有的点都画出
    result_image = cv2.drawMatchesKnn(left_image, kp1, right_image, kp2, matches, None, **draw_params)
    # show_image_list([("source image", left_image), ("target image", right_image), ("result image", result_image), ])
    plt.imshow(result_image)
    plt.show()


def dev_demo():
    Surf(slice_bg)
    # Surf_compare(best_frame, slice_bg_mask)


def net_demo(source, target):
    # ORB
    img_orb, orb_good_matches = orb_detect(source, target)

    # SIFT or SURF
    img_sift, surf_good_matches = sift_detect(source, target)

    printInfo("orb matches: {}, surf matches: {}".format(len(orb_good_matches), len(surf_good_matches)))
    show_image_list([("source", source), ("target", target), ("orb", img_orb), ("surf", img_sift)], TASK)


def diff_image(source, target):
    # ORB
    img_orb, orb_good_matches = orb_detect(source, target)

    # SIFT or SURF
    img_surf, surf_good_matches = sift_detect(source, target)
    return img_surf, surf_good_matches, orb_good_matches


if __name__ == '__main__':
    # failed
    # de3255dedfe241a3914402e9165b9c6b
    # 5f204d9b6a0c47ef8fca6d314ad4cda2
    slice_bg = "slice_bg.png"
    slice_bg_mask = "slice_mask.png"

    baddest_frame = "baddest_frame.png"
    best_frame = "best_frame.png"
    crop_bg = "crop_bg.png"
    #
    mask = get_mask(slice_bg)
    edge_slice_bg = Canny(apply_mask(slice_bg, mask), is_blurred=False)
    # net_demo(Canny(get_image(best_frame)), edge_slice_bg)

    cur_frame = "cur_frame_{}.png"
    for i in range(1, 7):
        net_demo(Canny(apply_mask(cur_frame.format(i), mask), is_blurred=False), edge_slice_bg)
