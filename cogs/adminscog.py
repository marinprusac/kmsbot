import discord
from discord.ext import commands
import helper
import discordserver


class Admins(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		server = discordserver.get_server(guild.id)
		if not server.data.setup_complete:
			return False

		member = helper.get_member(guild, id=ctx.author.id)
		if server.admin_role not in member.roles:
			return False

		if server.data.game_running:
			return False

		return True

	@commands.command()
	async def setwpn(self, ctx: commands.Context, *args):
		server = discordserver.get_server(ctx.guild.id)
		weapons = [a.strip(',') for a in args]
		server.data.weapons = weapons
		server.data.save()
		await ctx.send("Weapons set and ready.")

	@commands.command()
	async def setloc(self, ctx: commands.Context, *args):
		server = discordserver.get_server(ctx.guild.id)
		locations: list[str] = [a.strip(',') for a in args]
		server.data.locations = locations
		server.data.save()
		await ctx.send("Locations set and ready!")

	@commands.command()
	async def start(self, ctx: commands.Context):
		server = discordserver.get_server(ctx.guild.id)
		await server.start_game()




def setup(bot: commands.Bot):
	bot.add_cog(Admins(bot))