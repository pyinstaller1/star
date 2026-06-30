from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from api.start_kospi import set_kospi, set_kospi_1day
from api.ilbong import *
from api.db import *
from api.hoga import *
from api.naver_fin import *

from django.db import connection, transaction
from django.http import HttpResponse

import json
import requests
import queue
import threading

from dotenv import load_dotenv
import os
load_dotenv()

def get_token():
    url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"

    headers = {
        "content-type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "appkey": os.getenv("LS_APP_KEY"),
        "appsecretkey": os.getenv("LS_APP_SECRET"),
        "scope": "oob"
    }

    res = requests.post(url, headers=headers, data=data, verify=False)

    if res.status_code != 200:
        print("토큰 발급 실패 ❌, status:", res.status_code, ' ', res.text)
        return None

    return res.json().get("access_token")


def start_kospi(request):
    set_kospi()
    return redirect('index')

def start_kospi_1day(request):
    set_kospi_1day()
    return redirect('index')





# views.py (참고용 예시)
def get_ilbong_1day_view(request):
    qrycnt_param = request.GET.get('qrycnt', '500') # 프론트에서 보낸 값 받기
    set_kospi()
    
    final_qrycnt = int(qrycnt_param)
    
    return StreamingHttpResponse(get_ilbong_1day(final_qrycnt), content_type='text/event-stream')



