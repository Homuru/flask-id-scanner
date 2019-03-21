from __future__ import print_function
import cv2
import os
import sys
import pytesseract
import numpy as np
import tensorflow as tf
import re

# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--image", required=True,
#                 help="path to input image to be OCR"d")
# args = vars(ap.parse_args())

# pp = Pre-processing


def resize_image(img):
    img_size = img.shape
    im_size_min = np.min(img_size[0:2])
    im_size_max = np.max(img_size[0:2])

    im_scale = float(600) / float(im_size_min)
    if np.round(im_scale * im_size_max) > 1200:
        im_scale = float(1200) / float(im_size_max)
    new_h = int(img_size[0] * im_scale)
    new_w = int(img_size[1] * im_scale)

    new_h = new_h if new_h // 16 == 0 else (new_h // 16 + 1) * 16
    new_w = new_w if new_w // 16 == 0 else (new_w // 16 + 1) * 16

    re_im = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return re_im


def letterOnly(string):
    return re.sub("[^a-zA-Z]+", "", string)


def takeFirst(elem):
    return elem[0]


def takeSecond(elem):
    return elem[1]


def ppID(string):
    string = string.replace("ó", "6")
    string = string.replace("á", "4")
    string = string.replace("é", "6")
    string = string.replace("D", "0")
    string = string.replace("o", "0")
    temp = re.search(r"\d+", string)
    if (temp != None):
        return temp.group(0)
    else:
        return ""


def getID(result):

    print(f"ID:{ppID(result[0])}")
    ID = ppID(result[0])
    result = result[1:]
    return result, ID


def ppName(string):
    if (string.split(":")[1] != None):
        return string.split(":")[1]
    else:
        return ""


def getName(result):
    # print(result[0])
    name = ""
    if (":" in result[0]):
        if (result[0][(len(result[0])-1)] == ":"):
            print(f"Tên:{result[1]}")
            name = result[1]
            result = result[2:]
        else:
            print(f"Tên:{ppName(result[0])}")
            name = ppName(result[0])
            result = result[1:]
    else:
        print(f"Tên:{result[0]}")
        name = result[0]
        result = result[2:]
    return result, name


def ppDOB(string):
    temp = re.search(r"(\d+/\d+/\d+)", string)
    if (temp != None):
        return temp.group(1)
    else:
        return ""


def getDOB(result):
    dob = ""
    if (result[0][0].isdigit()):
        print(f"DOB:{ppDOB(result[0])}")
        dob = ppDOB(result[0])
        result = result[2:]
    else:
        print(f"DOB:{ppDOB(result[0])}")
        dob = ppDOB(result[0])
        result = result[1:]
    return result, dob


def ppSex(string):
    if(":" in string):
        gender = string.split(":")[1]
    if(";" in string):
        gender = string.split(";")[1]
    female = ["ư", "Ư", "ữ", "Ữ"]
    for ele in female:
        if(ele in gender):
            return "Nữ"
    return "Nam"


def ppCountry(string):
    if(":" in string):
        return string.split(":")[1]
    else:
        if(";" in string):
            return string.split(";")[1]
        else:
            return ""


def getSexAndCountry(result):  # fucking LMAO
    country = ["Quốc", "tịch", "Việt"]
    sex = ["Giới", "tính"]
    res_country = ""
    res_sex = ""
    for index, ele in enumerate(country):
        if(ele in result[0]):
            print(f"Quốc tịch:{ppCountry(result[0])}")
            res_country = ppCountry(result[0])
            print(f"Giới tính: {ppSex(result[1])}")
            res_sex = ppSex(result[1])
            break
        if(index == (len(country)-1)):
            print(f"Quốc tịch:{ppCountry(result[1])}")
            res_country = ppCountry(result[1])
            print(f"Giới tính: {ppSex(result[0])}")
            res_sex = ppSex(result[0])
    result = result[2:]
    return result, res_country, res_sex


def ppHome(string):
    if(":" in string):
        return string.split(":")[1]
    else:
        if(";" in string):
            return string.split(";")[1]
        else:
            return ""


