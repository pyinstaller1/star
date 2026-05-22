import sys

class CompanyEvaluator:
    """
    재무제표 데이터를 기반으로 기업의 투자 등급을 평가하는 클래스
    """
    def __init__(self, company_name, year, quarter_code, finance_data):
        self.company_name = company_name
        self.year = year
        self.quarter_code = quarter_code
        
        # 재무 데이터 매핑
        self.asset = finance_data.get('자산총계', 0)
        self.equity = finance_data.get('자본총계', 0)
        self.debt = finance_data.get('부채총계', 0)
        self.revenue = finance_data.get('매출액', 0)
        self.cf_operating = finance_data.get('영업활동 현금흐름', 0)
        self.cf_investing = finance_data.get('투자활동 현금흐름', 0)
        self.cf_financing = finance_data.get('재무활동 현금흐름', 0)

    def calculate_rating(self):
        score = 0
        max_score = 100
        diagnoses = []

        # 예외 처리: 데이터가 비어있거나 자본이 0 이하인 경우 (자본잠식 등)
        if self.equity <= 0 or self.asset <= 0:
            return {
                "score": 0,
                "grade": 5,
                "diagnoses": ["데이터 부족 또는 자본잠식 상태로 평가 불가"],
                "debt_ratio": 0.0
            }

        # -----------------------------------------------------------------
        # 1. 안정성 평가: 부채비율 (부채총계 / 자본총계) -> 배점 30점
        # -----------------------------------------------------------------
        debt_ratio = (self.debt / self.equity) * 100
        if debt_ratio <= 50:
            score += 30
            diagnoses.append(f"부채비율({debt_ratio:.1f}%) 극히 낮음 (최상위 재무 안정성)")
        elif debt_ratio <= 100:
            score += 25
            diagnoses.append(f"부채비율({debt_ratio:.1f}%) 안정적 수준 유지")
        elif debt_ratio <= 200:
            score += 15
            diagnoses.append(f"부채비율({debt_ratio:.1f}%) 보통 (적정 수준의 레버리지)")
        else:
            diagnoses.append(f"부채비율({debt_ratio:.1f}%) 과도함 (재무 리스크 관리 필요)")

        # -----------------------------------------------------------------
        # 2. 외형 및 효율성 평가: 자산 회전율 (매출액 / 자산총계) -> 배점 30점
        # -----------------------------------------------------------------
        asset_turnover = self.revenue / self.asset
        if asset_turnover >= 0.6:
            score += 30
            diagnoses.append("자산 규모 대비 매출 발생 효율 우수 (활발한 영업 활동)")
        elif asset_turnover >= 0.3:
            score += 20
            diagnoses.append("자산 규모 대비 매출 발생 효율 보통")
        else:
            score += 10
            diagnoses.append("자산 규모 대비 매출 발생 저조 (자산 활용도 개선 필요)")

        # -----------------------------------------------------------------
        # 3. 현금흐름 3대 지표 패턴 평가 -> 배점 40점
        # -----------------------------------------------------------------
        # 패턴 A: 우량 기업 (영업 +, 투자 -, 재무 -) -> 대기업 정석
        if self.cf_operating > 0 and self.cf_investing < 0 and self.cf_financing < 0:
            score += 40
            diagnoses.append("현금흐름 패턴 최우량 (영업수익으로 투자 실행 및 부채 상환/배당)")
        
        # 패턴 B: 성장 기업 (영업 +, 투자 -, 재무 +) -> 외부 조달해 공격적 투자
        elif self.cf_operating > 0 and self.cf_investing < 0 and self.cf_financing > 0:
            score += 35
            diagnoses.append("현금흐름 패턴 성장형 (영업 활동 양호 및 외부 자금 조달을 통한 대규모 투자)")
            
        # 패턴 C: 정체 또는 구조조정 (영업 +, 투자 +, 재무 -) -> 자산 매각 중
        elif self.cf_operating > 0 and self.cf_investing > 0:
            score += 20
            diagnoses.append("영업 흑자이나 투자 자산 처분으로 현금 유입 (사업 축소 또는 현금 확보 중)")
            
        # 패턴 D: 턴어라운드 혹은 위험 (영업 -, 투자 -, 재무 +) -> 번 돈 없고 빚내서 버팀
        elif self.cf_operating < 0 and self.cf_financing > 0:
            score += 5
            diagnoses.append("영업활동 적자 상태에서 외부 차입/증자로 연명 중 (투자 유의)")
            
        else:
            diagnoses.append("현금흐름 변동성 높음 (세부 흐름 분석 필요)")

        # -----------------------------------------------------------------
        # 최종 등급 산정 (1등급 ~ 5등급)
        # -----------------------------------------------------------------
        if score >= 90:
            grade = 1
        elif score >= 70:
            grade = 2
        elif score >= 50:
            grade = 3
        elif score >= 30:
            grade = 4
        else:
            grade = 5

        return {
            "score": score,
            "grade": grade,
            "diagnoses": diagnoses,
            "debt_ratio": debt_ratio
        }