def render_to_group_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT group_name, group_order 
            FROM tb_gwansim 
            ORDER BY group_order ASC
        """)
        groups = cursor.fetchall()

    # 전체 페이지가 아니라 리스트 조각만 있는 '별도의 템플릿'을 만들거나, 
    # 조건부 렌더링을 사용하여 조각만 보냅니다.
    return render(request, 'gwansim_list_snippet.html', {'groups': groups})

















def fin_gwansim_view(request):
    raw_groups = select_tb_gwansim_group()
    groups_data = []

    def add_comma(val):
        try: return format(int(str(val).replace(',', '')), ',')
        except: return val
    
    for g in raw_groups:
        gid, gname = g[0], g[1]
        # raw_stocks에 [0:코드, 1:종목명, 2:현재가, 3:등락률, 4:시총, 5:RSI] 포함
        raw_stocks = select_tb_gwansim_stock(gid)
        
        stocks_list = []

        for s in raw_stocks:
            stocks_list.append({
                'shcode': s[0],
                'hname': s[1],
                'price': add_comma(s[2]),
                'rate': s[3],
                'cap': add_comma(s[4]),       # 시가총액 추가
                'rsi': s[5],       # RSI 추가
            })
            
        groups_data.append({
            'id': gid, 
            'name': gname, 
            'stocks': stocks_list
        })

    list_kospi = select_tb_kospi()
    list_kospi_formatted = []
    for row in list_kospi:
        try:
            # RSI 처리 로직
            rsi_raw = row[5] if len(row) > 5 else None
            rsi_val = float(rsi_raw) if rsi_raw and str(rsi_raw).strip().lower() != 'nan' else None
            
            list_kospi_formatted.append({
                'code': row[0],
                'name': row[1],
                'price': row[2],
                'rate': row[3],
                'cap': row[4],
                'rsi': rsi_val
            })
        except (ValueError, TypeError, IndexError):
            continue

    return render(request, 'fin.html', {
        'groups': groups_data,
        'list_kospi': list_kospi_formatted
    })














def index_view(request):
    code = request.GET.get('code', '005930')
    name = request.GET.get('name', '삼성전자')
    
    raw_groups = select_tb_gwansim_group()
    groups_data = []
    
    for g in raw_groups:
        gid = g[0]
        gname = g[1]
        raw_stocks = select_tb_gwansim_stock(gid)
        
        stocks_list = []
        for s in raw_stocks:
            # --- 금액에 쉼표 추가 로직 ---
            try:
                price_val = str(s[2]).replace(',', '') if s[2] else "0"
                formatted_price = format(int(price_val), ',')
            except:
                formatted_price = s[2]
            
            stocks_list.append({
                'shcode': s[0],
                'hname': s[1],
                'price': formatted_price, # 쉼표 포함
                'rate': s[3],
                'rsi': s[5],
                'cap': s[4],                
            })
            
        groups_data.append({
            'id': gid,
            'name': gname,
            'stocks': stocks_list,
            'count': len(stocks_list)
        })

    # 검색용 리스트에도 금액/등락률 데이터 포함
    raw_kospi = select_tb_kospi()
    kospi_list = []
    for s in raw_kospi:
        try:
            p_val = format(int(str(s[2]).replace(',', '')), ',')
        except:
            p_val = s[2]
            
        kospi_list.append({
            'code': s[0], 
            'name': s[1],
            'cap': s[4],

        })





    list_ilbong = get_ilbong_db(code)
    if list_ilbong:
        list_ilbong = list_ilbong[::-1]







    last_update_str = "미정"
    try:
        sam_data = get_ilbong_data(code)
        if sam_data:
            last_day = sam_data[-1]
            raw_date = str(last_day.get('date', '')).strip()
            
            dt_obj = None
            if len(raw_date) == 8 and raw_date.isdigit():
                last_update_str = f"{int(raw_date[4:6])}/{int(raw_date[6:8])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y%m%d')
                except: pass
            elif "-" in raw_date and len(raw_date.split("-")) == 3:
                parts = raw_date.split("-")
                last_update_str = f"{int(parts[1])}/{int(parts[2])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y-%m-%d')
                except: pass
            else:
                last_update_str = raw_date

            if dt_obj:
                weeks = ['월', '화', '수', '목', '금', '토', '일']
                weekday_str = weeks[dt_obj.weekday()]
                last_update_str = f"{last_update_str} ({weekday_str})"
    except Exception as e:
        last_update_str = "확인불가"




    

    return render(request, 'index.html', {
        'list_ilbong': json.dumps(list_ilbong),
        'groups': groups_data,
        'kospi': kospi_list,
        'last_update': last_update_str,
        'init_code': code,
        'init_name': name,



        
    })











def gwansim_view(request):
    raw_groups = select_tb_gwansim_group()
    groups_data = []

    def add_comma(val):
        try: return format(int(str(val).replace(',', '')), ',')
        except: return val
    
    for g in raw_groups:
        gid, gname = g[0], g[1]
        # raw_stocks에 [0:코드, 1:종목명, 2:현재가, 3:등락률, 4:시총, 5:RSI] 포함
        raw_stocks = select_tb_gwansim_stock(gid)
        
        stocks_list = []

        for s in raw_stocks:
            stocks_list.append({
                'shcode': s[0],
                'hname': s[1],
                'price': add_comma(s[2]),
                'rate': s[3],
                'cap': add_comma(s[4]),       # 시가총액 추가
                'rsi': s[5],       # RSI 추가
            })
            
        groups_data.append({
            'id': gid, 
            'name': gname, 
            'stocks': stocks_list,
            'count': len(stocks_list)
        })

    list_kospi = select_tb_kospi()
    list_kospi_formatted = []
    for row in list_kospi:
        try:
            # RSI 처리 로직
            rsi_raw = row[5] if len(row) > 5 else None
            rsi_val = float(rsi_raw) if rsi_raw and str(rsi_raw).strip().lower() != 'nan' else None
            
            list_kospi_formatted.append({
                'code': row[0],
                'name': row[1],
                'price': row[2],
                'rate': row[3],
                'cap': row[4],
                'rsi': rsi_val
            })
        except (ValueError, TypeError, IndexError):
            continue

    return render(request, 'gwansim.html', {
        'groups': groups_data,
        'list_kospi': list_kospi_formatted
    })







def gwansim_index_view(request):
    raw_groups = select_tb_gwansim_group()
    groups_data = []
    
    for g in raw_groups:
        gid = g[0]
        gname = g[1]
        raw_stocks = select_tb_gwansim_stock(gid)
        
        stocks_list = []
        for s in raw_stocks:
            # --- 금액에 쉼표 추가 로직 ---
            try:
                price_val = str(s[2]).replace(',', '') if s[2] else "0"
                formatted_price = format(int(price_val), ',')
            except:
                formatted_price = s[2]
            
            stocks_list.append({
                'shcode': s[0],
                'hname': s[1],
                'price': formatted_price, # 쉼표 포함
                'rate': s[3],
            })
            
        groups_data.append({
            'id': gid,
            'name': gname,
            'stocks': stocks_list,
            'count': len(stocks_list)
        })

    # 검색용 리스트에도 금액/등락률 데이터 포함
    raw_kospi = select_tb_kospi()
    kospi_list = []
    for s in raw_kospi:
        try:
            p_val = format(int(str(s[2]).replace(',', '')), ',')
        except:
            p_val = s[2]
            
        kospi_list.append({
            'shcode': s[0], 
            'hname': s[1],
            'price': p_val,
            'rate': s[3]
        })
    
    return render(request, 'index.html', {
        'groups': groups_data,
        'kospi': kospi_list,
    })










@csrf_exempt
def delete_gwansim_group_view(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            group_id = data.get('group_id')
            
            if not group_id:
                return JsonResponse({'success': False, 'message': '그룹 ID가 없습니다.'})

            if delete_gwansim_group(group_id):
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': '삭제 중 DB 오류 발생'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def update_gwansim_group_order_view(request):
    try:
        # 프론트엔드에서 전송한 group_ids 배열을 가져옴
        group_ids = json.loads(request.POST.get('group_ids', '[]'))
        
        if not group_ids:
            return JsonResponse({'status': 'error', 'message': '데이터가 없습니다.'}, status=400)

        # db.py의 함수 호출
        if update_gwansim_group_order(group_ids):
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'DB 업데이트에 실패했습니다.'}, status=500)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def update_gwansim_stock_order_view(request):
    if request.method == 'POST':
        try:
            group_id = request.POST.get('group_id')
            shcodes_raw = request.POST.get('shcodes') # JSON 문자열로 수신
            
            if not group_id or not shcodes_raw:
                return JsonResponse({'status': 'error', 'message': '데이터 부족'}, status=400)

            # JSON 문자열 ['code1', 'code2']를 파이썬 리스트로 변환
            shcode_list = json.loads(shcodes_raw)
            
            # DB 함수 호출
            if update_gwansim_stock_order(group_id, shcode_list):
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'DB 반영 실패'}, status=500)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'message': 'POST 요청만 허용됩니다.'}, status=405)





        
@csrf_exempt
def add_gwansim_stock_view(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            code = data.get('code')
            group_id = data.get('group_id')

            success = insert_tb_gwansim_stock(group_id, code)
            
            if success:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': '이미 등록된 종목이거나 오류가 발생했습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def add_gwansim_group_view(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            group_name = data.get('group_name')

            if not group_name:
                return JsonResponse({'success': False, 'message': '그룹명을 입력하세요.'})

            insert_tb_gwansim_group(group_name)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})






@csrf_exempt
def add_gwansim_group_st_view(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            group_name = data.get('group_name')
            codes = data.get('codes')

            if not group_name:
                return JsonResponse({'success': False, 'message': '그룹명을 입력하세요.'})

            insert_tb_gwansim_group_st(group_name, codes)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

















def delete_gwansim_stock_view(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        shcode = request.POST.get('shcode')
        
        if group_id and shcode:
            delete_tb_gwansim_stock(group_id, shcode)
            
    return redirect('gwansim')



































@csrf_exempt # 프론트엔드 fetch 통신 시 CSRF 토큰 검증을 임시 면제하여 통신 에러를 방지합니다.
def save_check_setting_view(request):
    """체크박스 설정 문자열을 받아 DuckDB에 업데이트합니다."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings_json = data.get('settings', '{}')
            
            # db.py의 update_check_setting 함수 호출
            update_check_setting(settings_json)
            
            return JsonResponse({'status': 'success', 'message': '저장 완료'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'POST 요청만 허용됩니다.'}, status=405)


