from discord.ext import commands
import management
import helper

class OutOfGameCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def getwpn(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		server.data.load()
		weapons = server.data.weapons
		str_print = '\n'.join(weapons)
		await ctx.send(f"Weapons list:\n{str_print}")

	@commands.command()
	async def getloc(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		server.data.load()
		locations = server.data.locations
		str_print = '\n'.join(locations)
		await ctx.send(f"Locations list:\n{str_print}")

	@commands.command()
	async def register(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		server.data.load()

		if server.data.game_running:
			await ctx.send("Command failed. Reason: Cannot register during a running game!")
			return

		member = helper.get_member(ctx.guild, id=ctx.author.id)

		if server.registered_role in member.roles:
			await ctx.send(f"You already registered!")
		else:
			await member.add_roles(server.registered_role)
			await ctx.send(f"You have registered to play the game!")

	@commands.command()
	async def unregister(self, ctx: commands.Context):
		server = management.get_server(ctx.guild.id)
		server.data.load()

		if server.data.game_running:
			await ctx.send("Command failed. Reason: Cannot unregister during a running game!")
			return

		member = helper.get_member(ctx.guild, id=ctx.author.id)

		if server.registered_role not in member.roles:
			await ctx.send(f"You aren't registered!")
		else:
			await member.remove_roles(server.registered_role)
			await ctx.send(f"You have unregistered from playing the game!")