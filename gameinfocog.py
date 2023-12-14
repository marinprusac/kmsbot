
from discord.ext import commands
import management
import helper


class GameInfo(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		server = management.get_server(guild.id)
		if not server.data.setup_complete:
			return False

		return True

	@commands.command()
	async def getwpn(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		weapons = server.data.weapons
		str_print = '\n'.join(weapons)
		await ctx.send(f"Weapons list:\n{str_print}")

	@commands.command()
	async def getloc(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		locations = server.data.locations
		str_print = '\n'.join(locations)
		await ctx.send(f"Locations list:\n{str_print}")


def setup(bot: commands.Bot):
	bot.add_cog(GameInfo(bot))