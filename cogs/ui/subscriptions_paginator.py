import discord
from typing import List, Dict, Optional
from utils.http import logger

class SubscriptionsPaginator(discord.ui.View):
    def __init__(self, subs_list: List[Dict], author_id: int, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.subs = subs_list  # lista de dicts com keys: sub (raw subscription), user (dict ou None)
        self.index = 0
        self.author_id = author_id
        self.message: Optional[discord.Message] = None

    def _update_button_states(self):
        for child in self.children:
            if getattr(child, "custom_id", None) == "prev_sub":
                child.disabled = (self.index == 0)
            if getattr(child, "custom_id", None) == "next_sub":
                child.disabled = (self.index == len(self.subs) - 1)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                logger.exception("Falha ao atualizar mensagem na timeout do paginator")

        try:
            self.message = None
        except Exception:
            pass

        try:
            if isinstance(self.subs, list):
                self.subs.clear()
        except Exception:
            pass

        try:
            self.clear_items()
        except Exception:
            pass

    def _build_embed_for_index(self, idx: int) -> discord.Embed:
        item = self.subs[idx]
        sub = item.get("sub", {})
        user = item.get("user") or {}
        broadcaster_id = sub.get("condition", {}).get("broadcaster_user_id", "")
        display = user.get("display_name") or user.get("login") or broadcaster_id
        description = (user.get("description") or "").strip()
        if len(description) > 80:
            description = description[:77] + "..."
        profile = user.get("profile_image_url") or ""

        title = f"{display} ({idx+1}/{len(self.subs)})"
        streamer_url = f"https://twitch.tv/{user.get('login', broadcaster_id)}"
        embed = discord.Embed(title=title, description=description or "—", url=streamer_url)
        if profile:
            embed.set_thumbnail(url=profile)

        # campos da subscription
        embed.add_field(name="Subscription ID", value=sub.get("id", "—"), inline=False)
        embed.add_field(name="Tipo", value=sub.get("type", "—"), inline=True)
        embed.add_field(name="Status", value=sub.get("status", "—"), inline=True)
        embed.add_field(name="Broadcaster ID", value=broadcaster_id, inline=True)
        embed.add_field(name="Criado Em", value=sub.get("created_at", "—"), inline=True)

        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, custom_id="prev_sub")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        self._update_button_states()
        embed = self._build_embed_for_index(self.index)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary, custom_id="next_sub")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.subs) - 1:
            self.index += 1
        self._update_button_states()
        embed = self._build_embed_for_index(self.index)
        await interaction.response.edit_message(embed=embed, view=self)
