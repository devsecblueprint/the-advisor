import markdown2
from weasyprint import HTML
from io import BytesIO


class Utils:

    @staticmethod
    def convert_md_to_pdf(md_text: str) -> BytesIO:
        # Convert markdown to HTML
        html = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
        # Add basic CSS for better formatting
        css = """
        <style>
            body { font-family: Arial, sans-serif; margin: 0.5em; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            pre, code { background-color: #f4f4f4; padding: 4px; border-radius: 4px; }
        </style>
        """
        html = f"<html><head>{css}</head><body>{html}</body></html>"

        pdf_bytes = BytesIO()
        HTML(string=html).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes
