import discord
import credentials

from pixiv_module import PixivModule

cred = credentials.Credentials('settings.cfg')

TOKEN           = cred.get_item('DEFAULT', 'discord_token')
cmd_pref        = cred.get_item('DEFAULT', 'command_prefix')
pixiv_username  = cred.get_item('DEFAULT', 'pixiv_username')
pixiv_password  = cred.get_item('DEFAULT', 'pixiv_password')
pixiv_refresh   = cred.get_refresh_token()


# create PixivModule
pixiv = PixivModule(pixiv_username, pixiv_password,
                    cred.write_refresh_token, refresh_token=pixiv_refresh)












"""
from discord.ext import commands

bot = commands.Bot(command_prefix=cmd_pref)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to discord.")


@bot.command(name='test', help="A test response.")
async def test_response(ctx):
    await ctx.send("Test Response.")



@bot.command(name='test2')
async def test_response(ctx, a: int, b: int):
    await ctx.send(str(a+b))



# Starting Discord Bot
bot.run(TOKEN)
"""
