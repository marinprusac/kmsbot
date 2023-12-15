from discord.ext import commands
import helper
import discordserver


class AlivePlayers(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		server = discordserver.get_server(guild.id)
		if not server.data.setup_complete:
			return False

		if not server.data.game_running:
			return False

		member = helper.get_member(guild, id=ctx.author.id)
		if server.alive_role not in member.roles:
			return False

		player = helper.get_player(ctx.author.id, server.data.players)
		if ctx.channel.id != helper.get_player_channel(guild, player).id:
			return False

		return True

	@commands.command()
	async def reroll(self, ctx: commands.Context, what: str = ''):
		server = discordserver.get_server(ctx.guild.id)
		person = what == 'person' or what == 'all'
		location = what == 'location' or what == 'all'
		weapon = what == 'weapon' or what == 'all'
		await server.reroll_mission(helper.get_player(ctx.author.id, server.data.players),
		                            person=person, location=location, weapon=weapon)

	@commands.command()
	async def kill(self, ctx: commands.Context):
		server = discordserver.get_server(ctx.guild.id)
		await server.mission_accomplished(helper.get_player(ctx.author.id, server.data.players))


def setup(bot: commands.Bot):
	bot.add_cog(AlivePlayers(bot))