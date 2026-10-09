import time
from datetime import datetime
import pygetwindow as gw
from pywinauto import Application
import pyautogui
import numpy as np
import easyocr
import re
import psutil
import subprocess
import os
import keyboard, mouse
import pyperclip
import sys
from pynput.mouse import Controller, Button











def github():
    print("제우스 github01   " + time.strftime("%H:%M", time.localtime()))

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


    if os.environ.get('COMPUTERNAME') in ["DESKTOP-MA2NLC4"]:
        url = "https://github.com/pyinstaller1/game/edit/main/vp2.txt"

    if os.environ.get('COMPUTERNAME') in ["DESKTOP-792RKKB"]:
        url = "https://github.com/pyinstaller1/game/edit/main/vp3.txt"

    if os.environ.get('COMPUTERNAME') in ["DESKTOP-OHGK5MV"]:
        url = "https://github.com/pyinstaller1/game/edit/main/vp4.txt"

    if os.environ.get('COMPUTERNAME') in ["DESKTOP-H9B70U0"]:
        url = "https://github.com/pyinstaller1/game/edit/main/vp5.txt"

    process = subprocess.Popen([chrome_path, "--new-window", "--start-maximized", "--force-device-scale-factor=1", url])   # 크롬 열기

    time.sleep(20)




    win = gw.getWindowsWithTitle('Editing game/vp')[0]
    app = Application().connect(handle=win._hWnd)
    app.window(handle=win._hWnd).set_focus()

    global left, top, width, height
    left = win.left
    top = win.top
    width = win.width
    height = win.height

    keyboard.press_and_release('win + up')
    time.sleep(3)

    keyboard.press_and_release('ctrl + a')
    time.sleep(0.5)    
    keyboard.press_and_release('ctrl + x')
    time.sleep(1)

    str_temp = pyperclip.paste()

    now = datetime.now()

    global str_support, str_purchase
    # str_support = "초원"
    # str_purchase = "구매"


    try:
        if str_support:
            pass
    except:
        str_support = '오류'


    try:
        if str_purchase:
            pass
    except:
        str_purchase = '오류'

        
    
    now = now.strftime("%m%d %H:%M\t") + str_support + "\t" + str_purchase + '\n'
    str_temp = now + str_temp
    time.sleep(1)
    pyperclip.copy(str_temp)


    keyboard.press_and_release('ctrl + v')

    time.sleep(1)
    mouse.move(left+(width*0.5), 127, absolute=True, duration=0.1)   # 스크롤 올리기
    mouse.click()
    time.sleep(0.5)
    keyboard.press_and_release('home')
    time.sleep(1)
    
    mouse.move(left+(width*0.95), top+(height*0.25), absolute=True, duration=0.1)   # 커밋
    mouse.click()

    time.sleep(1)

    keyboard.press_and_release('enter')

    time.sleep(8)



    for win in gw.getWindowsWithTitle('game/vp'):
        if win.title.strip():
            win.close()
            break





def a01_start():
    print("제우스 a01_start   " + time.strftime("%H:%M", time.localtime()))

    if not gw.getWindowsWithTitle('제우스'):
        print("제우스 창이 없습니다.")
        on()
        return

    win = gw.getWindowsWithTitle('제우스')[0]
    app = Application().connect(handle=win._hWnd)

    time.sleep(1)        

    try:
        app.window(handle=win._hWnd).set_focus()
    except:
        time.sleep(1)        
        app.window(handle=win._hWnd).set_focus()


    global left, top, width, height
    left = win.left
    top = win.top
    width = win.width
    height = win.height


    mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 절전 해제
    mouse.click()    



    
    return



