"""docs/assignment.md 를 PDF 로 렌더링한다."""
from __future__ import annotations

import re
from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).parent
SRC = ROOT / "assignment.md"
OUT = ROOT / "assignment.pdf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"

PAGE_W = 210.0
LEFT = 20.0
RIGHT = 20.0
USABLE_W = PAGE_W - LEFT - RIGHT


def strip_bold(text: str) -> list[tuple[str, bool]]:
    """**bold** 마커를 (segment, is_bold) 리스트로 분리한다."""
    parts: list[tuple[str, bool]] = []
    pattern = re.compile(r"\*\*(.+?)\*\*")
    idx = 0
    for m in pattern.finditer(text):
        if m.start() > idx:
            parts.append((text[idx:m.start()], False))
        parts.append((m.group(1), True))
        idx = m.end()
    if idx < len(text):
        parts.append((text[idx:], False))
    return parts or [(text, False)]


def write_inline(pdf: FPDF, text: str, size: float = 10.5, line_h: float = 6.2) -> None:
    """볼드 마커를 해석해 한 문단을 출력한다."""
    # 한 줄 안에서 bold/normal 이 섞일 수 있으나
    # fpdf2 의 write() 는 글꼴을 중간에 바꿔도 같은 줄에 이어 붙여준다.
    pdf.set_x(LEFT)
    for seg, is_bold in strip_bold(text):
        pdf.set_font("malgun", "B" if is_bold else "", size)
        pdf.write(line_h, seg)
    pdf.ln(line_h)


def heading(pdf: FPDF, level: int, text: str) -> None:
    sizes = {1: 18, 2: 15, 3: 12.5, 4: 11.5}
    colors = {1: (20, 40, 120), 2: (30, 60, 160), 3: (40, 80, 180), 4: (60, 60, 60)}
    size = sizes.get(level, 11)
    r, g, b = colors.get(level, (0, 0, 0))

    if level <= 2:
        pdf.ln(3)
    else:
        pdf.ln(1.5)
    pdf.set_x(LEFT)
    pdf.set_font("malgun", "B", size)
    pdf.set_text_color(r, g, b)
    pdf.multi_cell(USABLE_W, size * 0.55, text)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def bullet(pdf: FPDF, text: str, indent: float = 0.0) -> None:
    pdf.set_x(LEFT + indent)
    pdf.set_font("malgun", "", 10.5)
    pdf.cell(4, 6.2, "·")
    # 나머지 행은 multi_cell 로 자동 줄바꿈
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    width = USABLE_W - 4 - indent
    # 볼드 인라인 처리를 위해 직접 write 사용
    pdf.set_xy(x_start, y_start)
    for seg, is_bold in strip_bold(text):
        pdf.set_font("malgun", "B" if is_bold else "", 10.5)
        # write 는 자동 줄바꿈 시 좌측 여백(LEFT)으로 복귀하므로 원하는 indent 유지 용도로 별도 처리
        pdf.write(6.2, seg)
    pdf.ln(6.2)


def checkbox(pdf: FPDF, checked: bool, text: str) -> None:
    pdf.set_x(LEFT)
    pdf.set_font("malgun", "B", 10.5)
    mark = "[v]" if checked else "[ ]"
    pdf.cell(10, 6.2, mark)
    pdf.set_font("malgun", "", 10.5)
    for seg, is_bold in strip_bold(text):
        pdf.set_font("malgun", "B" if is_bold else "", 10.5)
        pdf.write(6.2, seg)
    pdf.ln(6.2)


def hrline(pdf: FPDF) -> None:
    pdf.ln(2)
    y = pdf.get_y()
    pdf.set_draw_color(210, 210, 210)
    pdf.line(LEFT, y, PAGE_W - RIGHT, y)
    pdf.ln(3)


