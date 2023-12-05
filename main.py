import os

import discord
from discord.ext import commands

from cmds import prepare_commands

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

    await prepare_commands(bot)
    print(f"Logged in as {bot.user}")


def main():
    bot.run('MTE3OTE1MzU3Njk0MjExMjg0OQ.GtfXh2.FqwyyU5khyAOhzJeM7eRAGN_yGgTc-SSpDT-B8')


if __name__ == '__main__':
    main()