def print_evaluation_report(company_name, year, quarter_code, result):
    """
    평가 결과를 양식에 맞춰 출력하는 함수
    """
    grade_desc = {
        1: "1 등급 (최우량 투자 기업)",
        2: "2 등급 (우량 투자 기업)",
        3: "3 등급 (보통 기업 - 현상 유지)",
        4: "4 등급 (투자 유의 기업)",
        5: "5 등급 (위험 기업)"
    }
    
    print("\n" + "=" * 65)
    print(f"★ {year}년 {quarter_code} 분기 흐름 기반 종합 기업 등급 ★")
    print("=" * 65)
    print(f"■ 대상 기업 명칭   : {company_name}")
    print(f"■ 최종 기업 투자 등급 : {grade_desc[result['grade']]}")
    print(f"■ 재무 종합 점수   : {result['score']} 점 / 100 점 만점")
    print(f"■ 주요 부채 비율   : {result['debt_ratio']:.2f}%")
    print("-" * 65)
    print("▶ 종합 진단:")
    for txt in result['diagnoses']:
        print(f"   - {txt}")
    print("=" * 65 + "\n")


# ==========================================
# 메인 실행부 (실제 시스템 연동 예시)
# ==========================================
if __name__ == "__main__":
    
    # 1. API 또는 DB에서 수집된 로우 데이터 정의 (샘플: 삼성전자 2025년 11011 분기)
    # 유동/비유동 자산·부채는 제외하고 요청하신 핵심 항목만 구성
    raw_data = {
        '자산총계': 566942110000000,
        '자본총계': 436320337000000,
        '부채총계': 130621773000000,
        '매출액': 333605938000000,
        '재무활동 현금흐름': -13478040000000,
        '투자활동 현금흐름': -68512206000000,
        '영업활동 현금흐름': 85315148000000
    }
    
    # 데이터 로깅 디버그 메시지 (기존 콘솔 출력 스타일 유지)
    print("삼성전자     | 2025 | 11011 | 자산총계                | 566,942,110,000,000")
    print("삼성전자     | 2025 | 11011 | 자본총계                | 436,320,337,000,000")
    print("삼성전자     | 2025 | 11011 | 부채총계                | 130,621,773,000,000")
    print("삼성전자     | 2025 | 11011 | 매출액                 | 333,605,938,000,000")
    print("삼성전자     | 2025 | 11011 | 재무활동 현금흐름          | -13,478,040,000,000")
    print("삼성전자     | 2025 | 11011 | 투자활동 현금흐름          | -68,512,206,000,000")
    print("삼성전자     | 2025 | 11011 | 영업활동 현금흐름          |  85,315,148,000,000")
    print("-" * 85)
    print("DEBUG: 요청 완료. 재무 비율 및 현금흐름 패턴 기반 스코어링 시작...")

    # 2. 등급 평가 객체 생성 및 계산
    evaluator = CompanyEvaluator(
        company_name="삼성전자", 
        year=2025, 
        quarter_code="11011", 
        finance_data=raw_data
    )
    
    evaluation_result = evaluator.calculate_rating()
    
    # 3. 리포트 결과 출력
    print_evaluation_report("삼성전자", 2025, "11011", evaluation_result)