import discord
from discord.ext import commands

import adminscog
import aliveplayerscog
import gameinfocog
import management
import outofgamecog
import systemcog
import gamemoderationcog


def main():
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
		await management.load_guilds(bot)
		await bot.add_cog(systemcog.System(bot))
		await bot.add_cog(gameinfocog.GameInfo(bot))
		await bot.add_cog(aliveplayerscog.AlivePlayers(bot))
		await bot.add_cog(outofgamecog.OutOfGame(bot))
		await bot.add_cog(gamemoderationcog.GameModeration(bot))
		await bot.add_cog(adminscog.Admins(bot))

		print(f"Logged in as {bot.user}")

	bot.run('MTE4MzgzODY0ODY1NTk0NTg1MA.G6oWej.WJCLjHIfBJzpYlaSZHzkuV3vXG-pMA5rLyuxlk')


if __name__ == '__main__':
	main()