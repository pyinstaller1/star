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
    print("뱀피르 github01   " + time.strftime("%H:%M", time.localtime()))

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
    print("이클립스 a01_start   " + time.strftime("%H:%M", time.localtime()))


    if not gw.getWindowsWithTitle('이클립스: 더 어웨이크닝'):
        print("이클립스 창이 없습니다.")
        on()
        return



    win = gw.getWindowsWithTitle('이클립스: 더 어웨이크닝')[0]
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
    time.sleep(0.1)
    mouse.press()
    time.sleep(1)    
    mouse.move(int(left + width * 0.8), int(top + height * 0.5), duration=0.3)   # 절전 해제    
    time.sleep(1)
    mouse.release()
    time.sleep(3)
    
    return



def a02_bok():
    print("이클립스 a02_bok   " + time.strftime("%H:%M", time.localtime()))

    global left, top, width, height



    win = gw.getWindowsWithTitle('이클립스: 더 어웨이크닝')[0]
    left = win.left
    top = win.top
    width = win.width
    height = win.height



    time.sleep(1)
    scr = pyautogui.screenshot(region=(left + int(width*0.38), top + int(height*0.46), int(width*0.1), int(height*0.1)))
    scr.save('scr_ec_bok.png')

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(scr))
    print(results)

    if results and results[0][1][:3] in ['장시간']:
        print(results[0][0])

        mouse.move(left+(width*0.5), top+(height*0.63), absolute=True, duration=0.1)   # 확인
        mouse.click()
        time.sleep(1)

        on();
        
        return

    scr = pyautogui.screenshot(region=(left + int(width*0.8), top + int(height*0.8), int(width*0.15), int(height*0.15)))
    scr.save("scr_ec_bok.png")

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(scr))
    print(results)
    
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




def a03_jangbi():
    print("이클립스 a03_jangbi   " + time.strftime("%H:%M", time.localtime()))

    global left, top, width, height


    # 장비 분해
    mouse.move(left+(width*0.918), top+(height*0.07), absolute=True, duration=0.1)   # 가방
    mouse.click()
    time.sleep(2)

    mouse.move(left+(width*0.818), top+(height*0.95), absolute=True, duration=0.1)   # 분해
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.88), top+(height*0.95), absolute=True, duration=0.1)   # 자동선택
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.65), top+(height*0.63), absolute=True, duration=0.1)   # 분해
    mouse.click()
    time.sleep(2)


    # 성소
    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 메뉴
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.73), top+(height*0.27), absolute=True, duration=0.1)   # 메뉴
    mouse.click()
    time.sleep(2)

    mouse.move(left+(width*0.88), top+(height*0.9), absolute=True, duration=0.1)   # 일괄증축
    mouse.click()
    time.sleep(2)

    mouse.move(left+(width*0.938), top+(height*0.9), absolute=True, duration=0.1)   # 일괄수확
    mouse.click()
    time.sleep(2)

    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 닫기
    mouse.click()
    time.sleep(1)


    # 업적
    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 메뉴
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.88), top+(height*0.553), absolute=True, duration=0.1)   # 업적
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.938), top+(height*0.93), absolute=True, duration=0.1)   # 모두 받기
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 닫기
    mouse.click()
    time.sleep(1)


    # 우편
    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 메뉴
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.97), top+(height*0.738), absolute=True, duration=0.1)   # 우편
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.65), top+(height*0.938), absolute=True, duration=0.1)   # 모두받기
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.038), top+(height*0.38), absolute=True, duration=0.1)   # 계정
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.65), top+(height*0.938), absolute=True, duration=0.1)   # 모두받기
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.55), top+(height*0.618), absolute=True, duration=0.1)   # 모두받기
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 닫기
    mouse.click()
    time.sleep(1)

    return





def a04_ai():
    print("이클립스 a04_ai   " + time.strftime("%H:%M", time.localtime()))

    global left, top, width, height

    mouse.move(left+(width*0.97), top+(height*0.07), absolute=True, duration=0.1)   # 메뉴
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.918), top+(height*0.6), absolute=True, duration=0.1)   # AI모드
    mouse.click()
    time.sleep(1)

    mouse.move(left+(width*0.918), top+(height*0.938), absolute=True, duration=0.1)   # AI모드실행
    mouse.click()
    time.sleep(8)

    mouse.move(left+(width*0.03), top+(height*0.8), absolute=True, duration=0.1)   # 절전모드
    mouse.click()
    time.sleep(1)


















def off():
    print("이클립스 off   " + time.strftime("%H:%M", time.localtime()))

    a01_start()

    global left, top, width, height

    mouse.move(left+(width*0.98), top+(height*0.01), absolute=True, duration=0.1)   # X
    mouse.click()
    time.sleep(1)


    mouse.move(left+(width*0.6), top+(height*0.63), absolute=True, duration=0.1)   # X
    mouse.click()
    time.sleep(1)


    mouse.move(left+(width*0.57), top+(height*0.63), absolute=True, duration=0.1)   # X
    mouse.click()
    time.sleep(1)


    return











