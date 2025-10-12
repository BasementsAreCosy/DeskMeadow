from PyQt5.QtGui import QPixmap
import os
import sys

def resourcePath(relativePath):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativePath)
    return os.path.join(os.path.abspath("."), relativePath)

def getDataPath():
    return os.path.join(os.environ['APPDATA'], 'DeskMeadow')

def roundToNearestBase(num, base):
    return round(num/base)*base

def sign(num):
    if num == 0:
        return 0
    return int(num/abs(num))

def clamp(num, bound):
    return max(min(num, bound), -bound)

def invClamp(num, bound):
    return max(abs(num), bound) * sign(num)

def scaleImage(imagePath, size):
    if imagePath:
        return QPixmap(imagePath).scaled(round(size), round(size))
    return None