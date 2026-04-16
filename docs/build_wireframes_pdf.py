"""화면 설계(Wireframe) PDF 생성 스크립트."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from fpdf import FPDF

OUT = Path(__file__).parent / "wireframes.pdf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"

TITLE = "화면 설계 (Wireframe)"
SUBTITLE = "슈퍼센트 파트너 크리에이터 평가 도구"
DEPLOY_URL = "https://spcchecker.up.railway.app/"
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# 색상 (RGB)
C_BORDER = (150, 150, 150)
C_BORDER_DARK = (70, 70, 70)
C_FILL_SOFT = (245, 247, 250)
C_FILL_ACCENT = (225, 235, 250)
C_FILL_MODAL = (240, 240, 240)
C_TEXT_SUB = (90, 90, 90)
C_TEXT_MUTED = (140, 140, 140)


def draw_box(pdf, x, y, w, h, *, fill=None, dashed=False, thick=False):
    if thick:
        pdf.set_line_width(0.45)
    else:
        pdf.set_line_width(0.2)
    pdf.set_draw_color(*C_BORDER)
    if dashed:
        dl, sl = 1.2, 0.9
        pdf.dashed_line(x, y, x + w, y, dl, sl)
        pdf.dashed_line(x, y + h, x + w, y + h, dl, sl)
        pdf.dashed_line(x, y, x, y + h, dl, sl)
        pdf.dashed_line(x + w, y, x + w, y + h, dl, sl)
    else:
        if fill:
            pdf.set_fill_color(*fill)
            pdf.rect(x, y, w, h, style="DF")
        else:
            pdf.rect(x, y, w, h)
    pdf.set_line_width(0.2)


def put_label(pdf, x, y, w, h, label, desc=None, center=False):
    pdf.set_xy(x + 2, y + 1.5)
    pdf.set_font("malgun", "B", 8.5)
    pdf.set_text_color(0, 0, 0)
    if center:
        pdf.cell(w - 4, 4.5, label, align="C")
    else:
        pdf.cell(w - 4, 4.5, label)
    if desc:
        pdf.set_xy(x + 2, y + 5.8)
        pdf.set_font("malgun", "", 7.5)
        pdf.set_text_color(*C_TEXT_SUB)
        pdf.multi_cell(w - 4, 3.6, desc, align="C" if center else "L")
        pdf.set_text_color(0, 0, 0)


def put_annot(pdf, x, y, text, max_w=60):
    pdf.set_xy(x, y)
    pdf.set_font("malgun", "", 7)
    pdf.set_text_color(*C_TEXT_MUTED)
    pdf.multi_cell(max_w, 3.2, text)
    pdf.set_text_color(0, 0, 0)


def draw_arrow(pdf, x1, y1, x2, y2):
    pdf.set_draw_color(*C_BORDER_DARK)
    pdf.set_line_width(0.3)
    pdf.line(x1, y1, x2, y2)
    # 화살촉
    if abs(x1 - x2) < 0.1:  # 수직
        pdf.line(x2, y2, x2 - 1.2, y2 - 1.6 if y2 > y1 else y2 + 1.6)
        pdf.line(x2, y2, x2 + 1.2, y2 - 1.6 if y2 > y1 else y2 + 1.6)
    else:
        pdf.line(x2, y2, x2 - 1.6, y2 - 1.2)
        pdf.line(x2, y2, x2 - 1.6, y2 + 1.2)


def page_header(pdf, chapter, title_ko):
    pdf.set_xy(pdf.l_margin, 10)
    pdf.set_font("malgun", "", 8)
    pdf.set_text_color(*C_TEXT_MUTED)
    pdf.cell(0, 4, f"{TITLE}  —  {SUBTITLE}")
    pdf.ln(4)
    pdf.set_font("malgun", "B", 13)
    pdf.set_text_color(30, 60, 160)
    pdf.cell(0, 7, f"{chapter}  {title_ko}")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)
    y = pdf.get_y()
    pdf.set_draw_color(200, 210, 230)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(3)


# ====== 페이지별 그리기 함수 ======

def draw_cover(pdf: FPDF):
    pdf.add_page()
    pdf.set_xy(pdf.l_margin, 70)
    pdf.set_font("malgun", "B", 26)
    pdf.multi_cell(0, 13, TITLE, align="C")
    pdf.ln(4)
    pdf.set_font("malgun", "", 14)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 8, SUBTITLE, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)

    # 메타 박스
    box_w, box_h = 130, 28
    bx = (pdf.w - box_w) / 2
    by = pdf.get_y()
    draw_box(pdf, bx, by, box_w, box_h, fill=C_FILL_SOFT)
    pdf.set_xy(bx + 6, by + 4)
    pdf.set_font("malgun", "B", 10)
    pdf.cell(40, 5, "배포 URL")
    pdf.set_font("malgun", "", 10)
    pdf.cell(0, 5, DEPLOY_URL)
    pdf.set_xy(bx + 6, by + 11)
    pdf.set_font("malgun", "B", 10)
    pdf.cell(40, 5, "문서 종류")
    pdf.set_font("malgun", "", 10)
    pdf.cell(0, 5, "저해상도 와이어프레임 (흑백 박스 스킴)")
    pdf.set_xy(bx + 6, by + 18)
    pdf.set_font("malgun", "B", 10)
    pdf.cell(40, 5, "작성일")
    pdf.set_font("malgun", "", 10)
    pdf.cell(0, 5, DATE_STR)

    pdf.ln(40)
    pdf.set_font("malgun", "", 10)
    pdf.set_text_color(*C_TEXT_SUB)
    pdf.multi_cell(
        0, 6,
        "본 문서는 프로토타입의 화면 구성과 정보 배치를 규정하는 설계도입니다. "
        "실제 색/폰트/이미지 스타일은 배제하고, 각 영역의 역할과 상호작용을 박스와 라벨로만 표현했습니다.",
        align="C",
    )
    pdf.set_text_color(0, 0, 0)


def draw_inventory(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.1", "화면 인벤토리")

    rows = [
        ("메인 분석 페이지", "/",
         "URL 입력 → AI 분석 파이프라인 실행 → 결과 대시보드 렌더",
         "마케터 (외부 노출)"),
        ("관리자 콘솔", "/sc-9f3b2a7c",
         "등록된 크리에이터 목록·스케줄 관리·카드 클릭 시 상세 모달",
         "관리자 (Basic Auth)"),
        ("(내부) 상세 결과 모달", "모달 오버레이",
         "메인 페이지의 결과 대시보드와 동일한 구조를 모달 내부로 재사용",
         "관리자"),
    ]

    # 헤더
    pdf.set_font("malgun", "B", 9.5)
    pdf.set_fill_color(230, 235, 245)
    col_w = [46, 42, 68, 30]
    headers = ["화면", "경로", "핵심 역할", "사용자"]
    x = pdf.l_margin
    y = pdf.get_y()
    for w, t in zip(col_w, headers):
        pdf.set_xy(x, y)
        pdf.cell(w, 7, t, border=1, fill=True, align="C")
        x += w
    pdf.ln(7)

    pdf.set_font("malgun", "", 9)
    for row in rows:
        x = pdf.l_margin
        y = pdf.get_y()
        row_h = 14
        for w, text in zip(col_w, row):
            pdf.set_xy(x, y)
            pdf.multi_cell(w, 4.5, text, border=1)
            x += w
        pdf.set_y(y + row_h)

    pdf.ln(8)
    pdf.set_font("malgun", "B", 10)
    pdf.cell(0, 6, "공통 디자인 토큰")
    pdf.ln(6)
    pdf.set_font("malgun", "", 9)
    pdf.multi_cell(
        0, 5,
        "· 중앙 정렬: max-w-6xl (약 1152px) / 가로 패딩: 24px (모바일 16px)\n"
        "· 카드 스타일: 흰색 배경 + 라운드 12px + 1px 연한 테두리 + 은은한 그림자\n"
        "· 판정 컬러 팔레트: PASS=초록 / REVIEW=노랑 / FAIL=빨강\n"
        "· Chart.js 반응형: 컨테이너 너비 추종, 모바일에서 최대 높이 220px\n"
        "· Breakpoint: sm=640px 이상에서 멀티컬럼, 그 미만에서 세로 스택",
    )


def draw_main_pc_before(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.2", "메인 분석 페이지 — PC (분석 전)")

    left = pdf.l_margin
    top = pdf.get_y() + 2
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    # 전체 컨테이너 (max-w-6xl 시뮬)
    # 헤더 (full-bleed 느낌은 빼고 박스로 표현)
    y = top
    draw_box(pdf, left, y, usable_w, 14, fill=C_FILL_SOFT)
    put_label(pdf, left, y, usable_w, 14,
              "[Header]  파트너 크리에이터 평가 도구",
              "좌: 로고 + 제목 + 부제  |  우: '크리에이터 관리' 버튼 (→ /sc-9f3b2a7c)")
    y += 16

    # URL 입력 섹션
    draw_box(pdf, left, y, usable_w, 26)
    put_label(pdf, left, y, usable_w, 5,
              "[URL 입력 섹션]")
    # 내부: input + button
    draw_box(pdf, left + 4, y + 8, usable_w - 50, 8)
    put_label(pdf, left + 4, y + 8, usable_w - 50, 8, "YouTube 채널 URL input")
    draw_box(pdf, left + usable_w - 42, y + 8, 38, 8, fill=C_FILL_ACCENT)
    put_label(pdf, left + usable_w - 42, y + 8, 38, 8, "분석 시작", center=True)
    # 토글
    draw_box(pdf, left + 4, y + 19, 80, 5, dashed=True)
    put_annot(pdf, left + 4, y + 19, "[ toggle ] 슈퍼센트 게임 영상만 분석", max_w=120)
    y += 28

    # 점수 체계 안내
    draw_box(pdf, left, y, usable_w, 50)
    put_label(pdf, left, y, usable_w, 5, "[평가 점수 체계 안내]",
              "5개 평가 항목과 가중치를 카드로 제시")
    # 5개 가중치 카드
    card_w = (usable_w - 8 - 4 * 2) / 5
    items = [
        ("구독자", "20%"),
        ("참여도", "25%"),
        ("성장률", "20%"),
        ("감성", "20%"),
        ("일관성", "15%"),
    ]
    for i, (name, weight) in enumerate(items):
        cx = left + 4 + i * (card_w + 2)
        cy = y + 10
        draw_box(pdf, cx, cy, card_w, 16, fill=C_FILL_ACCENT)
        pdf.set_xy(cx, cy + 2)
        pdf.set_font("malgun", "B", 8)
        pdf.cell(card_w, 4, name, align="C")
        pdf.set_xy(cx, cy + 7)
        pdf.set_font("malgun", "B", 11)
        pdf.cell(card_w, 5, weight, align="C")
    # 접힘 영역 인디케이터
    draw_box(pdf, left + 4, y + 29, usable_w - 8, 7, dashed=True)
    put_annot(pdf, left + 6, y + 29.5,
              "▶ (클릭) 항목별 점수 계산 기준 펼치기 — 6칸 상세 표로 확장", max_w=200)
    # 판정 기준
    draw_box(pdf, left + 4, y + 38, usable_w - 8, 9)
    put_label(pdf, left + 4, y + 38, usable_w - 8, 4, "추천 판정 기준")
    pdf.set_xy(left + 6, y + 42)
    pdf.set_font("malgun", "", 7.5)
    pdf.set_text_color(*C_TEXT_SUB)
    pdf.cell(0, 3.6,
             "PASS: 종합 60점↑ & 구독자 500↑    REVIEW: 둘 중 하나만    FAIL: 둘 다 미충족")
    pdf.set_text_color(0, 0, 0)
    y += 54

    # 로딩 상태 플레이스홀더
    draw_box(pdf, left, y, usable_w, 18, dashed=True)
    put_label(pdf, left, y, usable_w, 5,
              "[분석 진행 중 로딩]  (분석 버튼 클릭 후 표시, 기본 hidden)",
              "스피너 + '채널 데이터를 수집하고 있습니다...' 안내")
    y += 22

    # 하단 주석
    put_annot(pdf, left, y + 2,
              "※ 분석 완료 시 아래 결과 대시보드 영역(P.3)이 이 아래에 렌더링됨", max_w=usable_w)


def draw_main_pc_after(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.3", "메인 분석 페이지 — PC (분석 후 결과 대시보드)")

    left = pdf.l_margin
    top = pdf.get_y() + 2
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    y = top
    # 추천 카드
    draw_box(pdf, left, y, usable_w, 22, fill=C_FILL_SOFT)
    put_label(pdf, left, y, usable_w, 5, "[추천 카드]",
              "좌: 판정 배지(PASS/REVIEW/FAIL) + 제목 + 종합점수 / 우: 평가 일자")
    # 배지 모양
    draw_box(pdf, left + 4, y + 10, 22, 8, fill=C_FILL_ACCENT)
    put_label(pdf, left + 4, y + 10, 22, 8, "PASS", center=True)
    put_annot(pdf, left + 30, y + 10, "파트너십 추천 결과", max_w=60)
    put_annot(pdf, left + 30, y + 14, "종합 점수: XX.X/100", max_w=60)
    put_annot(pdf, left + usable_w - 40, y + 10, "YYYY-MM-DD", max_w=36)
    y += 24

    # 채널 개요
    draw_box(pdf, left, y, usable_w, 32)
    put_label(pdf, left, y, usable_w, 5, "[채널 개요]")
    # 썸네일
    draw_box(pdf, left + 4, y + 9, 20, 20, fill=C_FILL_ACCENT)
    put_label(pdf, left + 4, y + 9, 20, 20, "thumb", center=True)
    # 타이틀 영역
    put_annot(pdf, left + 28, y + 10, "채널명 (h3)", max_w=60)
    put_annot(pdf, left + 28, y + 14, "@handle", max_w=60)
    # 4개 KPI
    kpi_start_x = left + 28
    kpi_w = (usable_w - 32 - 6) / 4
    kpis = ["구독자", "총 조회수", "영상 수", "가입일"]
    for i, name in enumerate(kpis):
        kx = kpi_start_x + i * (kpi_w + 2)
        draw_box(pdf, kx, y + 19, kpi_w, 10, fill=C_FILL_ACCENT)
        put_label(pdf, kx, y + 19, kpi_w, 10, name, "값", center=True)
    y += 34

    # 슈퍼센트 필터 정보
    draw_box(pdf, left, y, usable_w, 12)
    put_label(pdf, left, y, usable_w, 5, "[슈퍼센트 필터 정보]",
              "슈퍼센트 관련 영상 수 / 전체 영상 / 분석 댓글 수 (경고 조건부 표시)")
    y += 14

    # 차트 2x2
    ch_w = (usable_w - 4) / 2
    ch_h = 32
    charts = [
        ("차트 1  최근 영상 조회수", "Chart.js bar"),
        ("차트 2  댓글 감성 분포", "Chart.js doughnut"),
        ("차트 3  영상별 참여율 (%)", "Chart.js line/bar"),
        ("차트 4  항목별 점수", "Chart.js radar"),
    ]
    for i, (name, kind) in enumerate(charts):
        cx = left + (i % 2) * (ch_w + 4)
        cy = y + (i // 2) * (ch_h + 3)
        draw_box(pdf, cx, cy, ch_w, ch_h)
        put_label(pdf, cx, cy, ch_w, 5, name, kind)
    y += ch_h * 2 + 6

    # 댓글 분석
    draw_box(pdf, left, y, usable_w, 32)
    put_label(pdf, left, y, usable_w, 5, "[댓글 감성분석 결과]",
              "Gemini 2.5 Flash 가중 평균 기반")
    # 긍정/중립/부정 카드
    sw = (usable_w - 8 - 6) / 3
    for i, name in enumerate(["긍정", "중립", "부정"]):
        sx = left + 4 + i * (sw + 3)
        draw_box(pdf, sx, y + 10, sw, 8, fill=C_FILL_ACCENT)
        put_label(pdf, sx, y + 10, sw, 8, name, center=True)
    # 테마 태그 + 댓글 목록
    draw_box(pdf, left + 4, y + 20, usable_w - 8, 4, dashed=True)
    put_annot(pdf, left + 6, y + 20.2, "[#테마] [#테마] [#테마] … 핵심 테마 태그 그룹", max_w=200)
    draw_box(pdf, left + 4, y + 25, usable_w - 8, 4, dashed=True)
    put_annot(pdf, left + 6, y + 25.2, "주목할 댓글 (긍2·부2·중1) 목록 — 감정 뱃지 + 인용", max_w=200)
    y += 34

    # 점수 상세
    draw_box(pdf, left, y, usable_w, 32)
    put_label(pdf, left, y, usable_w, 5, "[종합 점수 상세]")
    # 원
    draw_box(pdf, left + 4, y + 9, 22, 22, fill=C_FILL_ACCENT)
    put_label(pdf, left + 4, y + 9, 22, 22, "종합 점수", "원형 링", center=True)
    # 진행 바 5개
    bar_x = left + 30
    bar_w = usable_w - 34
    for i, name in enumerate(["구독자", "참여도", "성장률", "감성", "일관성"]):
        by_ = y + 10 + i * 4.2
        pdf.set_xy(bar_x, by_)
        pdf.set_font("malgun", "", 7.5)
        pdf.cell(18, 3, name)
        draw_box(pdf, bar_x + 18, by_ + 0.5, bar_w - 20, 2.3, fill=C_FILL_ACCENT)


def draw_main_mobile(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.4", "메인 분석 페이지 — Mobile (375px)")

    left = pdf.l_margin
    top = pdf.get_y() + 2

    # 좌: 모바일 프레임, 우: 주석
    frame_w = 70
    frame_x = left + 5
    frame_y = top
    # 배경 프레임
    draw_box(pdf, frame_x - 2, frame_y - 2, frame_w + 4, 255, thick=True)
    put_annot(pdf, frame_x - 2, frame_y - 6, "viewport 375px 시뮬", max_w=60)

    y = frame_y
    # 헤더 (세로 스택)
    draw_box(pdf, frame_x, y, frame_w, 22, fill=C_FILL_SOFT)
    put_label(pdf, frame_x, y, frame_w, 5, "Header")
    put_annot(pdf, frame_x + 2, y + 8, "로고+제목 (세로 위)", max_w=frame_w - 4)
    put_annot(pdf, frame_x + 2, y + 14, "[관리자] 버튼 (세로 아래)", max_w=frame_w - 4)
    y += 24

    # 입력
    draw_box(pdf, frame_x, y, frame_w, 30)
    put_label(pdf, frame_x, y, frame_w, 5, "URL 입력")
    draw_box(pdf, frame_x + 2, y + 8, frame_w - 4, 6)
    put_label(pdf, frame_x + 2, y + 8, frame_w - 4, 6, "input 전체 폭")
    draw_box(pdf, frame_x + 2, y + 15, frame_w - 4, 6, fill=C_FILL_ACCENT)
    put_label(pdf, frame_x + 2, y + 15, frame_w - 4, 6, "분석 시작", center=True)
    draw_box(pdf, frame_x + 2, y + 23, frame_w - 4, 5, dashed=True)
    put_annot(pdf, frame_x + 3, y + 23.5, "토글 + 라벨", max_w=frame_w - 6)
    y += 32

    # 점수 체계 (2열로 축소)
    draw_box(pdf, frame_x, y, frame_w, 42)
    put_label(pdf, frame_x, y, frame_w, 5, "점수 체계")
    for i in range(5):
        r, c = divmod(i, 2)
        cw = (frame_w - 4 - 2) / 2
        cx = frame_x + 2 + c * (cw + 2)
        cy = y + 8 + r * 10
        draw_box(pdf, cx, cy, cw, 8, fill=C_FILL_ACCENT)
    put_annot(pdf, frame_x + 2, y + 36, "▶ 상세 펼치기", max_w=frame_w - 4)
    y += 44

    # 추천 카드 세로 스택
    draw_box(pdf, frame_x, y, frame_w, 28, fill=C_FILL_SOFT)
    put_label(pdf, frame_x, y, frame_w, 5, "추천 카드")
    draw_box(pdf, frame_x + 2, y + 8, 16, 6, fill=C_FILL_ACCENT)
    put_label(pdf, frame_x + 2, y + 8, 16, 6, "PASS", center=True)
    put_annot(pdf, frame_x + 2, y + 16, "제목 + 점수 (아래)", max_w=frame_w - 4)
    put_annot(pdf, frame_x + 2, y + 21, "일자 (세로 스택)", max_w=frame_w - 4)
    y += 30

    # 채널 개요 세로 스택
    draw_box(pdf, frame_x, y, frame_w, 48)
    put_label(pdf, frame_x, y, frame_w, 5, "채널 개요")
    draw_box(pdf, frame_x + (frame_w - 18) / 2, y + 8, 18, 18, fill=C_FILL_ACCENT)
    put_label(pdf, frame_x + (frame_w - 18) / 2, y + 8, 18, 18, "thumb", center=True)
    # 2x2 KPI
    for i, name in enumerate(["구독자", "조회수", "영상 수", "가입일"]):
        r, c = divmod(i, 2)
        cw = (frame_w - 4 - 2) / 2
        cx = frame_x + 2 + c * (cw + 2)
        cy = y + 28 + r * 9
        draw_box(pdf, cx, cy, cw, 8, fill=C_FILL_ACCENT)
        put_label(pdf, cx, cy, cw, 8, name, center=True)
    y += 50

    # 차트 (1열)
    for i in range(4):
        draw_box(pdf, frame_x, y, frame_w, 14)
        put_label(pdf, frame_x, y, frame_w, 5, f"차트 {i+1}", "canvas max-h 220px")
        y += 16

    # 오른쪽 주석 영역
    right_x = frame_x + frame_w + 15
    right_y = top
    pdf.set_xy(right_x, right_y)
    pdf.set_font("malgun", "B", 10)
    pdf.cell(0, 5, "모바일 주요 변화")
    right_y += 7
    notes = [
        "· 헤더가 세로 스택 (로고+제목 위, 버튼 아래).",
        "· URL input 과 버튼이 세로로 쌓여 양쪽 다 전체 폭.",
        "· 점수 체계 카드가 5열→2열 그리드.",
        "· 추천 카드 배지/제목/일자가 세로 스택.",
        "· 채널 개요 썸네일이 중앙 정렬, KPI 가 2×2.",
        "· 차트 2×2 → 1열 세로 스택.",
        "· 댓글/점수 상세도 세로로 정렬 (생략).",
        "· style.css @media (max-width: 640px) 안전망으로 본문 패딩·차트 높이 제어.",
    ]
    for n in notes:
        pdf.set_xy(right_x, right_y)
        pdf.set_font("malgun", "", 9)
        pdf.multi_cell(pdf.w - right_x - pdf.r_margin, 4.5, n)
        right_y = pdf.get_y() + 1


def draw_admin_pc(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.5", "관리자 콘솔 — PC")

    left = pdf.l_margin
    top = pdf.get_y() + 2
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    y = top
    # 헤더
    draw_box(pdf, left, y, usable_w, 14, fill=C_FILL_SOFT)
    put_label(pdf, left, y, usable_w, 14,
              "[Header]  크리에이터 관리",
              "좌: 제목 + 부제  |  우: [개별 분석] [전체 평가 실행]")
    y += 16

    # 진행률 (조건부)
    draw_box(pdf, left, y, usable_w, 14, dashed=True)
    put_label(pdf, left, y, usable_w, 14,
              "[전체 평가 진행률]  (전체 평가 실행 시에만 표시)",
              "진행 메시지 + x/N 카운트 + progress bar + 실패 요약")
    y += 16

    # 등록
    draw_box(pdf, left, y, usable_w, 22)
    put_label(pdf, left, y, usable_w, 5, "[크리에이터 등록]")
    draw_box(pdf, left + 4, y + 9, usable_w - 70, 8)
    put_label(pdf, left + 4, y + 9, usable_w - 70, 8, "채널 URL input")
    draw_box(pdf, left + usable_w - 64, y + 9, 24, 8, dashed=True)
    put_label(pdf, left + usable_w - 64, y + 9, 24, 8, "[v] SC 필터", center=True)
    draw_box(pdf, left + usable_w - 36, y + 9, 32, 8, fill=C_FILL_ACCENT)
    put_label(pdf, left + usable_w - 36, y + 9, 32, 8, "등록", center=True)
    y += 24

    # 스케줄
    draw_box(pdf, left, y, usable_w, 22)
    put_label(pdf, left, y, usable_w, 5, "[자동 평가 스케줄]")
    # 스위치 + 라벨 + select + 저장
    draw_box(pdf, left + 4, y + 10, 10, 6, fill=C_FILL_ACCENT)
    put_annot(pdf, left + 16, y + 10, "스케줄 활성화", max_w=30)
    draw_box(pdf, left + 50, y + 10, 50, 6)
    put_label(pdf, left + 50, y + 10, 50, 6, "주기 프리셋 select")
    draw_box(pdf, left + 102, y + 10, 36, 6, dashed=True)
    put_label(pdf, left + 102, y + 10, 36, 6, "cron 직접 입력 (조건부)", center=True)
    draw_box(pdf, left + usable_w - 22, y + 10, 18, 6, fill=C_FILL_ACCENT)
    put_label(pdf, left + usable_w - 22, y + 10, 18, 6, "저장", center=True)
    put_annot(pdf, left + 4, y + 17, "마지막 실행 시각 표시 (우측 정렬)", max_w=120)
    y += 24

    # 크리에이터 카드 그리드 (3x2)
    draw_box(pdf, left, y, usable_w, 92)
    put_label(pdf, left, y, usable_w, 5,
              "[등록된 크리에이터 카드 그리드 (3열)]",
              "각 카드: aspect-square. 클릭 시 상세 결과 모달 (→ P.6)")
    card_w = (usable_w - 8 - 2 * 4) / 3
    card_h = (92 - 10 - 4) / 2
    for i in range(6):
        r, c = divmod(i, 3)
        cx = left + 4 + c * (card_w + 4)
        cy = y + 10 + r * (card_h + 4)
        draw_box(pdf, cx, cy, card_w, card_h)
        # 카드 내부 구조
        draw_box(pdf, cx + 2, cy + 2, 10, 10, fill=C_FILL_ACCENT)
        put_annot(pdf, cx + 14, cy + 2, "채널명 truncate", max_w=card_w - 16)
        put_annot(pdf, cx + 14, cy + 5, "@handle", max_w=card_w - 16)
        draw_box(pdf, cx + card_w - 14, cy + 2, 12, 4, fill=C_FILL_ACCENT)
        put_label(pdf, cx + card_w - 14, cy + 2, 12, 4, "PASS", center=True)
        # 점수 박스
        draw_box(pdf, cx + 2, cy + 14, card_w - 4, 8, fill=C_FILL_SOFT)
        put_annot(pdf, cx + 3, cy + 15, "종합 점수 / 구독자", max_w=card_w - 6)
        # 요약 + 버튼
        put_annot(pdf, cx + 2, cy + 24, "AI 요약 (3줄)", max_w=card_w - 4)
        put_annot(pdf, cx + 2, cy + card_h - 6, "평가일", max_w=card_w * 0.45)
        draw_box(pdf, cx + card_w - 22, cy + card_h - 6.5, 10, 5, fill=C_FILL_ACCENT)
        put_label(pdf, cx + card_w - 22, cy + card_h - 6.5, 10, 5, "평가", center=True)
        draw_box(pdf, cx + card_w - 10, cy + card_h - 6.5, 8, 5)
        put_label(pdf, cx + card_w - 10, cy + card_h - 6.5, 8, 5, "삭제", center=True)


def draw_admin_modal(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.6", "관리자 콘솔 — 상세 결과 모달")

    left = pdf.l_margin
    top = pdf.get_y() + 2
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    # 딤 배경
    draw_box(pdf, left, top, usable_w, 210, fill=C_FILL_MODAL)
    put_annot(pdf, left + 2, top + 2,
              "모달 오버레이: 반투명 배경 + 블러. 외부 클릭/× 버튼으로 닫기.",
              max_w=usable_w - 4)

    # 모달 본체 (가운데 정렬, 살짝 inset)
    mx = left + 8
    my = top + 10
    mw = usable_w - 16
    mh = 195
    draw_box(pdf, mx, my, mw, mh, fill=(255, 255, 255), thick=True)

    # 모달 헤더 (sticky)
    draw_box(pdf, mx, my, mw, 14, fill=C_FILL_SOFT)
    put_label(pdf, mx, my, mw, 14,
              "[Modal Header — sticky]",
              "좌: 제목 + 서브타이틀 (채널명)  |  우: × 닫기 버튼")

    # 내부: 메인 결과 대시보드와 동일 구조 재사용
    inner_y = my + 18
    sections = [
        ("추천 카드", "판정 배지 + 제목 + 점수 + 일자"),
        ("채널 개요", "썸네일 + 4 KPI"),
        ("슈퍼센트 필터 정보", "영상·댓글 수 요약"),
        ("차트 2×2 그리드", "조회수·감성·참여율·점수"),
        ("댓글 감성분석 패널", "긍중부 + 테마 + 주목 댓글"),
        ("점수 상세", "원형 점수 + 5 항목 바"),
    ]
    for name, desc in sections:
        draw_box(pdf, mx + 4, inner_y, mw - 8, 22)
        put_label(pdf, mx + 4, inner_y, mw - 8, 5, f"[{name}]", desc)
        inner_y += 25

    # 오른쪽 안내
    pdf.set_xy(left, my + mh + 4)
    pdf.set_font("malgun", "", 9)
    pdf.set_text_color(*C_TEXT_SUB)
    pdf.multi_cell(0, 4.5,
                   "※ 이 모달의 내부 영역은 메인 분석 페이지 '결과 대시보드'(P.3) 와 "
                   "동일한 HTML 구조·JS 렌더 함수를 재사용함 (charts.js · ui.js). "
                   "DOM id 가 중복되지 않도록 모달 열릴 때 기존 차트를 destroy 하고 재생성.")
    pdf.set_text_color(0, 0, 0)


def draw_user_flow(pdf: FPDF):
    pdf.add_page()
    page_header(pdf, "P.7", "User Flow — 분석 파이프라인")

    left = pdf.l_margin
    top = pdf.get_y() + 6
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    nodes = [
        ("① URL 입력", "사용자가 YouTube 채널 URL 을 입력하고 '분석 시작' 클릭"),
        ("② 채널 ID 해석", "channel_resolver: /@handle, /channel/UCxxx, /user 등 다양한 형식을 채널 ID 로 변환"),
        ("③ YouTube 데이터 수집", "youtube_service: 채널 메타 + 최근 영상 목록 + 영상별 댓글"),
        ("④ Gemini 감성분석 (병렬)", "gemini_service.analyze_comments_batch — ThreadPool 로 배치 동시 호출 (gemini-2.5-flash)"),
        ("⑤ 스코어 계산", "scoring_service: 5개 항목 가중 평균 → 종합점수 + 판정"),
        ("⑥ 평가 요약문 생성", "gemini_service.generate_evaluation_summary — 한국어 평가 요약"),
        ("⑦ 대시보드 렌더", "frontend app.js: 차트/카드/점수바 일괄 렌더, fade-in 애니메이션"),
    ]

    node_w = 140
    node_h = 16
    x = left + (usable_w - node_w) / 2
    y = top
    for label, desc in nodes:
        draw_box(pdf, x, y, node_w, node_h, fill=C_FILL_SOFT)
        put_label(pdf, x, y, node_w, 5, label, desc)
        # 화살표 (마지막 제외)
        if label != nodes[-1][0]:
            draw_arrow(pdf, x + node_w / 2, y + node_h + 0.5,
                       x + node_w / 2, y + node_h + 5.5)
        y += node_h + 6


def build():
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("malgun", "", FONT_REG)
    pdf.add_font("malgun", "B", FONT_BOLD)
    pdf.set_margins(left=12, top=12, right=12)

    draw_cover(pdf)
    draw_inventory(pdf)
    draw_main_pc_before(pdf)
    draw_main_pc_after(pdf)
    draw_main_mobile(pdf)
    draw_admin_pc(pdf)
    draw_admin_modal(pdf)
    draw_user_flow(pdf)

    pdf.output(str(OUT))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
