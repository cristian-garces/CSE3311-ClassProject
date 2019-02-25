from fpdf import FPDF


class PDFMaker(FPDF):
    def __init__(self, page_orientation="P", size_units="mm", size="Letter", **kwargs):
        super().__init__(page_orientation, size_units, size)
        self.title = kwargs.get("title", "")
        self.set_title(self.title)

        self.default_draw_color = kwargs.get("draw_color", {"r": 255, "g": 255, "b": 255})
        self.default_fill_color = kwargs.get("fill_color", {"r": 255, "g": 255, "b": 255})
        self.default_text_color = kwargs.get("text_color", {"r": 0, "g": 0, "b": 0})
        self.uta_blue = kwargs.get("text_color", {"r": 0, "g": 68, "b": 124})
        self.uta_orange = kwargs.get("text_color", {"r": 245, "g": 128, "b": 38})
        self.default_font = kwargs.get("font", {"family": "Arial", "style": "", "size": 9})
        self.default_header_font = kwargs.get("title_font", {"family": "Arial", "style": "B", "size": 16})
        self.default_title_font = kwargs.get("header_font", {"family": "Arial", "style": "B", "size": 11})
        self.default_footer_font = kwargs.get("title_font", {"family": "Arial", "style": "I", "size": 7})

    def header(self):
        self.set_font(**self.default_header_font)

        self.set_x(10)
        self.set_y(30)
        self.set_draw_color(**self.default_draw_color)
        self.set_fill_color(**self.default_fill_color)
        self.set_text_color(**self.uta_blue)
        self.set_line_width(1)

        self.cell(0, 9, self.title, 1, 1, "C", 1)

        self.ln(5)

    def footer(self):
        self.set_font(**self.default_footer_font)
        self.set_text_color(**self.default_text_color)
        self.set_y(-15)

        self.cell(0, 10, str(self.page_no()), 0, 0, "R")

    def page_title(self, text):
        self.set_font(**self.default_title_font)
        self.set_fill_color(**self.default_fill_color)
        self.set_text_color(**self.default_text_color)

        self.cell(0, 6, text, 0, 1, "L", 1)

        self.ln(3)

    def page_body(self, text):
        self.set_font(**self.default_font)

        self.multi_cell(0, 5, text)

        self.ln()

    def print_page(self, title, text):
        self.add_page()
        self.page_title(title)
        self.page_body(text)