def getHome(result):
    home = ""
    if(result[0].find(":") < len(result[0])):
        if(":" in result[1] or ";" in result[1]):
            print(f"Quê quán:{ppHome(result[0])}")
            home = ppHome(result[0])
            result = result[1:]
        else:
            if(not "Nơi" in result[1]):
                string = result[0] + " " + result[1]
                # print(string)
                print(f"Quê quán:{ppHome(string)}")
                home = ppHome(string)
                result = result[2:]
            else:
                print(f"Quê quán:{ppHome(result[0])}")
                home = ppHome(result[0])
                result = result[1:]
    return result, home


def ppAddress(string):
    if(":" in string):
        return string.split(":")[1]
    else:
        if(";" in string):
            return string.split(";")[1]
        else:
            return string


def ppExpire(string):
    temp = re.search(r"(\d+/\d+/\d+)", string)
    if(temp != None):
        return temp.group(1)


def getExpire(result):
    string = result[len(result)-1]
    print(f"Expire Date:{ppExpire(string)}")
    expire = ppExpire(string)
    result.pop()
    return result, expire


def getAddress(result):
    address = ""
    temp = result
    # If the first line is "Noi thuong tru" aka not include ":" sign, ignore it !
    if(not ":" in temp[0]):
        temp = temp[1:]
    # Join all the remaining lines
    fullString = ""
    for ele in temp:
        if(fullString != ""):
            fullString = fullString + " " + ele
        else:
            fullString = fullString + ele
    print(f"Nơi thường trú:{ppAddress(fullString)}")
    address = ppAddress(fullString)
    return None, address


############## PRE_PROCESSING ################


def threshHolding(image):
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                 cv2.THRESH_BINARY, 11, 2)


def addingBorder(image):
    white = [255, 255, 255]
    return cv2.copyMakeBorder(token, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, [169, 169, 169])


def Blurring(image):
    return cv2.blur(gray, (5, 5))


def bilateralFiltering(image):
    return cv2.bilateralFilter(gray, 9, 75, 75)


def fastDenoising(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)


def getImage(path):
    # load the example image and convert it to grayscale
    image = cv2.imread(path)
    # Resize before put in the coordinates
    image = resize_image(image)
    gray = image
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print("------------------")
    return gray


def getCoordinate(path):
    # Get the result file (txt)
    print("Extracting text...")
    path = path.replace("demo", "res")
    filePath = path[:-3] + "txt"
    print(f"Reading: {filePath}")
    file = open(filePath, "r")
    y_list = []
    for line in file:
        split = line.split(",")
        split = split[:-2]
        split = [int(x) for x in split]
        y_list.append(split)
    y_list.sort(key=takeSecond)
    print("------------------")
    return y_list


def printList(result):
    print("------------------")
    for index, ele in enumerate(result):
        print(f"{index}:{ele}")
    print("------------------")


def getNakedResult(textArea, image):
    print("Getting naked result")
    result = []
    for split in textArea:
        # Define config parameters.
        # "-l vie"  for using the Vietnamese language
        config = ("-l vie")
        padding = int((split[5]-split[1])*0.15)
        # Selecting the text area with extra 7px
        token = image[split[1]-padding:split[5]+padding,
                      split[0]-padding:split[2]+padding]
        token = fastDenoising(token)
        # token = cv2.cvtColor(token, cv2.COLOR_BGR2GRAY)
        # token = addingBorder(token)
        # token = threshHolding(token)
        # Put through Tesseract
        text = pytesseract.image_to_string(token, config=config)
        result.append(text)
        print(f"{text}")
        # Display for testing
        # cv2.imshow("Input", token)
        # cv2.waitKey(0)
    print("------------------")
    return result


def getInformation(path):
    image = getImage(path)
    coordinate = getCoordinate(path)
    result = getNakedResult(coordinate, image)
    print("Brute-force processing...")
    # Remove communism xD
    result = result[3:]
    temp = result
    # Remove blank space
    for index, ele in enumerate(result):
        if(not ele):
            temp.pop(index)
    result, ID = getID(result)
    result, name = getName(result)
    result, dob = getDOB(result)
    result, country, sex = getSexAndCountry(result)
    result, home = getHome(result)
    result, expire = getExpire(result)
    result, address = getAddress(result)
    return {"ID": ID, "Name": name, "DOB": dob, "Country": country, "Sex": sex, "Home": home, "Address": address}


# res = getInformation("data/demo/CC9.jpg")
# print(res)


# Threshold + border or do nothing
# padding = 20%: 1, 2
