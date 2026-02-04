import discord
import logging

logger = logging.getLogger("bot_logger")

class ImagePaginator(discord.ui.View):
    def __init__(self, results, query, author_id, timeout=300):
        super().__init__(timeout=timeout)
        self.results = results  # lista de dicts com 'title' e 'link'
        self.query = query
        self.index = 0
        self.author_id = author_id
        self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def _update_button_states(self):
        # Disable prev on first, next on last
        for child in self.children:
            if getattr(child, "custom_id", None) == "prev_btn":
                child.disabled = (self.index == 0)
            if getattr(child, "custom_id", None) == "next_btn":
                child.disabled = (self.index == len(self.results) - 1)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, custom_id="prev_btn")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        self._update_button_states()
        current_result = self.results[self.index]
        title = current_result["title"]
        url = current_result["link"]
        embed = discord.Embed(title=f"{title} ({self.index + 1}/{len(self.results)})", url=url)
        embed.set_image(url=url)
        logger.info(f"Embed URL set to: {url}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary, custom_id="next_btn")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.results) - 1:
            self.index += 1
        self._update_button_states()
        current_result = self.results[self.index]
        title = current_result["title"]
        url = current_result["link"]
        embed = discord.Embed(title=f"{title} ({self.index + 1}/{len(self.results)})", url=url)
        embed.set_image(url=url)
        logger.info(f"Embed URL set to: {url}")
        await interaction.response.edit_message(embed=embed, view=self)