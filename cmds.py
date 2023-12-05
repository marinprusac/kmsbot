from discord.ext import commands
from helper import *
from datahandler import DataHandler
from management import DiscordServer

server: DiscordServer


async def prepare_commands(bot: commands.Bot):
    global server
    guild = bot.guilds[0]
    server = DiscordServer(guild)
    bot.add_command(reload)
    bot.add_command(setwpn)
    bot.add_command(setloc)
    bot.add_command(getwpn)
    bot.add_command(getloc)
    bot.add_command(register)
    bot.add_command(unregister)
    bot.add_command(start)
    bot.add_command(end)
    bot.add_command(revive)
    bot.add_command(kill)
    bot.add_command(introduce)
    bot.add_command(remove)
    bot.add_command(success)
    bot.add_command(reroll)
    await server.refresh()


def role_required(*roles: str):
    async def predicate(ctx: Context):
        member = get_member(ctx.guild, id=ctx.author.id)
        if not member:
            return False
        return any(role_name in (role.name for role in member.roles)
                   for role_name in roles)

    return commands.check(predicate)


# commands
@commands.command()
async def reroll(ctx: commands.Context, what: str = ''):
    person = what == 'person' or what == 'all'
    location = what == 'location' or what == 'all'
    weapon = what == 'weapon' or what == 'all'

    if not person and not location and not weapon:
        await ctx.send("Please specify what you want to reroll (person, location, weapon, all).")
        return

    allowed = await server.reroll_mission(ctx.author.id, reroll_person=person, reroll_location=location, reroll_weapon=weapon)
    if allowed:
        await ctx.send("**Rerolled.**")
    else:
        await ctx.send("You don't have anymore rerolls.")


@commands.command()
@role_required("alive")
async def success(ctx: commands.Context):
    allowed = await server.mission_accomplished(ctx.author.id)
    if allowed:
        await ctx.send("**Successfully killed!**")
    else:
        await ctx.send("You cannot kill anymore.")


@commands.command()
@role_required("alive")
async def reload(ctx: commands.Context):
    await server.refresh()
    await ctx.send("Reloaded and cleaned up.")


@commands.command()
@role_required("admin")
async def setwpn(ctx: commands.Context, *args):
    argss: list[str] = [a.strip(',') for a in args]
    DataHandler.set('weapons', argss)
    await ctx.send("Weapons set and ready.")


@commands.command()
async def getwpn(ctx: commands.Context):
    args: list[str] = DataHandler.get('weapons')
    str_print = '\n'.join(args)
    await ctx.send(f"Weapons list:\n{str_print}")


@commands.command()
@role_required("admin")
async def setloc(ctx: commands.Context, *args):
    argss: list[str] = [a.strip(',') for a in args]
    DataHandler.set('locations', argss)
    await ctx.send("Locations set and ready!")


@commands.command()
async def getloc(ctx: commands.Context):
    args: list[str] = DataHandler.get('locations')
    str_print = '\n'.join(args)
    await ctx.send(f"Locations list:\n{str_print}")


@commands.command()
async def register(ctx: commands.Context, *mentions: str):
    if DataHandler.get('running'):
        await ctx.send(
            "Command failed. Reason: Cannot register during a running game!")
        return

    if ctx.author not in server.admin_role.members and len(mentions) > 0:
        await ctx.send("Command failed. Only admins may register by mention. Use the command without parameters.")

    members = extract_members_from_args(ctx, *mentions)
    if members is None:
        await ctx.send("Command failed. Invalid mention.")
        return

    for member in members:
        if server.registered_role in member.roles:
            await ctx.send(f"{member.mention} is already registered!")
        else:
            await member.add_roles(server.registered_role)
            await ctx.send(f"{member.mention} has registered to play the game!"
                           )


@commands.command()
async def unregister(ctx: commands.Context, *mentions: str):
    if DataHandler.get('running'):
        await ctx.send(
            "Command failed. Reason: Cannot unregister during a running game!")
        return

    if ctx.author not in server.admin_role.members and len(mentions) > 0:
        await ctx.send("Command failed. Only admins may unregister by mention. Use the command without parameters.")

    members = extract_members_from_args(ctx, *mentions)
    if members is None:
        await ctx.send("Command failed. Invalid mention.")
        return

    for member in members:
        if server.registered_role not in member.roles:
            await ctx.send(f"{member.mention} wasn't registered!")
        else:
            await member.remove_roles(server.registered_role)
            await ctx.send(
                f"{member.mention} has unregistered from playing the game!")


