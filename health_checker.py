import requests
import csv
import datetime
from typing import List

def health_check_url(url: str) -> dict:
    """
    지정한 URL에 HTTP GET 요청을 보내고 Health Check 결과를 반환

    Args:
        url: 체크할 URL

    Returns:
        dict: timestamp, url, status_code, result를 포함한 딕셔너리
    """
    # 장애 안내 키워드
    failure_keywords = ["시스템 점검", "화재", "서비스 중단", "불편을 드려 죄송"]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    try:
        # HTTP GET 요청 (타임아웃 10초)
        response = requests.get(url, timeout=10)
        status_code = response.status_code

        if status_code == 200:
            # 응답 본문에서 장애 키워드 확인
            content = response.text.lower()
            has_failure_keyword = any(keyword in content for keyword in failure_keywords)

            if has_failure_keyword:
                result = "Unhealthy"
            else:
                result = "Healthy"
        else:
            result = "Error"

    except (requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException) as e:
        status_code = "N/A"
        result = "Error"
        print(f"요청 실패 ({url}): {e}")

    return {
        "timestamp": timestamp,
        "url": url,
        "status_code": status_code,
        "result": result
    }

def check_multiple_urls(urls: List[str], csv_filename: str = "health_check_results.csv"):
    """
    여러 URL을 순차적으로 검사하고 결과를 CSV 파일로 저장

    Args:
        urls: 검사할 URL 리스트
        csv_filename: 저장할 CSV 파일명
    """
    results = []

    # 각 URL을 순차적으로 검사
    for url in urls:
        print(f"검사 중: {url}")
        result = health_check_url(url)
        results.append(result)
        print(f"결과: {result['result']} (상태코드: {result['status_code']})")

    # CSV 파일로 결과 저장
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'url', 'status_code', 'result']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # 헤더 쓰기
        writer.writeheader()

        # 데이터 쓰기
        for result in results:
            writer.writerow(result)

    print(f"\n결과가 {csv_filename} 파일로 저장되었습니다.")
    return results

# 사용 예시
if __name__ == "__main__":
    # 테스트할 URL 리스트
    test_urls = [
        "https://www.google.com",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/500",
        "https://httpbin.org/delay/15",  # 타임아웃 테스트
    ]

    # 여러 URL 검사 실행
    check_multiple_urls(test_urls)

    # 단일 URL 검사 예시
    print("\n=== 단일 URL 검사 예시 ===")
    single_result = health_check_url("https://www.example.com")
    print(f"결과: {single_result}")