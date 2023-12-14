import discord
from discord.ext import commands
from typing import Mapping, Any, List, Optional


class Help(commands.HelpCommand):

	async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]], /) -> None:
		pass

	async def send_cog_help(self, cog: commands.Cog, /) -> None:
		pass

	async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
		pass
