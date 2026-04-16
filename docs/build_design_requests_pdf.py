"""설계 과정에서 요청한 사항을 상황별로 정리해 PDF 로 출력한다."""
from __future__ import annotations

from pathlib import Path
from fpdf import FPDF

OUT = Path(__file__).parent / "design-requests.pdf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"

TITLE = "슈퍼센트 파트너 크리에이터 평가 도구"
SUBTITLE = "설계·개선 과정 요청 기록"
INTRO = (
    "본 문서는 프로젝트 기획 단계부터 최근 개선까지, 제가 요청했던 사항을 "
    "원문 그대로가 아니라 '어떤 상황에서 어떤 요청을 했는지' 관점으로 정리한 기록입니다. "
    "시간 순서대로 나열되어 있으며, 각 블록은 [상황] → [요청] → [결과] 구조로 읽으시면 됩니다."
)

SECTIONS: list[dict] = [
    {
        "idx": "1",
        "title": "프로젝트 초기 기획",
        "situation": (
            "슈퍼센트 마케팅팀은 YouTube 파트너 크리에이터를 1명당 20~30분씩 수작업으로 평가하고 있었고, "
            "월 50명 이상의 지원자가 있을 때 주당 10시간 이상이 소요되었다. "
            "평가자마다 기준이 달라 일관성이 떨어졌고, 수백 개의 댓글을 사람이 읽어 감성을 요약하는 것은 "
            "사실상 불가능한 상태였다."
        ),
        "requests": [
            "YouTube 채널 URL을 넣으면 채널/영상/댓글 데이터를 자동 수집하도록 만들어달라.",
            "Gemini API로 댓글 감성분석을 수행하고, 핵심 테마와 주목할 댓글을 뽑아달라.",
            "구독자(20%)·참여도(25%)·성장률(20%)·감성(20%)·일관성(15%) 가중 평균으로 종합 점수를 내달라.",
            "종합 60점 이상 & 구독자 500명 이상이면 PASS, 둘 중 하나만 충족이면 REVIEW, 둘 다 미달이면 FAIL로 자동 판정해달라.",
            "결과는 차트가 포함된 웹 대시보드로 보여달라. 스택은 FastAPI + Tailwind CDN + Chart.js + Vanilla JS (빌드 도구 없이).",
            "Gemini 모델은 gemini-2.0-flash로 시작.",
        ],
        "result": "c2e310a Initial commit 으로 기본 파이프라인과 대시보드를 구축.",
    },
    {
        "idx": "2",
        "title": "Railway 배포 환경 준비",
        "situation": (
            "로컬 실행만 되던 프로토타입을 실제 배포 환경(Railway)에 올려야 했다. "
            "재시작 시 SQLite 데이터가 사라지는 문제도 있었다."
        ),
        "requests": [
            "Railway 가 인식할 Procfile 을 추가해달라.",
            "SQLite DB 경로를 DB_PATH 환경변수로 관리해서, Railway 영구 볼륨을 가리킬 수 있게 해달라.",
        ],
        "result": "75544c2, 1a4a410 로 배포 설정과 영구 저장 대응 완료.",
    },
    {
        "idx": "3",
        "title": "관리자 페이지 분리 및 보안 강화",
        "situation": (
            "초기에는 관리자 기능(크리에이터 목록·자동 평가 스케줄)이 별도 보호 없이 노출되어 있었다. "
            "외부 공개 도구에서는 관리자 영역을 반드시 가려야 한다는 이슈가 있었다."
        ),
        "requests": [
            "관리자 콘솔을 추측 가능한 URL(/manage 등) 이 아니라 난독화된 경로(/sc-9f3b2a7c)로 옮겨달라.",
            "해당 경로에 HTTP Basic Auth 를 걸고, ADMIN_USERNAME / ADMIN_PASSWORD 를 환경변수로 받게 해달라.",
            "/api/v1/creators, /api/v1/schedule 같은 관리용 API 에도 동일한 인증을 적용해달라.",
            "메인 페이지(index.html)에 있던 관리자 링크는 제거해달라.",
            "Gemini 가 돌려준 댓글 텍스트도 프론트에서 이스케이프해서 XSS 를 막아달라.",
        ],
        "result": "44a5b57 — auth.py 추가, manage.html 을 backend/templates/admin_console.html 로 이동, 정적 마운트에서 제외.",
    },
    {
        "idx": "4",
        "title": "대량 평가 성능 개선",
        "situation": (
            "등록 크리에이터가 늘어나자 '전체 평가 실행' 이 직렬 처리로 인해 너무 오래 걸렸고, "
            "한 채널 안에서도 댓글 배치들이 순차적으로 Gemini 를 호출해 시간이 쌓였다."
        ),
        "requests": [
            "'전체 평가' 를 5개 워커 풀로 병렬 처리해 동시에 여러 크리에이터가 평가되도록 해달라.",
            "한 채널의 Gemini 댓글 배치들도 ThreadPoolExecutor 로 동시에 돌리고, 워커 수는 GEMINI_BATCH_CONCURRENCY 환경변수로 조절하게 해달라 (기본 3).",
        ],
        "result": "4314be8, c1f3375 — 두 단계 모두 병렬화 적용.",
    },
    {
        "idx": "5",
        "title": "감성 분석 정확도 + 관리자 UI 개선",
        "situation": (
            "배치마다 댓글 수가 달랐는데 긍정/부정/중립 비율을 단순 평균으로 내고 있어 "
            "정확도가 왜곡되고 있었다. 또한 관리자 목록이 한눈에 잘 들어오지 않았고, "
            "크리에이터별 상세 결과를 다시 보는 경로가 없었다."
        ),
        "requests": [
            "긍정/부정/중립 비율을 배치별 실제 댓글 수로 가중 평균을 내도록 수정해달라.",
            "앞서 떼어냈던 관리자 링크를 메인 페이지에 다시 노출해달라 (단, 난독화 경로 그대로).",
            "관리자 페이지의 크리에이터 목록을 3열 정사각형 카드 그리드로 바꾸고, 카드를 누르면 상세 평가 결과가 모달로 뜨게 해달라.",
        ],
        "result": "165fb1b — 가중 평균 + 카드/모달 UI 적용.",
    },
    {
        "idx": "6",
        "title": "평가 중 차단 해결 + 점수 체계 안내",
        "situation": (
            "'전체 평가' 가 돌고 있을 때 다른 페이지가 거의 안 열리는 문제가 있었다. "
            "또한 마케터 입장에서 종합 점수가 어떻게 계산되는지 공개돼 있지 않아 판단 근거가 모호했다."
        ),
        "requests": [
            "evaluate_creator 엔드포인트를 async def → def 로 바꿔서 FastAPI 가 자동으로 threadpool 에 오프로드하도록 해달라. 그러면 이벤트 루프가 살아 있어 사용자가 사이트를 계속 돌아다닐 수 있다.",
            "메인 페이지에 '평가 점수 체계' 섹션을 새로 추가해달라. 5개 항목의 가중치는 카드로, 각 항목별 점수 구간표는 펼침/접힘 영역으로.",
            "헤더의 'Powered by ...' 문구는 불필요하니 삭제해달라.",
        ],
        "result": "3827a6d — 차단 해결 + 점수 체계 카드 + 헤더 정리.",
    },
    {
        "idx": "7",
        "title": "모바일 반응형 대응",
        "situation": (
            "PC 환경에서는 문제가 없었으나, 모바일로 열면 헤더·입력·추천 카드·점수 상세 같은 "
            "가로 flex 레이아웃 섹션들이 찌그러지거나 잘려 보였다."
        ),
        "requests": [
            "PC 화면(≥640px)은 최대한 그대로 유지하면서 모바일에서만 깨지는 부분을 고쳐달라.",
            "메인 분석 페이지(index.html)와 관리자 콘솔(admin_console.html) 두 쪽 모두 대응해달라.",
        ],
        "result": (
            "0108a12 — 헤더/입력/추천 카드/채널 개요/점수 상세를 모바일에서 세로 스택으로 전환, "
            "관리자 카드 aspect-square 를 모바일에서만 해제, style.css 에 @media (max-width: 640px) "
            "안전망(본문 패딩·차트 높이·채널명 줄바꿈) 추가."
        ),
    },
    {
        "idx": "8",
        "title": "Gemini 모델 교체",
        "situation": (
            "댓글 배치 감성분석에 쓰던 Gemini 모델이 초기 선택한 2.0-flash 로 고정돼 있었다."
        ),
        "requests": [
            "댓글 배치 감성 분석 모델을 gemini-2.0-flash 에서 gemini-2.5-flash 로 바꿔달라. "
            "(평가 요약문 생성 쪽 모델은 그대로 유지)",
        ],
        "result": "0108a12 — gemini_service.py:143 한 줄 교체.",
    },
    {
        "idx": "9",
        "title": "변경사항 배포",
        "situation": "반응형 대응과 모델 교체까지 끝난 뒤 바로 원격에 반영하고 싶었다.",
        "requests": [
            "로컬 변경분을 커밋한 뒤 origin/main 으로 푸시해달라.",
        ],
        "result": "3827a6d..0108a12 푸시 완료.",
    },
]