def codeblock(pdf: FPDF, lines: list[str]) -> None:
    pdf.ln(1)
    pdf.set_font("malgun", "", 9.5)
    pdf.set_fill_color(245, 246, 250)
    pdf.set_draw_color(220, 223, 230)
    pdf.set_text_color(25, 30, 50)
    line_h = 5.2
    pad = 2.0
    # 간단하게 각 줄을 배경 있는 cell 로 출력
    for ln in lines:
        pdf.set_x(LEFT)
        # 너무 길면 multi_cell 로 쪼갠다
        pdf.multi_cell(USABLE_W, line_h, ln if ln else " ", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def table(pdf: FPDF, rows: list[list[str]]) -> None:
    """| ... | ... | 형태 표 렌더. rows[0] 은 헤더, rows[1] 은 구분선이 이미 제거된 상태."""
    if not rows:
        return
    header = rows[0]
    body = rows[1:]
    cols = len(header)
    # 열 폭: 첫 열은 약간 좁게, 나머지는 균등
    if cols == 2:
        widths = [USABLE_W * 0.30, USABLE_W * 0.70]
    elif cols == 3:
        widths = [USABLE_W * 0.25, USABLE_W * 0.35, USABLE_W * 0.40]
    else:
        widths = [USABLE_W / cols] * cols

    line_h = 6.0
    pdf.ln(1)

    def render_row(cells: list[str], is_header: bool) -> None:
        pdf.set_font("malgun", "B" if is_header else "", 10)
        if is_header:
            pdf.set_fill_color(232, 237, 250)
        else:
            pdf.set_fill_color(252, 252, 252)
        pdf.set_draw_color(210, 214, 225)
        # 각 셀의 필요한 높이를 미리 구해 최대값으로 맞춘다
        heights = []
        for w, txt in zip(widths, cells):
            # multi_cell 의 dry-run 대체: 단순 길이 기반 예측
            # fpdf2 의 get_string_width 기반으로 줄 수 계산
            pdf.set_x(LEFT)
            lines = 1
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", txt)
            # 대략적인 줄 수 추정 — split_only 옵션을 이용
            split = pdf.multi_cell(w - 2, line_h, text, split_only=True)
            lines = max(1, len(split))
            heights.append(lines * line_h)
        row_h = max(heights) if heights else line_h

        x = LEFT
        y = pdf.get_y()
        # 페이지 넘침 처리
        if y + row_h > pdf.h - pdf.b_margin:
            pdf.add_page()
            y = pdf.get_y()
        for w, txt in zip(widths, cells):
            pdf.set_xy(x, y)
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", txt)
            pdf.multi_cell(w, line_h, text, border=1, fill=True)
            x += w
        pdf.set_xy(LEFT, y + row_h)

    render_row(header, is_header=True)
    for row in body:
        render_row(row, is_header=False)
    pdf.ln(1)


def parse_table(block: list[str]) -> list[list[str]]:
    """| a | b | 형태의 블록을 2차원 리스트로 파싱하고 구분선(| --- |)은 제거."""
    rows = []
    for line in block:
        s = line.strip()
        if not s.startswith("|"):
            continue
        # 구분선 제거
        if re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?", s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        rows.append(cells)
    return rows


def render(pdf: FPDF, md: str) -> None:
    lines = md.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 수평선
        if stripped == "---":
            hrline(pdf)
            i += 1
            continue

        # 코드블록
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            codeblock(pdf, buf)
            i += 1  # closing ```
            continue

        # 표
        if stripped.startswith("|") and stripped.endswith("|"):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            rows = parse_table(buf)
            table(pdf, rows)
            continue

        # 헤더
        m = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            heading(pdf, level, text)
            i += 1
            continue

        # 체크박스 항목
        m = re.match(r"^-\s+\[( |x|X)\]\s+(.*)", stripped)
        if m:
            checked = m.group(1).lower() == "x"
            checkbox(pdf, checked, m.group(2))
            i += 1
            continue

        # 일반 리스트
        m = re.match(r"^[-*]\s+(.*)", stripped)
        if m:
            bullet(pdf, m.group(1))
            i += 1
            continue

        # 번호 리스트
        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if m:
            pdf.set_x(LEFT)
            pdf.set_font("malgun", "B", 10.5)
            pdf.cell(8, 6.2, f"{m.group(1)}.")
            pdf.set_font("malgun", "", 10.5)
            for seg, is_bold in strip_bold(m.group(2)):
                pdf.set_font("malgun", "B" if is_bold else "", 10.5)
                pdf.write(6.2, seg)
            pdf.ln(6.2)
            i += 1
            continue

        # 공백
        if stripped == "":
            pdf.ln(2)
            i += 1
            continue

        # 일반 문단
        write_inline(pdf, stripped)
        i += 1


def build() -> None:
    md = SRC.read_text(encoding="utf-8")
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("malgun", "", FONT_REG)
    pdf.add_font("malgun", "B", FONT_BOLD)
    pdf.set_margins(left=LEFT, top=18, right=RIGHT)
    pdf.add_page()
    pdf.set_xy(LEFT, pdf.t_margin)
    render(pdf, md)
    pdf.output(str(OUT))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
