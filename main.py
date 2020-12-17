import discord
from discord.ext import commands

import credentials
from pixiv_module import PixivModule
from pixivapi.enums import SearchTarget, Size, ContentType, Sort


cred = credentials.Credentials('settings.cfg')

TOKEN           = cred.get_item('DEFAULT', 'discord_token')
cmd_pref        = cred.get_item('DEFAULT', 'command_prefix')
pixiv_username  = cred.get_item('DEFAULT', 'pixiv_username')
pixiv_password  = cred.get_item('DEFAULT', 'pixiv_password')
pixiv_refresh   = cred.get_refresh_token()


# create PixivModule
pixiv = PixivModule(pixiv_username, pixiv_password,
                    cred.write_refresh_token,
                    refresh_token=pixiv_refresh)


client = commands.Bot(command_prefix=cmd_pref)


@client.event
async def on_ready():
    print(f"{client.user.name} has connected to discord.")



@client.command(name='test')
async def test(ctx):
    await ctx.send("Test Response.")



@client.command(name='search_tag')
async def search_tag(ctx, *, tag:str):

    # Create Message Embed Object
    embed=discord.Embed(title="Search Result Tags",
                        description="Please select the the appropriate tags",
                        color=0xff9214)

    async with ctx.typing():
        tag_result = pixiv.get_client().search_autocomplete(tag)

        if tag_result:
            # Process the tag results
            for index, tag_dict in enumerate(tag_result):
                eng_tag = tag_dict['translated_name']
                jap_tag = tag_dict['name']
                embed.add_field(name=f"{index+1}. {jap_tag}",
                                value=eng_tag,
                                inline=False)

        else:
            embed.description = ""
            embed.add_field(name="No result found",
                                value="Please check the tag again.",
                                inline=False)
            
        
    # Send Embeded Message
    await ctx.send(embed=embed)
        

    
    
"""
@search_tag.error
async def search_tag_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing Arguements.")
"""
















# Starting Discord Bot
client.run(TOKEN)



























