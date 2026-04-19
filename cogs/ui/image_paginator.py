import discord
import logging
from urllib.parse import urlparse

from utils.http import get_timestamp

logger = logging.getLogger("bot_logger")

class ImagePaginator(discord.ui.View):
    def __init__(self, results, query, ctx, timeout=300, search_engine="DuckDuckGo"):
        super().__init__(timeout=timeout)
        self.results = results
        self.query = query
        self.index = 0
        self.author_id = ctx.author.id
        self.author_name = ctx.author.display_name
        self.author_avatar = ctx.author.avatar.url if ctx.author.avatar else None
        self.message = None
        self.search_engine = search_engine
        self.time_str = get_timestamp()

    def build_embed(self) -> discord.Embed:
        result = self.results[self.index]
        title = result["title"]
        url = result["link"]

        domain = urlparse(url).netloc

        embed = discord.Embed(
            title=title,
            description=f"[{domain}]({url})",
            url=url,
        )
        embed.set_author(name=self.author_name, icon_url=self.author_avatar)
        embed.set_image(url=url)
        embed.set_footer(text=f"Página {self.index + 1}/{len(self.results)} - {self.search_engine} • {self.time_str}")
        return embed

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def update_button_states(self):
        for child in self.children:
            if getattr(child, "custom_id", None) == "prev_btn":
                child.disabled = (self.index == 0)
            if getattr(child, "custom_id", None) == "next_btn":
                child.disabled = (self.index == len(self.results) - 1)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, custom_id="prev_btn")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        self.update_button_states()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary, custom_id="next_btn")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.results) - 1:
            self.index += 1
        self.update_button_states()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="shuffle_btn")
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        import random
        self.index = random.randint(0, len(self.results) - 1)
        self.update_button_states()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)
