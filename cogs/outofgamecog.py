from discord.ext import commands
import discordserver
import helper


class OutOfGame(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		server = discordserver.get_server(guild.id)
		if not server.data.setup_complete:
			return False

		if server.data.game_running:
			return False

		return True

	@commands.command()
	async def register(self, ctx: commands.Context):
		server = discordserver.get_server(ctx.guild.id)

		member = helper.get_member(ctx.guild, id=ctx.author.id)

		if server.registered_role in member.roles:
			await ctx.send(f"You already registered!")
		else:
			await member.add_roles(server.registered_role)
			await ctx.send(f"You have registered to play the game!")

	@commands.command()
	async def unregister(self, ctx: commands.Context):
		server = discordserver.get_server(ctx.guild.id)

		if server.data.game_running:
			await ctx.send("Command failed. Reason: Cannot unregister during a running game!")
			return

		member = helper.get_member(ctx.guild, id=ctx.author.id)

		if server.registered_role not in member.roles:
			await ctx.send(f"You aren't registered!")
		else:
			await member.remove_roles(server.registered_role)
			await ctx.send(f"You have unregistered from playing the game!")