def a02_bok():
    print("제우스 a02_bok   " + time.strftime("%H:%M", time.localtime()))

    global left, top, width, height



    win = gw.getWindowsWithTitle('제우스')[0]
    left = win.left
    top = win.top
    width = win.width
    height = win.height

    time.sleep(3)



    time.sleep(1)
    scr = pyautogui.screenshot(region=(left + int(width*0.38), top + int(height*0.46), int(width*0.1), int(height*0.05)))
    scr.save('scr_ze_bok.png')

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(scr))


    if results and results[0][1][:3] in ['장시간']:

        keyboard.press_and_release('space')
        time.sleep(1)

        mouse.move(left+(width*0.5), top+(height*0.63), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.5), top+(height*0.63), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)


        mouse.move(left+(width*0.5), top+(height*0.63), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)


        mouse.move(left+(width*0.9), top+(height*0.93), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)


        time.sleep(50)

    scr = pyautogui.screenshot(region=(left + int(width*0.05), top + int(height*0.12), int(width*0.1), int(height*0.06)))
    scr.save('scr_ze_bok.png')
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(scr))

    print(results)

    if results and results[0][1][:3] in ['테살리']:
        mouse.move(left+(width*0.2), top+(height*0.07), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.5), top+(height*0.8), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)


        mouse.move(left+(width*0.55), top+(height*0.61), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)

        keyboard.press_and_release('esc')
        time.sleep(1)

        mouse.move(left+(width*0.86), top+(height*0.83), absolute=True, duration=0.1)   # 잡화상인
        mouse.click()
        time.sleep(1)
    
        time.sleep(15)



        mouse.move(left+(width*0.2), top+(height*0.15), absolute=True, duration=0.1)   # 물약
        mouse.click()
        time.sleep(1)



        mouse.move(left+(width*0.23), top+(height*0.93), absolute=True, duration=0.1)   # 자동구매
        mouse.click()
        time.sleep(1)


        keyboard.press_and_release('space')
        time.sleep(1)
        
        keyboard.press_and_release('esc')
        time.sleep(1)

        mouse.move(left+(width*0.05), top+(height*0.3), absolute=True, duration=0.1)   # 이동
        mouse.click()
        time.sleep(1)


        mouse.move(left+(width*0.1), top+(height*0.3), absolute=True, duration=0.1)   # 이동
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.1), top+(height*0.68), absolute=True, duration=0.1)   # 이동
        mouse.click()
        time.sleep(1)


        keyboard.press_and_release('space')
        time.sleep(1)


        time.sleep(30)


        keyboard.press_and_release('g')
        time.sleep(1)



        mouse.move(left+(width*0.96), top+(height*0.81), absolute=True, duration=0.1)   # AUTO
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.02), top+(height*0.9), absolute=True, duration=0.1)   # 절전
        mouse.click()
        time.sleep(1)

        
    return





    


    scr = pyautogui.screenshot(region=(left + int(width*0.8), top + int(height*0.8), int(width*0.15), int(height*0.15)))
    scr.save("scr_ze_bok.png")

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(scr))
    print(results)


    return
    
    if results and results[0][1][:1] in ['잡', '집']:
        print(results[0][0])

        mouse.move(results[0][0][0][0] + left + int(width*0.8) + int(width*0.015), results[0][0][0][1] + top + int(height*0.8) - int(height*0.03), absolute=True, duration=0.1)
        mouse.click()
        time.sleep(15)

        mouse.move(left+(width*0.18), top+(height*0.388), absolute=True, duration=0.1)   # 최상급 물약
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.57), top+(height*0.58), absolute=True, duration=0.1)   # MAX
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.57), top+(height*0.75), absolute=True, duration=0.1)   # 구매
        mouse.click()
        time.sleep(1)

        mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 닫기
        mouse.click()
        time.sleep(1)

        a04_ai()

        return








def on():
    print("제우스 on   " + time.strftime("%H:%M", time.localtime()))


    for proc in psutil.process_iter():
        if "C2SLauncher.exe" in proc.name():
            proc.kill()
            print("C2SLauncher 를 닫았습니다.")


    os.startfile("c2sgpgcheck://open/?gpg_appid=com.com2us.es.android.google.kr.normal&hive_appid=com.com2us.es.pc.hive.kr.normal")



    time.sleep(7)




    for i in range(58):
        if gw.getWindowsWithTitle('C2SLauncher'):
            print('C2SLauncher')
            win_com2us = gw.getWindowsWithTitle('C2SLauncher')[0]
            app = Application().connect(handle=win_com2us._hWnd)
            app.window(handle=win_com2us._hWnd).set_focus()            
            break
        time.sleep(1)



    mouse.move(int(win_com2us.left + win_com2us.width * 0.9), int(win_com2us.top + win_com2us.height * 0.9))   # 화면 클릭
    mouse.click()
    time.sleep(1)




    time.sleep(23)

    keyboard.press_and_release('tab')
    keyboard.press_and_release('enter')   # AMD No

    time.sleep(70)

    a02_bok()


    return












def play():


    a01_start()
    a02_bok()

    return











if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "on":
            on()
        elif sys.argv[1] == "off":
            off()


            
        elif sys.argv[1] == "github":
            a01_start()
            a021_support()
            github()
        else:
            play()
    else:
        play()
        # on()
        # mission()
        # off()












    
