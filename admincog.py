import discord
from discord.ext import commands
import helper
import management


class AdminCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		member = helper.get_member(guild, id=ctx.author.id)
		return 'admin' in [role.name for role in member.roles]

	@commands.command()
	async def setwpn(self, ctx: commands.Context, *args):
		server = management.get_server(ctx.guild.id)
		weapons = [a.strip(',') for a in args]
		server.data.weapons = weapons
		server.data.save()
		await ctx.send("Weapons set and ready.")

	@commands.command()
	async def setloc(self, ctx: commands.Context, *args):
		server = management.get_server(ctx.guild.id)
		locations: list[str] = [a.strip(',') for a in args]
		server.data.locations = locations
		server.data.save()
		await ctx.send("Locations set and ready!")

	@commands.command()
	async def start(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		await server.start_game()

	@commands.command()
	async def end(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		await server.end_game()

	@commands.command()
	async def final(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		await server.day_report(True)

	@commands.command()
	async def nextday(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		await server.day_report(False)

	@commands.command()
	async def systemrevive(self, ctx: commands.Context, member: discord.Member):
		server = management.get_server(ctx.guild.id)
		await server.revive_player(helper.get_player(member.id, server.data.players))

	@commands.command()
	async def systemkill(self, ctx: commands.Context, member: discord.Member):
		server = management.get_server(ctx.guild.id)
		await server.kill_player(helper.get_player(member.id, server.data.players))

	@commands.command()
	async def systemintroduce(self, ctx: commands.Context, member: discord.Member):
		server = management.get_server(ctx.guild.id)
		await server.add_player(member)

	@commands.command()
	async def systemremove(self, ctx: commands.Context, member: discord.Member):
		server = management.get_server(ctx.guild.id)
		await server.remove_player(helper.get_player(member.id, server.data.players))


def setup(bot: commands.Bot):
	bot.add_cog(AdminCog(bot))