def on():
    print("이클립스 on   " + time.strftime("%H:%M", time.localtime()))


    for proc in psutil.process_iter():
        if "STOVE.exe" in proc.name():
            proc.kill()
            print("STOVE 를 닫았습니다.")

        if "EclipseTheAwakening.exe" in proc.name():
            proc.kill()
            print("이클립스를 닫았습니다.")

        if "EclipseTheAwakening-Win64-Shipping.exe" in proc.name():
            proc.kill()
            print("이클립스 Shipping을 닫았습니다.")

        if "ucldr_EclipseTheAwakening_KR_loader_x64.exe" in proc.name():
            proc.kill()
            print("이클립스 로더를 닫았습니다.")
            








    if os.environ.get('COMPUTERNAME') == "DESKTOP-H9B70U0":
        os.startfile("sgup://run/STOVE_ECLIPSE?auto_action=PrepareAndLaunch")

    time.sleep(5)



    for i in range(58):
        if gw.getWindowsWithTitle('STOVE'):
            print('STOVE')
            win_stove = gw.getWindowsWithTitle('STOVE')[0]
            app = Application().connect(handle=win_stove._hWnd)
            app.window(handle=win_stove._hWnd).set_focus()            
            break
        time.sleep(1)






    time.sleep(8)
    print(7)
    

    if os.environ.get('COMPUTERNAME') == "DESKTOP-H9B70U0":
        keyboard.write('ground077@naver.com')

    if os.environ.get('COMPUTERNAME') == "DESKTOP-MA2NLC4":
        keyboard.write('s070092@nate.com')

    if os.environ.get('COMPUTERNAME') == "DESKTOP-792RKKB":
        keyboard.write('s0700921@nate.com')

    if os.environ.get('COMPUTERNAME') == "DESKTOP-OHGK5MV":
        keyboard.write('ground077@kakao.com')
        
    keyboard.press_and_release('tab')
    keyboard.write('windows1!')
    keyboard.press_and_release('tab')
    keyboard.press_and_release('enter')

    time.sleep(18)

    keyboard.press_and_release('tab')
    keyboard.press_and_release('enter')   # AMD No
    


    # time.sleep(70)

    time.sleep(38)




    print("이클립스 a01_start   " + time.strftime("%H:%M", time.localtime()))

    win = gw.getWindowsWithTitle('이클립스: 더 어웨이크닝')[0]

    left = win.left
    top = win.top
    width = win.width
    height = win.height

    mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
    mouse.click()
    time.sleep(1)

    mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
    mouse.click()
    time.sleep(1)

    mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
    mouse.click()
    time.sleep(1)

    mouse.move(int(left + width * 0.55), int(top + height * 0.65))   # 화면 클릭
    mouse.click()
    time.sleep(1)


    time.sleep(3)
    mouse.move(int(left + width * 0.93), int(top + height * 0.93))   # 화면 클릭
    mouse.click()
    time.sleep(1)

    time.sleep(15)

    mouse.move(int(left + width * 0.5), int(top + height * 0.67))   # 무접속 플레이 결과 확인
    mouse.click()
    time.sleep(1)

    a02_bok()
    a03_jangbi()
    a04_ai()


    if os.environ.get('COMPUTERNAME') == "DESKTOP-H9B70U0":
        keyboard.write('ground077@naver.com')    


        for i in range(58):
            if gw.getWindowsWithTitle('STOVE'):
                print('STOVE')
                win_stove = gw.getWindowsWithTitle('STOVE')[0]
                app = Application().connect(handle=win_stove._hWnd)
                app.window(handle=win_stove._hWnd).set_focus()            
                break
            time.sleep(1)





        mouse.move(int(win_stove.left + win_stove.width * 0.9), int(win_stove.top + win_stove.height * 0.95))   # 멀티플레이 클릭
        mouse.click()
        time.sleep(3)


        mouse.move(int(win_stove.left + win_stove.width * 0.9), int(win_stove.top + win_stove.height * 0.57))   # 멀티플레이 클릭
        mouse.click()
        time.sleep(1)








        time.sleep(18)

        keyboard.press_and_release('tab')
        keyboard.press_and_release('enter')   # AMD No
        
        # time.sleep(70)
        time.sleep(38)


        print("이클립스 a01_start   " + time.strftime("%H:%M", time.localtime()))

        win = gw.getWindowsWithTitle('이클립스: 더 어웨이크닝')[0]

        left = win.left
        top = win.top
        width = win.width
        height = win.height

        mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
        mouse.click()
        time.sleep(1)

        mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
        mouse.click()
        time.sleep(1)

        mouse.move(int(left + width * 0.5), int(top + height * 0.5))   # 화면 클릭
        mouse.click()
        time.sleep(1)

        mouse.move(int(left + width * 0.55), int(top + height * 0.65))   # 화면 클릭
        mouse.click()
        time.sleep(1)


        time.sleep(3)
        mouse.move(int(left + width * 0.93), int(top + height * 0.93))   # 화면 클릭
        mouse.click()
        time.sleep(1)

        time.sleep(15)

        mouse.move(int(left + width * 0.5), int(top + height * 0.67))   # 무접속 플레이 결과 확인
        mouse.click()
        time.sleep(1)

        a02_bok()
        a03_jangbi()
        a04_ai()
        









def play():

    a01_start()
    a02_bok()    
    a03_jangbi()
    a04_ai()

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












    