def build() -> None:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("malgun", "", FONT_REG)
    pdf.add_font("malgun", "B", FONT_BOLD)
    pdf.set_margins(left=20, top=20, right=20)

    # --- 표지 ---
    pdf.add_page()
    pdf.set_xy(pdf.l_margin, 50)
    pdf.set_font("malgun", "B", 22)
    pdf.multi_cell(0, 12, TITLE, align="C")
    pdf.ln(2)
    pdf.set_font("malgun", "", 14)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 9, SUBTITLE, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(18)
    pdf.set_font("malgun", "", 11)
    pdf.multi_cell(0, 7, INTRO)

    # --- 본문 ---
    pdf.add_page()
    pdf.set_xy(pdf.l_margin, pdf.t_margin)
    for sec in SECTIONS:
        # 섹션 타이틀
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "B", 14)
        pdf.set_text_color(30, 60, 160)
        pdf.multi_cell(0, 9, f"{sec['idx']}. {sec['title']}")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        # 상황
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "B", 11)
        pdf.multi_cell(0, 7, "상황")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "", 11)
        pdf.multi_cell(0, 6.5, sec["situation"])
        pdf.ln(2)

        # 요청
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "B", 11)
        pdf.multi_cell(0, 7, "요청")
        pdf.set_font("malgun", "", 11)
        for req in sec["requests"]:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6.5, f"· {req}")
        pdf.ln(2)

        # 결과
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "B", 11)
        pdf.multi_cell(0, 7, "결과")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("malgun", "", 11)
        pdf.multi_cell(0, 6.5, sec["result"])

        pdf.ln(5)
        y = pdf.get_y()
        pdf.set_draw_color(220, 220, 220)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(5)

    pdf.output(str(OUT))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
