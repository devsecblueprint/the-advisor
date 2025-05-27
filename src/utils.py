import os
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


class VaultSecretsLoader:
    """
    A class to load secrets from Vault Agent-injected files.
    """

    def __init__(self, secret_path="/vault/secrets"):
        """
        Initializes the VaultSecretsLoader.

        Args:
            secret_path (str): The base path where Vault secrets are injected.
        """
        self.secret_path = secret_path

    def load_secret(self, secret_file_name: str):
        """
        Loads the secret from the Vault-injected file.

        Returns:
            str: The Redis password, or None if the file is not found.
        """
        return self._load_secret_file(secret_file_name)

    def _load_secret_file(self, filename):
        """
        Loads the content of a secret file.

        Args:
            filename (str): The name of the secret file to load.

        Returns:
            str: The content of the secret file, or None if the file is not found.
        """
        file_path = os.path.join(self.secret_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(
                f"Secret file '{filename}' not found at path '{file_path}'. Is Vault Agent Injector configured?"
            )
            return None
