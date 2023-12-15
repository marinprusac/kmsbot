from discord.ext import commands
import helper
import gamemanager
import discord


class System(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def cog_check(self, ctx: commands.Context) -> bool:
		guild = ctx.guild
		if guild is None:
			return False

		return True

	@commands.command()
	async def hello(self, ctx: commands.Context):
		await ctx.send(f"Hello there, {ctx.author.name}!")

	@commands.command()
	async def ping(self, ctx: commands.Context):
		await ctx.send(f"Pong! {round(ctx.bot.latency * 1000)}ms")

	@commands.command()
	@commands.has_permissions(administrator=True)
	async def setup(self, ctx: commands.Context,
	                admin_channel: discord.TextChannel,
	                announce_channel: discord.TextChannel,
	                private_category: discord.CategoryChannel,
	                admin_role: discord.Role,
	                register_role: discord.Role,
	                alive_role: discord.Role,
	                dead_role: discord.Role):

		if admin_channel is None or announce_channel is None or private_category is None:
			await ctx.send("Please provide all 3 arguments: admin_channel_id, announce_channel_id, private_category_id")
			return
		await ctx.send("Setting up server...")
		server = gamemanager.get_server(ctx.guild.id)

		server.data.admin_channel_id = admin_channel.id
		server.data.announcements_channel_id = announce_channel.id
		server.data.private_category_id = private_category.id
		server.data.admin_role_id = admin_role.id
		server.data.registered_role_id = register_role.id
		server.data.alive_role_id = alive_role.id
		server.data.dead_role_id = dead_role.id
		server.data.save()
		success = server.setup()
		server.data.setup_complete = success
		server.data.save()
		if success:
			await ctx.send("Setup complete!")
		else:
			await ctx.send("Setup failed!")


def setup(bot: commands.Bot):
	bot.add_cog(System(bot))