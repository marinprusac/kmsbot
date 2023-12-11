import os

import discord
from discord.ext import commands

import management
import alivecog, outofgamecog, admincog

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello there, {ctx.author.name}!")


@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command()
async def h(ctx: commands.Context):
    try:
        with open('./help.txt') as file:
            text = file.read()
            await ctx.send(text)
    except BaseException:
        await ctx.send("Command failed. Reason: CRITICAL SERVER ERROR!")


@bot.event
async def on_ready():

    await management.prepare_commands(bot)
    await bot.add_cog(alivecog.AliveCog(bot))
    await bot.add_cog(outofgamecog.OutOfGameCog(bot))
    await bot.add_cog(admincog.AdminCog(bot))
    print(f"Logged in as {bot.user}")


def main():
    bot.run('MTE4MzgzODY0ODY1NTk0NTg1MA.G6oWej.WJCLjHIfBJzpYlaSZHzkuV3vXG-pMA5rLyuxlk')


if __name__ == '__main__':
    main()