@commands.command()
@role_required("admin")
async def start(ctx: commands.Context):
    if DataHandler.get('running'):
        await ctx.send("Command failed. Game is already running!")
        return

    locations: list[str] = DataHandler.get("locations")
    weapons: list[str] = DataHandler.get("weapons")
    if len(server.registered_role.members) <= 1:
        await ctx.send("There aren't enough players! :(")
        return
    if len(locations) < 1:
        await ctx.send("There aren't enough locations! :(")
        return
    if len(weapons) < 1:
        await ctx.send("There aren't enough weapons! :(")
        return

    players: list[int] = []
    for memb in ctx.guild.members:
        if memb.bot:
            continue
        if server.registered_role in memb.roles:
            await memb.remove_roles(server.registered_role)
            await memb.add_roles(server.alive_role)
            players.append(memb.id)

            tc = await server.private_category.create_text_channel(str(memb.id))
            await tc.set_permissions(memb, view_channel=True)

    DataHandler.set('running', True)
    DataHandler.set('players', [])
    await server.refresh()
    await ctx.send("Game started!")


@commands.command()
@role_required("admin")
async def end(ctx: commands.Context):
    if not DataHandler.get('running'):
        await ctx.send("Command failed. Reason: Game isn't running!")
        return

    for memb in ctx.guild.members:
        await memb.remove_roles(server.alive_role, server.dead_role)

    if server.private_category:
        for channel in server.private_category.channels:
            await channel.delete()

    DataHandler.set('running', False)
    DataHandler.set('players', [])
    await server.refresh()
    await ctx.send("Game ended!")


@commands.command()
@role_required("admin")
async def nextday(ctx: commands.Context):
    pass


@commands.command()
@role_required("admin")
async def revive(ctx: commands.Context, *mentions: str):
    if not DataHandler.get('running'):
        await ctx.send("Command failed. Game isn't running!")
        return
    members = extract_members_from_args(ctx, *mentions)

    if members is None:
        await ctx.send("Command failed. Invalid mention!")
        return

    for member in members:
        if server.dead_role not in member.roles:
            await ctx.send(f"{member.mention} is already alive!")
            return
        else:
            await member.add_roles(server.alive_role)
            await member.remove_roles(server.dead_role)
            await ctx.send(f"{member.mention} has been revived!")
    await server.refresh()


@commands.command()
@role_required("admin")
async def kill(ctx: commands.Context, *mentions: str):
    if not DataHandler.get('running'):
        await ctx.send("Command failed. Game isn't running!")
        return
    members = extract_members_from_args(ctx, *mentions)

    if members is None:
        await ctx.send("Command failed. Invalid mention!")
        return

    for member in members:
        if server.alive_role not in member.roles:
            await ctx.send(f"{member.mention} is already dead!")
            return
        else:
            await member.add_roles(server.dead_role)
            await member.remove_roles(server.alive_role)
            await server.notify_of_death(member)
            await ctx.send(f"{member.mention} has been killed!")
    await server.refresh()


@commands.command()
@role_required("admin")
async def introduce(ctx: commands.Context, *mentions: str):
    if not DataHandler.get('running'):
        await ctx.send("Command failed. Game isn't running!")
        return

    members = extract_members_from_args(ctx, *mentions)

    if members is None:
        await ctx.send("Command failed. Invalid mention!")
        return

    for member in members:
        if server.alive_role in member.roles or server.dead_role in member.roles:
            await ctx.send(f"{member.mention} is already in the game!")
        else:
            await member.add_roles(server.alive_role)
            await ctx.send(f"{member.mention} has been added to the game!")
    await server.refresh()


@commands.command()
@role_required("admin")
async def remove(ctx: commands.Context, *mentions: str):
    if not DataHandler.get('running'):
        await ctx.send("Command failed. Reason: Game isn't running!")
        return

    members = extract_members_from_args(ctx, *mentions)

    if members is None:
        await ctx.send("Command failed. Invalid mention!")
        return

    for member in members:
        if server.alive_role not in member.roles and server.dead_role not in member.roles:
            await ctx.send(f"{member.mention} isn't in the game!")
        else:
            await member.remove_roles(server.alive_role, server.dead_role)

            await ctx.send(f"{member.mention} has been removed from the game!")
    await server.refresh()