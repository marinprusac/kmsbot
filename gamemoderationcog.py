from discord.ext import commands
import helper
import management
import discord


class GameModeration(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		server = management.get_server(guild.id)
		if not server.data.setup_complete:
			return False

		member = helper.get_member(guild, id=ctx.author.id)
		if server.admin_role not in member.roles:
			return False

		if not server.data.game_running:
			return False

		return True

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
	bot.add_cog(GameModeration(bot))