def get_check_setting_view(request):
    """DuckDB에서 저장된 체크박스 설정값을 읽어 프론트엔드로 반환합니다."""
    try:
        # db.py의 select_check_setting 함수 호출
        settings_json = select_check_setting()
        
        # settings_json은 이미 문자열 형태이므로 json.loads로 딕셔너리 변환 후 전달
        return JsonResponse({'status': 'success', 'settings': json.loads(settings_json)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)




























































def index(request):
    """메인 페이지 로드 시 NaN 값을 완벽 세척하여 프론트 자바스크립트 파싱 에러를 원천 차단"""
    list_kospi = select_tb_kospi()
    
    initial_code = '005930' # 삼성전자 기본 세팅
    if list_kospi:
        initial_code = list_kospi[0][0] if isinstance(list_kospi[0], (tuple, list)) else list_kospi[0].get('코드', '005930')

    ilbong_data = get_ilbong_db(shcode=initial_code)
    if ilbong_data:
        ilbong_data = ilbong_data[::-1]

    # ⭐️ [핵심 방어막] 자바스크립트 Unexpected token 'N' 에러 예방을 위한 데이터 전처리
    clean_ilbong = []
    if ilbong_data:
        for day in ilbong_data:
            if isinstance(day, dict):
                cleaned_day = {}
                for k, v in day.items():
                    # float 타입이면서 NaN 이거나 무한대(inf)일 경우 null(None)로 변환!
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        cleaned_day[k] = None
                    else:
                        cleaned_day[k] = v
                clean_ilbong.append(cleaned_day)
            else:
                clean_ilbong.append(day)

    # 리스트 데이터를 안전한 kospi_list 구조로 변환하여 템플릿 전달
    list_kospi_formatted = []
    for row in list_kospi:
        try:
            rsi_raw = row[5] if len(row) > 5 else None
            if rsi_raw is not None and str(rsi_raw).strip().lower() != 'nan':
                rsi_val = float(rsi_raw)
            else:
                rsi_val = None

            list_kospi_formatted.append({
                'code': row[0],
                'name': row[1],
                'price': row[2],
                'rate': row[3],
                'cap': row[4],
                'rsi': rsi_val
            })
        except:
            continue

    # ⭐️ [자로 잰 듯한 바인딩] 중복 DB 조회 없이 이미 정제된 list_kospi_formatted에서 초기 종목명(name) 추출
    initial_name = "삼성전자"  # 매칭 실패를 대비한 기본 방어선
    for stock in list_kospi_formatted:
        if stock['code'] == initial_code:
            initial_name = stock['name']
            break

    # JSON 호환용 null 변환 스트링 마감
    json_ilbong = json.dumps(clean_ilbong)
    
    # 첫 화면 진입 시에도 상단 메뉴 탭 리스트를 무조건 렌더링하도록 DB에서 조회
    groups_data = select_tb_gwansim_group()
    
    # 💡 [날짜 완벽 복원 + 요일 생성]
    last_update_str = "미정"
    try:
        sam_data = get_ilbong_data('005930')
        if sam_data:
            last_day = sam_data[-1]
            raw_date = str(last_day.get('date', '')).strip()
            
            dt_obj = None
            if len(raw_date) == 8 and raw_date.isdigit():
                last_update_str = f"{int(raw_date[4:6])}/{int(raw_date[6:8])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y%m%d')
                except: pass
            elif "-" in raw_date and len(raw_date.split("-")) == 3:
                parts = raw_date.split("-")
                last_update_str = f"{int(parts[1])}/{int(parts[2])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y-%m-%d')
                except: pass
            else:
                last_update_str = raw_date

            if dt_obj:
                weeks = ['월', '화', '수', '목', '금', '토', '일']
                weekday_str = weeks[dt_obj.weekday()]
                last_update_str = f"{last_update_str} ({weekday_str})"
    except Exception as e:
        last_update_str = "확인불가"

    db_settings = select_check_setting()

    # 파이썬 None 상태로 넘어가 자바스크립트 'None is not defined' 에러가 터지는 현상을 원천 방어합니다.
    if db_settings is None:
        db_settings = 'null'

    return render(request, 'index.html', {
        'kospi': list_kospi_formatted,
        'code': initial_code,
        'name': initial_name,
        'json_ilbong': json_ilbong,
        'groups': groups_data, 
        'last_update': last_update_str,
        'db_settings': db_settings  
    })




















def partial_kospi_view(request):
    """
    프린트 로그 분석 결과에 맞춰 튜플 인덱스(RSI, CAP) 번호를 자로 잰 듯이 수정했습니다.
    """
    group_id = request.GET.get('group_id')
    
    try:
        groups = select_tb_gwansim_group()  
        kospi_list = []
        
        # 💡 1. 관심종목 탭을 클릭했을 때 (2번째 이후 탭)
        if group_id:
            raw_data = select_tb_gwansim_stock(group_id)
            if raw_data:
                for row in raw_data:
                    try:
                        if isinstance(row, (tuple, list)) and len(row) >= 11:
                            code = str(row[0]).strip()
                            name = str(row[1]).strip()
                            price = row[2]
                            rate = row[3]
                            cap = row[4]    
                            rsi = row[10]  
                        else:
                            continue
                    except Exception as e:
                        print(f"❌ 관심종목 인덱스 예외: {e}")
                        continue
                        
                    try:
                        price_clean = str(price).replace(',', '').strip()
                        p_val = format(int(price_clean), ',')
                    except:
                        p_val = price

                    if rsi is not None and str(rsi).strip().lower() != 'nan':
                        try: rsi = round(float(rsi), 1)
                        except: rsi = None
                    else:
                        rsi = None

                    kospi_list.append({
                        'code': code,
                        'name': name,
                        'price': p_val,
                        'rate': rate,
                        'rsi': rsi,
                        'cap': cap
                    })
                        
        # 💡 2. 첫 번째 탭 (전체 KOSPI - 정상 작동 규격 유지)
        else:
            raw_data = select_tb_kospi()
            if raw_data:
                for row in raw_data:
                    if isinstance(row, (tuple, list)) and len(row) >= 6:
                        code = str(row[0]).strip()
                        name = str(row[1]).strip()
                        price = row[2]
                        rate = row[3]
                        cap = row[4]
                        rsi = row[5]
                        
                        try:
                            price_clean = str(price).replace(',', '').strip()
                            p_val = format(int(price_clean), ',')
                        except:
                            p_val = price

                        if rsi is not None and str(rsi).strip().lower() != 'nan':
                            try: rsi = round(float(rsi), 1)
                            except: rsi = None
                        else:
                            rsi = None

                        kospi_list.append({
                            'code': code,
                            'name': name,
                            'price': p_val,
                            'rate': rate,
                            'rsi': rsi,
                            'cap': cap
                        })

    except Exception as e:
        print(f"🚨 최상위 에러: {e}")
        kospi_list = []
        groups = []

    # 💡 [날짜 완벽 복원 + 요일 생성]
    last_update_str = "미정"
    try:
        sam_data = get_ilbong_data('005930')
        if sam_data:
            last_day = sam_data[-1]
            raw_date = str(last_day.get('date', '')).strip()
            
            dt_obj = None
            # 1. 20260517 형태 파싱
            if len(raw_date) == 8 and raw_date.isdigit():
                last_update_str = f"{int(raw_date[4:6])}/{int(raw_date[6:8])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y%m%d')
                except: pass
            # 2. 2026-05-17 형태 파싱
            elif "-" in raw_date and len(raw_date.split("-")) == 3:
                parts = raw_date.split("-")
                last_update_str = f"{int(parts[1])}/{int(parts[2])}"
                try: dt_obj = datetime.strptime(raw_date, '%Y-%m-%d')
                except: pass
            else:
                last_update_str = raw_date

            # 3. 요일 추출 후 결합
            if dt_obj:
                weeks = ['월', '화', '수', '목', '금', '토', '일']
                weekday_str = weeks[dt_obj.weekday()]
                last_update_str = f"{last_update_str} ({weekday_str})"
    except Exception as e:
        last_update_str = "확인불가"

    return render(request, '_partial_kospi.html', {
        'kospi': kospi_list,
        'groups': groups,
        'current_group_id': group_id,
        'last_update': last_update_str
    })












def partial_detail_view(request):
    """비동기 클릭 시 호출되는 상세 뷰에서도 NaN 유입 차단"""
    code = request.GET.get('code')
    check_web = request.GET.get('check_web')

    if check_web == 'true':
        ilbong_data = get_ilbong(access_token=get_token(), shcode=code)
    else:
        ilbong_data = get_ilbong_db(shcode=code)

    if ilbong_data:
        ilbong_data = ilbong_data[::-1]

    # ⭐️ 비동기 상세 페이지 갱신 시에도 NaN 안심 세척 가동
    clean_ilbong = []
    if ilbong_data:
        for day in ilbong_data:
            if isinstance(day, dict):
                cleaned_day = {}
                for k, v in day.items():
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        cleaned_day[k] = None
                    else:
                        cleaned_day[k] = v
                clean_ilbong.append(cleaned_day)
            else:
                clean_ilbong.append(day)
    
    basic_data = select_tb_kospi(code)
    
    # ⭐️ [자로 잰 듯한 수정] db.py 규격에 맞춰 인자 없이 호출하여 바인딩 오류를 해결합니다.
    db_settings = select_check_setting()

    return render(request, '_partial_detail.html', {
        'code': code,
        'json_basic': json.dumps(basic_data),
        'json_ilbong': json.dumps(clean_ilbong),
        'db_settings': db_settings  # ⭐️ 프론트엔드 자바스크립트로 세팅값 주입
    })









def partial_chart_view(request):
    code = request.GET.get('code')
    check_web = request.GET.get('check_web')

    if check_web == 'true':
        ilbong_data = get_ilbong(access_token=get_token(), shcode=code)
    else:
        ilbong_data = get_ilbong_db(shcode=code)

    if ilbong_data:
        ilbong_data = ilbong_data[::-1]

    # ⭐️ 비동기 상세 페이지 갱신 시에도 NaN 안심 세척 가동
    clean_ilbong = []
    if ilbong_data:
        for day in ilbong_data:
            if isinstance(day, dict):
                cleaned_day = {}
                for k, v in day.items():
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        cleaned_day[k] = None
                    else:
                        cleaned_day[k] = v
                clean_ilbong.append(cleaned_day)
            else:
                clean_ilbong.append(day)
    
    kospi_info = select_tb_kospi(code)
    stock_name = ''
    if kospi_info and len(kospi_info) > 0:
        if len(kospi_info[0]) > 1:
            stock_name = kospi_info[0][1]  # 예: "삼성전자"
    
    db_settings = select_check_setting()

    return render(request, '_partial_chart.html', {
        'code': code,
        'name': stock_name,          # ⭐️ 프론트엔드로는 name이라는 이름으로 깔끔하게 주입!
        'json_ilbong': json.dumps(clean_ilbong),
        'db_settings': db_settings  # ⭐️ 프론트엔드 자바스크립트로 세팅값 주입
    })









def partial_hoga_view(request, shcode):
    try:
        api_data = fetch_hoga_api(shcode)
        if api_data:
            upsert_hoga(shcode, api_data)
    except Exception as e:
        print(f"⚠️ API 호출 실패: {e}")
    
    hoga_data = select_hoga(shcode) or {}
    
    # 1. 시각화를 위한 최대 잔량(max_rem) 계산
    all_rems = []
    for i in range(1, 11):
        all_rems.append(int(hoga_data.get(f'offer_rem{i}', 0)))
        all_rems.append(int(hoga_data.get(f'bid_rem{i}', 0)))
    
    max_rem = max(all_rems) if all_rems else 1
    # print(hoga_data)

    # print(max_rem)
    
    return render(request, '_partial_hoga.html', {
        'hoga': hoga_data,
        'max_rem': max_rem  # 막대그래프 비율 계산용
    })











def st_hoga_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_hoga.html', {
        'mode': mode,
        'strategy_title': '🚀 호가틱 전략',
        'strategy_button_html': '''
            <button class="btn" onclick="startHogaWindow('/hoga_stream/')" style="padding:8px 16px;background:#2563eb;color:white;cursor:pointer;">
                📊 호가틱 수집
            </button>
        ''',
        'st_id': 'st_hoga',

    })


