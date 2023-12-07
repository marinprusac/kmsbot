from discord.ext import commands
import helper
import management


class AliveCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		member = helper.get_member(guild, id=ctx.author.id)
		return 'alive' in [role.name for role in member.roles]

	@commands.command()
	async def reroll(self, ctx: commands.Context, what: str = ''):
		server = management.get_server(ctx.guild.id)
		person = what == 'person' or what == 'all'
		location = what == 'location' or what == 'all'
		weapon = what == 'weapon' or what == 'all'
		await server.reroll_mission(helper.get_player(ctx.author.id, server.data.players),
		                            reroll_person=person, reroll_location=location, reroll_weapon=weapon)

	@commands.command()
	async def kill(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		await server.mission_accomplished(helper.get_player(ctx.author.id, server.data.players))


def setup(bot: commands.Bot):
	bot.add_cog(AliveCog(bot))