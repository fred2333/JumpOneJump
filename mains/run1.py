__author__ = '孙帅'

"""
python 调用ADB来玩微信跳一跳。
需要安装最新版ADB，老版本可能会一直报ADB连接不上的问题
本代码是在windows环境连接华为荣耀6X环境下开发。
手机连上电脑，开启调试模式后可用。

注意：可自己修改代码中的坐标参数。
推荐先进入跳一跳后在执行，并且不需要执行本代码中的startJump()方法。
我这里执行startJump()方法是让ADB帮我进入跳一跳的页面。

原理：通过ADB进行截屏，然后pull到电脑的  thisImgSrc  配置的地址中（运行时请修改  thisImgSrc 参数到自己的指定目录）
然后使用图像像素点的分析计算下一个中心点和当前小跳棋的中心点，然后计算两个点的距离，然后计算两点间的弧线
"""

import os
import time
from PIL import Image,ImageDraw
import math


thisImgSrc="z:/AdbJump/screenshot.png" # 截图pull到电脑的位置
thisMemorySrc="z:/AdbJump/Jump.txt" # 训练的数据存储的位置


arrData=[] # 训练数据，保存到数组格式中
try:
    f2 = open(thisMemorySrc, 'r')
    TrainingData=f2.read()
    arrData=TrainingData.split('\n')
    # print(arrData)
    f2.close()
except:pass


"""
初始化游戏，开始游戏
"""
def startJump():
    os.system("adb shell input keyevent 3") # 点击home按键
    time.sleep(0.5) # 暂停  秒
    os.system("adb shell am start com.tencent.mm/com.tencent.mm.ui.LauncherUI") # 直接打开 微信
    time.sleep(0.5) # 暂停  秒
    os.system("adb shell input swipe 640 500 640 1000") # 滑动,下拉
    time.sleep(0.5) # 暂停  秒
    os.system("adb shell input tap 135 410") # 点击进入“跳一跳”
    time.sleep(10) # 暂停  秒
    os.system("adb shell input tap 540 1350") # 点击开始游戏（跳一跳的开始）
    time.sleep(1) # 暂停  秒

"""
截屏
"""
def JieTu():
    os.system("adb shell /system/bin/screencap -p /sdcard/Jump/screenshot.png") # 截屏 并且保存到 手机的  /sdcard/Jump/screenshot.png  位置
    os.system("adb pull /sdcard/Jump/screenshot.png %s" % thisImgSrc) # 将 /sdcard/Jump/screenshot.png 文件上传到电脑的 z:/AdbJump/screenshot.png 位置
    os.system("adb shell rm /sdcard/Jump/screenshot.png") # 删除手机上的 /sdcard/Jump/screenshot.png 文件