def st_hoga_data_view(request):
    mode = request.GET.get('mode', 'buy')
    
    list_data = select_st_hoga(mode)

    # print(list_hoga)
    
    return JsonResponse({ 'list_data': json.loads(json.dumps(list_data, default=str)) })

















def st_macd_view(request):
    mode = request.GET.get('mode', 'buy')
    return render(request, 'strategy/st_macd.html', {
        'mode': mode,
        'strategy_title': '🚀 MACD 전략',
        'st_id': 'st_macd',
    })

def st_macd_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes', None)
    
    # 1. 초기 종목 리스트만 요청할 때
    if not codes:
        data = select_st_macd(mode)
        # 종목 리스트만 객체로 감싸서 전달
        return JsonResponse({'list_data': data}) 
    
    # 2. 특정 종목 코드들(50개씩)의 상세 일봉 데이터 요청할 때
    else:
        code_list = codes.split(',')
        # DB에서 데이터 조회
        data = select_st_macd_ilbong(code_list)
        # 딕셔너리 형태로 그대로 전달 (클라이언트에서 json_ilbong에 병합)
        return JsonResponse(data)












def st_rsi_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_rsi.html', {
        'mode': mode,
        'strategy_title': '🚀 RSI 전략',
        'st_id': 'st_rsi',

    })


