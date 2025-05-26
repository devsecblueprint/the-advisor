# services/discord_bot.py

import os
import logging
from datetime import date
from io import BytesIO
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Interaction, Object, Attachment, File
from PyPDF2 import PdfReader

from src.utils import Utils
from src.services.prompt import PromptBuilder
from src.services.resume import ResumeReviewService


load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DiscordBotClient:
    def __init__(self):
        self.token = os.getenv("DISCORD_TOKEN")
        self.guild = Object(id=int(os.getenv("DISCORD_GUILD_ID")))
        self.api_url = os.getenv("API_URL")
        intents = Intents.default()  # Add this line
        self.bot = commands.Bot(
            command_prefix="/", intents=intents
        )  # Pass intents here

        @self.bot.check
        async def globally_block_dms(ctx):
            if ctx.guild is None:
                await ctx.send("❌ Commands can only be used in a server, not in DMs.")
                return False
            return True

        self._register_commands()
        self._register_events()

    def _register_events(self):
        @self.bot.event
        async def on_ready():
            logging.info(f"Logged in as {self.bot.user.name} (ID: {self.bot.user.id})")
            try:
                synced = await self.bot.tree.sync(guild=self.guild)
                logging.info(f"Synced {len(synced)} command(s) to guild {self.guild}.")
            except Exception as e:
                logging.error(f"Failed to sync commands: {e}")

    def _register_commands(self):
        @self.bot.tree.command(
            name="review_resume",
            description="Submit your resume for feedback.",
            guild=self.guild,
        )
        async def review_resume(interaction: Interaction, file: Attachment):
            if interaction.guild is None:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server, not in DMs.",
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(
                "Processing your resume, please wait...", ephemeral=True
            )
            logging.info(f"Received resume for review from {interaction.user.name}.")

            # Check if the user attached a file (resume) via the 'file' parameter
            if file is None:
                await interaction.followup.send("Please attach a PDF file.")
                return

            if not file.filename.lower().endswith(".pdf"):
                await interaction.followup.send("Only PDF files are supported.")
                return

            try:
                file_bytes = await file.read()
                pdf_bytes = BytesIO(file_bytes)
                reader = PdfReader(pdf_bytes)
                resume_text = ""
                for page in reader.pages:
                    resume_text += page.extract_text() or ""
                resume = resume_text
            except Exception as e:
                await interaction.followup.send(f"⚠️ Failed to read PDF: {str(e)}")
                return

            try:
                prompt = PromptBuilder.build_review_prompt(resume_text=resume)
                logging.info("Generated prompt for resume review")

                feedback = ResumeReviewService().generate_feedback(prompt)
                if not feedback:
                    await interaction.followup.send(
                        "❌ The Advisor failed to generate feedback."
                    )
                    return

                logging.info("Received feedback from the resume review service")

                pdf_file = Utils.convert_md_to_pdf(feedback)
                await interaction.followup.send(
                    content="Your resume feedback is attached as a PDF. Good luck with your job search!",
                    file=File(
                        pdf_file,
                        filename=f"{interaction.user.name}_{date.isoformat(date.today())}.pdf",
                    ),
                )
            except Exception as e:
                await interaction.followup.send(f"⚠️ Error: {str(e)}")

    def run(self):
        self.bot.run(self.token)