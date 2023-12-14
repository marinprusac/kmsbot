import discord
from discord.ext import commands
import sys

from cogs import gameinfocog, aliveplayerscog, outofgamecog, gamemoderationcog, adminscog, systemcog
import discordserver


def main(token):
	bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

	@bot.event
	async def on_command_error(ctx: commands.Context, error: commands.CommandError):
		if isinstance(error, commands.CheckFailure):
			await ctx.send("You do not have permission to use this command here at this moment.")
			return

		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("You are missing a required argument.")
			return

		if isinstance(error, commands.BadArgument):
			await ctx.send("You have provided a bad argument.")
			return

		if isinstance(error, commands.CommandNotFound):
			await ctx.send("Command not found.")
			return

		if isinstance(error, commands.MissingPermissions):
			await ctx.send("You are missing permissions to use this command.")
			return

	@bot.event
	async def on_ready():
		await discordserver.load_guilds(bot)
		await bot.add_cog(systemcog.System(bot))
		await bot.add_cog(gameinfocog.GameInfo(bot))
		await bot.add_cog(aliveplayerscog.AlivePlayers(bot))
		await bot.add_cog(outofgamecog.OutOfGame(bot))
		await bot.add_cog(gamemoderationcog.GameModeration(bot))
		await bot.add_cog(adminscog.Admins(bot))
		print(f"Logged in as {bot.user}")

	@bot.event
	async def on_member_join(member: discord.Member):
		pass

	@bot.event
	async def on_member_remove(member: discord.Member):
		server = management.get_server(member.guild.id)
		await server.remove_player(member, True)

	@bot.event
	async def on_guild_join(guild: discord.Guild):
		management.add_server(guild.id, management.DiscordServer(guild))

	@bot.event
	async def on_guild_remove(guild: discord.Guild):
		management.remove_server(guild.id)
	bot.run(token)


if __name__ == '__main__':
	main(sys.argv[1])