def st_rsi_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes', None)

    if not codes:
        data = select_st_rsi(mode)
        return JsonResponse({'list_data': data})

    code_list = codes.split(',')

    data = select_st_rsi_ilbong(code_list)

    return JsonResponse(data)







def st_bol_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_bol.html', {
        'mode': mode,
        'strategy_title': '🚀 볼린저 밴드 전략',
        'st_id': 'st_bol',        
    })


def st_bol_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes', None)

    if not codes:
        data = select_st_bol(mode)
        return JsonResponse({'list_data': data})

    code_list = codes.split(',')

    data = select_st_bol_ilbong(code_list)

    return JsonResponse(data)






def st_ilmok_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_ilmok.html', {
        'mode': mode,
        'strategy_title': '🚀 일목균형표 전략',
        'st_id': 'st_ilmok',        
    })


def st_ilmok_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes', None)

    if not codes:
        data = select_st_ilmok(mode)
        return JsonResponse({'list_data': data})

    code_list = codes.split(',')

    data = select_st_ilmok_ilbong(code_list)

    # print(data[next(iter(data))])

    return JsonResponse(data)







def st_vol_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_vol.html', {
        'mode': mode,
        'strategy_title': '🚀 거래량 전략',
        'st_id': 'st_vol',        
    })


def st_vol_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_vol(mode)
        return JsonResponse({'list_data': data})

    data = select_st_vol_ilbong(codes.split(','))

    return JsonResponse(data)









