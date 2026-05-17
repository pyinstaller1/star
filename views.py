from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from api.start_kospi import set_kospi, set_kospi_1day
from api.ilbong import *
from api.db import *

from django.db import connection, transaction
from django.http import HttpResponse

import json
import requests

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



















def gwansim_view(request):
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
    
    return render(request, 'gwansim.html', {
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
            group_name = data.get('name')

            if not group_name:
                return JsonResponse({'success': False, 'message': '그룹명을 입력하세요.'})

            insert_tb_gwansim_group(group_name)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})



def select_tb_gwansim_group():
    """데이터베이스에서 관심그룹 목록을 순서대로 조회"""
    try:
        with duckdb.connect(db_path) as conn:
            return conn.execute("""
                SELECT group_id, group_name 
                FROM tb_gwansim_group 
                ORDER BY order_no ASC
            """).fetchall()
    except Exception as e:
        print(f"그룹 조회 중 오류 발생: {e}")
        return []

def select_tb_gwansim_stock(group_id):
    """특정 그룹에 속한 종목들을 tb_kospi와 조인하여 기존 코스피 행 구조와 100% 일치하게 반환"""
    con = duckdb.connect(db_path)
    
    # ⭐️ 기존 select_tb_kospi()가 넘겨주던 데이터 구조(행 인덱스)를 그대로 맞추기 위해
    # tb_kospi의 모든 컬럼(A.*)을 order_no 순서대로 정렬해서 긁어옵니다.
    sql = """
        SELECT A.*
        FROM tb_gwansim_stock B
        LEFT JOIN tb_kospi A ON B.shcode = A."코드"
        WHERE B.group_id = ?
        ORDER BY B.order_no ASC
    """
    try:
        res = con.execute(sql, [int(group_id)]).fetchall()
    except Exception as e:
        print(f"관심종목 조회 중 오류 발생: {e}")
        res = []
    finally:
        con.close()
    return res


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

    # 기본 요약 정보 추출
    basic_raw = select_tb_kospi(initial_code)
    
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

    # JSON 호환용 null 변환 스트링 마감
    json_ilbong = json.dumps(clean_ilbong)
    json_basic = json.dumps(basic_raw)
    
    # ⭐️ 첫 화면 진입 시에도 상단 메뉴 탭 리스트를 무조건 렌더링하도록 DB에서 조회
    groups_data = select_tb_gwansim_group()
    
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
    
    return render(request, 'index.html', {
        'kospi': list_kospi_formatted,
        'code': initial_code,
        'json_ilbong': json_ilbong,
        'json_basic': json_basic,
        'groups': groups_data, 
        'last_update': last_update_str  
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
    
    return render(request, '_partial_detail.html', {
        'code': code,
        'json_basic': json.dumps(basic_data),
        'json_ilbong': json.dumps(clean_ilbong)
    })



















def account_view(request):
    # 나중에 여기서 DB에 저장된 내 계좌/보유종목 데이터를 가져올 겁니다.
    access_token=get_token()
    account_number = get_account_number(access_token)
    balance = get_balance(access_token, account_number)
    print(balance)
    print(type(balance))
    return render(request, 'account.html', {'balance': balance})


