# services/discord_bot.py

import os
import logging
import time
from io import BytesIO
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Interaction, Object, Attachment, File, User

from PyPDF2 import PdfReader
from src.utils import Utils
from src.services.prompt import PromptBuilder
from src.services.resume import ResumeReviewService
from utils import VaultSecretsLoader

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DiscordBotClient:
    def __init__(self):
        self.token = VaultSecretsLoader().load_secret("discord-token") or os.getenv(
            "DISCORD_TOKEN"
        )

        if not self.token:
            raise ValueError(
                "Discord token not found. Set DISCORD_TOKEN environment variable or use Vault secrets."
            )
        if not os.getenv("DISCORD_GUILD_ID"):
            raise ValueError(
                "Discord guild ID not found. Set DISCORD_GUILD_ID environment variable."
            )

        self.guild = Object(id=int(os.getenv("DISCORD_GUILD_ID")))
        intents = Intents.default()  # Add this line
        self.bot = commands.Bot(command_prefix="/", intents=intents)

        @self.bot.check
        async def globally_block_dms(ctx):
            if ctx.guild is None:
                await ctx.send(
                    "Commands can only be used in a server, not in DMs. Please use it in a DSB server.",
                )
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
        async def review_resume(
            interaction: Interaction, file: Attachment, user: User = None
        ):
            await interaction.response.defer(ephemeral=True)  # ⬅ acknowledge quickly

            if User is not None:
                user = interaction.user

            if interaction.guild is None:
                await interaction.followup.send(
                    "This command can only be used in a server, not in DMs. Please use it in a server.",
                    ephemeral=True,
                )
                return

            if (
                interaction.user.get_role(
                    int(os.getenv("DISCORD_COMMUNITY_MANAGER_ROLE_ID"))
                )
                is None
            ):
                await interaction.followup.send(
                    "You do not have permission to use this command. Please contact a community manager.",
                    ephemeral=True,
                )
                return

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
                await interaction.followup.send(
                    f"We encountered an error reading the PDF. Please ensure it is a valid PDF file, and try again."
                )
                logging.error(f"Error reading PDF: {str(e)}")
                return

            try:
                prompt = PromptBuilder.build_review_prompt(resume_text=resume)
                logging.info("Generated prompt for resume review for %s", user.name)

                feedback = ResumeReviewService().generate_feedback(prompt)
                if not feedback:
                    await interaction.followup.send(
                        "I am unable to provide feedback at this time. Please try again later."
                    )
                    logging.error(
                        "No feedback generated for resume review: %s", user.name
                    )
                    return

                logging.info(
                    "Received feedback from the resume review service for %s", user.name
                )

                pdf_file = Utils.convert_md_to_pdf(feedback)
                await interaction.followup.send(
                    content=f"<@{user.id}>, your resume feedback is attached as a PDF. I hope you find this helpful! Good luck with your job search!",
                    file=File(
                        pdf_file,
                        filename=f"{user.name}_{time.time()}.pdf",
                    ),
                )
            except Exception as e:
                await interaction.followup.send(
                    "An error occurred while processing your resume that I could not handle. Please contact a community manager for assistance."
                )
                logging.error(
                    f"Error processing resume review for {user.name}: {str(e)}"
                )

    def run(self):
        self.bot.run(self.token)