def st_ma5_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_ma5.html', {
        'mode': mode,
        'strategy_title': '📈 MA5 전략',
        'st_id': 'st_ma5',        
    })


def st_ma5_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_ma5(mode)
        return JsonResponse({'list_data': data})

    data = select_st_ma5_ilbong(codes.split(','))

    return JsonResponse(data)










def st_ma20_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_ma20.html', {
        'mode': mode,
        'strategy_title': '📈 MA20 전략',
        'st_id': 'st_ma20',
    })


def st_ma20_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_ma20(mode)
        return JsonResponse({'list_data': data})

    data = select_st_ma20_ilbong(codes.split(','))

    return JsonResponse(data)







def st_sales_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_sales.html', {
        'mode': mode,
        'strategy_title': '📊 매출/영업이익 전략',
        'st_id': 'st_sales',        
    })


def st_sales_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_sales(mode)
        return JsonResponse({'list_data': data})

    data = select_st_sales_fin(codes.split(','))

    return JsonResponse(data)








def st_salesqoq_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_salesqoq.html', {
        'mode': mode,
        'strategy_title': '📈 매출/영업이익 성장률 전략',
        'st_id': 'st_salesqoq',        
    })


def st_salesqoq_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_salesqoq(mode)
        return JsonResponse({'list_data': data})

    data = select_st_salesqoq_fin(codes.split(','))

    return JsonResponse(data)











def st_asset_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_asset.html', {
        'mode': mode,
        'strategy_title': '🏦 자산/부채 전략',
        'st_id': 'st_asset',
    })


def st_asset_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_asset(mode)
        return JsonResponse({'list_data': data})

    data = select_st_asset_fin(codes.split(','))

    return JsonResponse(data)





def st_cf_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_cf.html', {
        'mode': mode,
        'strategy_title': '💰 현금흐름 전략',
        'st_id': 'st_cf',        
    })


def st_cf_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_cf(mode)
        return JsonResponse({'list_data': data})

    data = select_st_cf_fin(codes.split(','))

    return JsonResponse(data)





def st_eps_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_eps.html', {
        'mode': mode,
        'strategy_title': '📈 EPS 전략',
        'st_id': 'st_eps',        
    })


def st_eps_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_eps(mode)
        return JsonResponse({'list_data': data})

    data = select_st_eps_fin(codes.split(','))

    return JsonResponse(data)







def st_epsqoq_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_epsqoq.html', {
        'mode': mode,
        'strategy_title': '📈 EPS 성장률 전략',
        'st_id': 'st_epsqoq',
    })


def st_epsqoq_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_epsqoq(mode)
        return JsonResponse({'list_data': data})

    data = select_st_epsqoq_fin(codes.split(','))

    return JsonResponse(data)





def st_margin_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_margin.html', {
        'mode': mode,
        'strategy_title': '📈 영업이익률 전략',
        'st_id': 'st_margin',        
    })


def st_margin_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_margin(mode)
        return JsonResponse({'list_data': data})

    data = select_st_margin_fin(codes.split(','))

    return JsonResponse(data)








def st_roe_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_roe.html', {
        'mode': mode,
        'strategy_title': '📈 ROE 전략',
        'st_id': 'st_roe',        
    })


def st_roe_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_roe(mode)
        return JsonResponse({'list_data': data})

    data = select_st_roe_fin(codes.split(','))

    return JsonResponse(data)






def st_dept_view(request):
    mode = request.GET.get('mode', 'buy')

    return render(request, 'strategy/st_dept.html', {
        'mode': mode,
        'strategy_title': '📉 부채비율 전략',
        'st_id': 'st_dept',
    })


def st_dept_data_view(request):
    mode = request.GET.get('mode', 'buy')
    codes = request.GET.get('codes')

    if not codes:
        data = select_st_dept(mode)
        return JsonResponse({'list_data': data})

    data = select_st_dept_fin(codes.split(','))

    return JsonResponse(data)








@require_GET
def api_ilbong_chart_st(request):

    stock_code = request.GET.get('code', '').strip()

    if not stock_code:
        return JsonResponse({'error': '종목코드가 누락되었습니다.'}, status=400)

    list_ilbong = select_tb_ilbong(stock_code)
    df_fin = select_naver_fin(stock_code)


    fin = {}

    if not df_fin.empty:

        q_data = df_fin[
            (df_fin['구분'] == '분기') &
            (~df_fin['기간'].astype(str).str.contains(r'\(E\)', na=False))
            ]

        fin_row = q_data.iloc[-1]

        fin = {
            '업종': fin_row.get('업종', ''),
            '시가총액': fin_row.get('시가총액', 0),
            'EPS': fin_row.get('EPS', 0),
            'PER': fin_row.get('PER', 0),
            'PBR': fin_row.get('PBR', 0),
            '배당': fin_row.get('배당', 0),
            '부채비율3': q_data.tail(3)['부채비율'].round(1).fillna(0).tolist(),
            'RSI': round(day_rsi, 1) if (day_rsi := list_ilbong[-1].get('rsi14')) is not None else 0
        }


    chart_result_list = []

    for day in list_ilbong:

        raw_date = str(day.get('date', '')).strip()

        if len(raw_date) == 8 and raw_date.isdigit():
            formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        else:
            formatted_date = raw_date

        chart_result_list.append({

            'time': formatted_date,

            'open': day.get('open', 0),
            'high': day.get('high', 0),
            'low': day.get('low', 0),
            'close': day.get('close', 0),

            'volume': day.get('volume', 0),

            'ma5': day.get('ma5'),
            'ma20': day.get('ma20'),
            'ma60': day.get('ma60'),
            'ma120': day.get('ma120'),

            'macd': day.get('macd'),
            'macd9': day.get('macd9'),

            '개인': day.get('개인'),
            '외국인': day.get('외국인'),
            '기관': day.get('기관')
        })




    df = select_naver_fin(stock_code)
    data = df.to_dict(orient='records')


    return JsonResponse({
        'chart': chart_result_list,
        'fin': fin,
        'data': data
    })
