"""
图片识别，计算位置和时间
"""
def TuShiBie():
    im=Image.open(thisImgSrc)
    cur_pixel = im.getpixel((5, 5)) # 获得图像的rgba值
    if(cur_pixel[0]>40 and cur_pixel[0]<55 and cur_pixel[1]>40 and cur_pixel[1]<50 and cur_pixel[2]>30 and cur_pixel[2]<60): #如果像素点的颜色是这一个，代表失败
        arrData[len(arrData)-1]=arrData[len(arrData)-1]+":error"
        print(arrData[len(arrData)-1]);
        f = open(thisMemorySrc, 'a')
        f.write(':error')
        f.close()
        restart()
        return

    box = (0,720,1080,1520) #创建一个选区范围【左、上、右、下】
    out= im.crop(box)  #截取获得新的图像（region就是新的图像）
    # out.show()
    draw = ImageDraw.Draw(out) # 创建一个画笔

    # 得到小跳棋的顶部的圆球，并且将颜色换成red,用来过滤颜色造成的中心点定位影响
    isRed=0
    for y in range(out.height):
        for x in range(out.width):
            cur_pixel = out.getpixel((x, y)) # 获得图像的rgba值
            if(cur_pixel[0]==53 and cur_pixel[1]==54 and cur_pixel[2]==62):
                isRed=1
                draw.ellipse((x-27,y-3,x+40,y+60), fill = "red") # 画一个红色的圆圈，覆盖掉顶部圆球
                break
        if(isRed==1):
            break

    DownCenterX=1000000 # 下一个板块的中心点的最左边的X坐标
    DownCenterY=0 # 找到下一个板块的中心的点的Y坐标

    upNum=0 # 上一行的板块的像素点的个数
    for y in range(out.height):
        # 开始过滤纯色的行，一行的颜色都是一样的代表，当前行没有出现板块
        one_cur_pixel=out.getpixel((0, y)) # 每一行的第一个像素的颜色
        thisNum=0 # 本行的板块的像素点个数
        for x in range(out.width):
            cur_pixel = out.getpixel((x, y)) # 获得图像的rgba值
            # 像素点跟当前行第一位是相似的点就排除掉
            rc=abs(int(one_cur_pixel[0])-int(cur_pixel[0]))
            gc=abs(int(one_cur_pixel[1])-int(cur_pixel[1]))
            bc=abs(int(one_cur_pixel[2])-int(cur_pixel[2]))
            if(rc<10 and  gc<10 and bc<10):
                continue
            else:
                # 如果是跳棋的小圆球也排除掉(颜色是red)
                if(cur_pixel[0]==255 and cur_pixel[1]==0 and cur_pixel[2]==0):
                    continue

                # print(cur_pixel)
                if(DownCenterX>x):
                    DownCenterX=x # 暂时记录最左边的x位置
                thisNum=thisNum+1 # 统计本行的板块的像素个数
        if(thisNum>upNum): # 每个板块的中心点是像素点最多的地方，所以那里最宽，代表那里就是中心横线
            upNum=thisNum
        elif(thisNum<=upNum and upNum!=0): # 当前行小于或者等于上一行，代表上一行就是下一个板块的中心线
            DownCenterY=y # 直接等于y，偏差一个像素点，影响可以忽略不计。
            break

    DownCenterX=DownCenterX+int(upNum/2.2) # 中心点X等于  暂时记录的最左边的点  加上  一半的板块的像素点
    print("下一个坐标",DownCenterX,DownCenterY) # 下个板块的中心点坐标
    draw.ellipse((DownCenterX,DownCenterY,DownCenterX+5,DownCenterY+5), fill = "red")

    ################################### 开始求当前小棋的中心点 ######################################
    thisCenterX=0
    thisCenterY=0
    upNum2=0 # 上一行的板块的像素点的个数
    for y in range(DownCenterY,out.height): # 从下一个板块的中心点的下一行开始(节省判断时间和计算资源)
        thisNum2=0 # 本行的板块的像素点个数
        for x in range(out.width):
            cur_pixel = out.getpixel((x, y)) # 获得图像的rgba值
            if((cur_pixel[0]>40 and cur_pixel[0]<60) and (cur_pixel[1]>40 and cur_pixel[1]<60) and (cur_pixel[2]>70 and cur_pixel[2]<100)):
                thisNum2=thisNum2+1
                thisCenterX=x-int(thisNum2/2)+5 # 这里的+5是可能的偏差量(加不加都可以)
        if thisNum2>upNum2:
            upNum2=thisNum2
            thisCenterY=y+5 # 这里的+5是偏差量

    print("当前坐标",thisCenterX,thisCenterY) # 当前板块的中心点坐标


    draw.ellipse((thisCenterX,thisCenterY,thisCenterX+6,thisCenterY+6), fill = "red")
    out.save("z:/AdbJump/asd.png",'png')


    # 求出两点的距离    根号下[(x1-x2)的平方+(y1-y2)的平方]
    d=math.sqrt((thisCenterX-DownCenterX)*(thisCenterX-DownCenterX) + (thisCenterY-DownCenterY)*(thisCenterY-DownCenterY))
    print("两点距离",int(d))
    timeNum=int((d*math.pi)/2) # 默认的屏幕长按时间
    ########## 开始读训练文本，有没有相近的位置和时间轴并且没有失败
    isSuccess=[] #成功的数据
    isFail=[] #失败的数据
    for i in range(len(arrData)):
        da=arrData[i]
        if(len(da)!=0):
            # 开始进行数据判断
            # print("da",da)
            # 开始根据   :  截取 ( 第一位是距离，第二位是点击时间，[第三位是失败信息])
            OneDa=da.split(':')
            # print(OneDa)
            if( abs( int(OneDa[0]) - d )<5 ):
                # print("距离差不多")
                if(len(OneDa)==2): # 单行数据只有两个位，代表是成功数据，
                    isSuccess.append(int(OneDa[1])) # 成功数据添加到成功数据的数组中
                else:
                    isFail.append(int(OneDa[1])) # 失败数据添加到数百数据的数组中

    if(len(isSuccess)!=0): # 有成功数据就对数据进行排序
        isSuccess=sorted(isSuccess)
        if(len(isSuccess)<2): #如果成功数据只有2个或1个，则，直接取第一个的时间
            timeNum=int(isSuccess[0])
        else: # 否则取时间点的中间的一个
            timeNum=int(isSuccess[int(len(isSuccess)/2)])
        print("相似成功时间",timeNum)
    if(len(isFail)!=0): # 有失败数据就进行排序
        isFail=sorted(isFail)
        if(isFail[len(isFail)-1]<=timeNum): # 失败时间中最大的一个时间还小于等于计算的可能时间
            if(len(isFail)<15): # 如果小于当前时间的失败数小于20，则继续往下减时间
                timeNum=isFail[0]-20
        else: # 如果往下递减20次还是失败，则往上递增
            timeNum=isFail[len(isFail)-1]+20 # 最大的一个时间+20毫秒

    swipe(int(timeNum))
    arrData.append('%d:%d' % (int(d),int(timeNum)))
    f = open(thisMemorySrc, 'a')
    f.write('\n%d:%d' % (d,timeNum))
    f.close()

"""
长按屏幕
参数：timeNum：毫秒数
"""
def swipe(timeNum):
    os.system("adb shell input swipe 500 500 501 501 %d" % timeNum) # 长按屏幕，
    time.sleep(2) # 暂停  秒


"""
重新开始
"""
def restart():
    im=Image.open("z:/AdbJump/screenshot.png")
    os.system("adb shell input tap 540 1580") # 点击再来一次
    time.sleep(2) # 暂停  秒





# startJump() # 初始化游戏（进入游戏，开始游戏）

while(True):
    JieTu() # 开始截屏
    # 开始图片识别
    TuShiBie()
    time.sleep(2) # 暂停  秒