def hoga_stream_view(request):
    log_queue = queue.Queue()

    # 로그를 큐에 넣는 함수
    def logger(msg):
        log_queue.put(msg)

    # 수집 로직을 별도 스레드에서 실행
    threading.Thread(target=save_hoga, args=(logger,)).start()

    # 클라이언트로 데이터 스트리밍
    def event_stream():
        while True:
            msg = log_queue.get()
            yield f"data: {msg}\n\n"
            # 완료 메시지가 나오면 루프 종료
            if "모든 수집 및 저장 완료" in msg:
                break

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream; charset=utf-8')


from api.hoga import stop_event

@csrf_exempt
def stop_hoga_view(request):
    if request.method == 'POST':
        stop_event.set() # '멈춰!' 신호 전송
        return JsonResponse({"message": "중지 신호 전달됨"})







def strategy_view(request):
    return render(request, 'strategy/strategy.html')









@csrf_exempt
def add_st_gwansim_group_view(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_name = data.get('group_name', '').strip()
            codes = data.get('codes', [])
            
            if not group_name or not codes:
                return JsonResponse({'status': 'fail', 'message': '누락'}, status=400)
            
            # 1. db.py에 있는 그룹 생성 함수 호출
            insert_tb_gwansim_group(group_name)
            
            # 2. 고유 ID 재조회
            with duckdb.connect(db_path) as conn:
                res = conn.execute("SELECT group_id FROM tb_gwansim_group WHERE group_name = ?", [group_name]).fetchone()
                if not res:
                    return JsonResponse({'status': 'fail', 'message': 'ID조회실패'}, status=500)
                group_id = res[0]
            
            # 3. 종목 삽입 함수 호출 (🎯 오타 완벽 수정 완료)
            success_count = 0
            for shcode in codes:
                # insert_tb_gwansim_stock으로 오차 없이 명확하게 직통 매핑 호출!
                inserted = insert_tb_gwansim_stock(group_id, shcode)
                if inserted:
                    success_count += 1
            
            return JsonResponse({'status': 'success', 'message': f'{success_count}개 성공'})
        except Exception as e:
            print(f"❌ [최종 에러 로그]: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'fail'}, status=405)









@csrf_exempt
def add_naver_fin_view(request):
    """
    POST로 요청이 오면 전 종목 수집/저장 프로세스를 시작하고,
    그 과정을 실시간 로그로 스트리밍합니다.
    """
    def event_stream():
        # 1. 전 종목 리스트 가져오기
        stock_list = select_tb_kospi_name() # [ (코드, 종목명), ... ]
        total = len(stock_list)
        
        yield f"🚀 총 {total}개 종목 수집 및 DB 저장 시작...\n"
        
        for idx, (code, name) in enumerate(stock_list):
            try:
                # 2. 수집 및 DB 저장 실행 (이미 만들어둔 로직 재사용)
                set_naver_fin(code)
                
                # 3. 실시간 로그 전송
                yield f"[{idx+1}/{total}] ✅ [{code}] {name} 저장 완료\n"
                
                # 4. 부하 방지용 딜레이
                time.sleep(0.5)
            except Exception as e:
                yield f"[{idx+1}/{total}] ❌ [{code}] {name} 에러: {str(e)}\n"
        
        yield "🏁 전체 작업 완료!"

    # 스트리밍 응답 반환
    return StreamingHttpResponse(event_stream(), content_type='text/plain')

def get_naver_fin_view(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': '종목 코드가 없습니다.'}, status=400)
    
    # 아까 작성하신 재무 조회 함수 호출
    df = select_naver_fin(code)
    
    # DataFrame을 JSON 리스트 형태로 변환
    data = df.to_dict(orient='records')

    # print(data)
    return JsonResponse({'data': data}, safe=False)




















def fin_view(request):

    code = request.GET.get('code', '005930')
    name = request.GET.get('name', '삼성전자')
    
    raw_groups = select_tb_gwansim_group()
    groups_data = []

    for g in raw_groups:
        gid = g[0]
        gname = g[1]
        raw_stocks = select_tb_gwansim_stock(gid)

        stocks_list = []
        for s in raw_stocks:
            try:
                price_val = str(s[2]).replace(',', '') if s[2] else "0"
                formatted_price = format(int(price_val), ',')
            except:
                formatted_price = s[2]

            stocks_list.append({
                'shcode': s[0],
                'hname': s[1],
                'price': formatted_price,
                'rate': s[3],
                'rsi': s[5],
                'cap': s[4],
            })

        groups_data.append({
            'id': gid,
            'name': gname,
            'stocks': stocks_list,
            'count': len(stocks_list)
        })

    raw_kospi = select_tb_kospi()
    kospi = [{'code': s[0], 'name': s[1], 'cap': s[4]} for s in raw_kospi]

    return render(request, 'fin.html', {
        'groups': groups_data,
        'kospi': kospi,
        'init_code': code,
        'init_name': name,
    })


# ========================================================
# ★ 새롭게 추가하는 일봉 차트 데이터 전달 비동기 API 뷰
# ========================================================
from django.views.decorators.http import require_GET

@require_GET
def api_ilbong_chart(request):
    """
    특정 종목의 일봉(OHLCV) 데이터를 JSON으로 반환하는 API
    """
    try:
        stock_code = request.GET.get('code', '').strip()
        
        if not stock_code:
            return JsonResponse({'error': '종목코드가 누락되었습니다.'}, status=400)
            
        # 1. DB에서 데이터 가져오기 (유저님의 기존 함수 호출)
        list_ilbong = get_ilbong_db(stock_code)
        
        if list_ilbong:
            list_ilbong = list_ilbong[::-1]  # 과거 -> 현재 순서로 뒤집기
        else:
            list_ilbong = []

        # ★ 최종 결과를 담을 '리스트' 변수명을 명확하게 지정
        chart_result_list = []  
        
        for day in list_ilbong:
            raw_date = day.get('date')
            if not raw_date:
                continue
                
            raw_date = str(raw_date).strip()
            
            # 'YYYYMMDD' -> 'YYYY-MM-DD' 포맷팅
            if len(raw_date) == 8 and raw_date.isdigit():
                formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            elif "-" in raw_date and len(raw_date.split("-")) == 3:
                formatted_date = raw_date
            else:
                continue # 규격 외 불량 날짜 스킵
                
            try:
                # 쉼표(,) 제거 및 부동소수점 변환
                o = float(str(day.get('open', 0)).replace(',', ''))
                h = float(str(day.get('high', 0)).replace(',', ''))
                l = float(str(day.get('low', 0)).replace(',', ''))
                c = float(str(day.get('close', 0)).replace(',', ''))
                v = float(str(day.get('volume', 0)).replace(',', ''))
                
                # 시가나 종가가 0인 데이터(거래정지 등) 예외처리
                if o == 0 or c == 0:
                    continue

                # ★ 개별 날짜 데이터를 담을 '딕셔너리' 변수 분리
                day_data = {
                    'time': formatted_date,
                    'open': o,
                    'high': h,
                    'low': l,
                    'close': c,
                    'volume': v
                }
                
                # 리스트에 정제된 딕셔너리 삽입
                chart_result_list.append(day_data)
                
            except Exception:
                continue

        # 2. 확실하게 날짜 오름차순(과거->현재) 정렬 보장 (.sort 정상 작동)
        chart_result_list.sort(key=lambda x: x['time'])

        # 3. 정상 JSON 리스트 반환
        return JsonResponse(chart_result_list, safe=False)

    except Exception as e:
        # 시스템 내부에서 예기치 못한 에러 발생 시 HTML 대신 JSON 에러 반환 (자바스크립트 오작동 방지)
        return JsonResponse({'error': f'서버 내부 오류: {str(e)}'}, status=500)






def get_ilbong_view(request):
    code = request.GET.get('code')
    list_ilbong = select_tb_ilbong(code)
    
    return JsonResponse({'list_ilbong': list_ilbong}, safe=False)








def get_ilbong_main_view(request):
    code = request.GET.get('code')

    list_ilbong = select_tb_ilbong(code)

    d = datetime.strptime(str(list_ilbong[-1]['date']), '%Y%m%d')
    base_date = f'{d.month}.{d.day}.({"월화수목금토일"[d.weekday()]}) 기준'

    list_fin = select_naver_fin(code).to_dict(orient='records')

    return JsonResponse({
        'list_ilbong': list_ilbong,
        'base_date': base_date,
        'list_fin': list_fin,
    })


























def get_ilbong_view(request):
    code = request.GET.get('code')
    
    # 1. 일봉 데이터
    list_ilbong = select_tb_ilbong(code)
    
    # 2. 최신일 계산
    d = datetime.strptime(str(list_ilbong[-1]['date']), '%Y%m%d')
    base_date = f'{d.month}.{d.day}.({"월화수목금토일"[d.weekday()]}) 기준'
    
    # 3. 재무 데이터
    df_fin = select_naver_fin(code)
    list_financial = df_fin.to_dict(orient='records')

    # 4. 필요하면 분기별 데이터도 추가 가능
    # list_quarter = select_quarter_data(code).to_dict(orient='records')
    
    return JsonResponse({
        'list_ilbong': list_ilbong,
        'base_date': base_date,
        'list_financial': list_financial,
        # 'list_quarter': list_quarter
    }, safe=False)













def golden_view(request):
    return render(request, "golden.html")


@require_POST
def golden_api_view(request):

    data = json.loads(request.body)
    sql = data.get("sql", "").strip()

    result = select_golden(sql)

    return JsonResponse(result)









def select_checkbox_view(request):

    data = select_tb_checkbox()
    return JsonResponse(data)



@csrf_exempt
def update_checkbox_view(request):

    if request.method != 'POST':
        return JsonResponse({'result': 'fail'})

    body = json.loads(request.body)

    checkbox_id = body.get('checkbox_id')
    checked = body.get('checked')

    update_tb_checkbox(checkbox_id, checked)

    return JsonResponse({'result': 'ok'})












def account_view(request):
    # 나중에 여기서 DB에 저장된 내 계좌/보유종목 데이터를 가져올 겁니다.
    access_token=get_token()
    account_number = get_account_number(access_token)
    balance = get_balance(access_token, account_number)
    # print(balance)
    # print(type(balance))
    return render(request, 'account.html', {'balance': balance})






















