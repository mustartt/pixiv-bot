import discord
from discord.ext import commands

import credentials
from pixiv_module import PixivModule
from pixivapi.enums import SearchTarget, Size, ContentType, Sort
from pixivapi.models import Illustration

from typing import List, Tuple, Dict

import io
import asyncio
import random
import re
from Levenshtein import ratio


cred = credentials.Credentials('settings.cfg')

TOKEN           = cred.get_item('DEFAULT', 'discord_token')
cmd_pref        = cred.get_item('DEFAULT', 'command_prefix')
pixiv_username  = cred.get_item('DEFAULT', 'pixiv_username')
pixiv_password  = cred.get_item('DEFAULT', 'pixiv_password')
pixiv_refresh   = cred.get_refresh_token()


# create PixivModule
pixiv = PixivModule(pixiv_username, pixiv_password,
                    cred.write_refresh_token,
                    refresh_token=pixiv_refresh).get_client()


client = commands.Bot(command_prefix=cmd_pref)


@client.event
async def on_ready():
    print(f"{client.user.name} has connected to discord.")



@client.command(name='test')
async def test(ctx, *, query):
    await ctx.send('test')

    

        

@client.command(name='search')
async def search(ctx, *, query: str):

    #trigger typing
    await ctx.trigger_typing()
    
    def find_best_tag(query: str, query_item: Dict[str, str]) -> str:
        def calc_max_ratio(query: str, query_item: Dict[str, str]) -> Tuple[float, float]:
            eng_tag = query_item['translated_name']
            jap_tag = query_item['name']

            eng_ratio = ratio(query.lower(), str(eng_tag).lower())
            jap_ratio = ratio(query.lower(), str(jap_tag).lower())

            return max(eng_ratio, jap_ratio)

        best_item = max(tag_suggestions, key=lambda x: calc_max_ratio(query, x))
        return best_item['name']
    
    
    tag_list = query.split(',')
    tag_result = []

    for tag in tag_list:
        tag_suggestions = pixiv.search_autocomplete(tag.strip())

        # create query for only valid tags
        if tag_suggestions:      
            best = find_best_tag(tag, tag_suggestions)
            tag_result.append(best)

    compiled_query = ' '.join(tag_result)
    query_display = ' '.join(map(lambda x: f'`#{x}`', tag_result))

    #DEBUG: await ctx.send(f'```{compiled_query}```')

    # get illustrations
    # TODO: Change to pixiv.search_popular() 
    res = pixiv.search_popular_preview(compiled_query)
    illusts = res['illustrations'] # array of Illustrations

    curr_page = 0
    pages_total = len(illusts)

    # create gallery embed
    preview = pixiv.get_illust_byte_streams(illusts[curr_page])[0]

    embed, file = create_embed_file('Search Results',
                                    f'tags: {query_display}',
                                    illusts[curr_page].id,
                                    preview)
    embed.set_footer(text=f'Page {curr_page+1}/{pages_total} id: {illusts[curr_page].id}')
    
    message = await ctx.send(embed=embed, file=file)

    # add reactions
    await message.add_reaction(LEFT_ARROW)
    await message.add_reaction(RIGHT_ARROW)
    await message.add_reaction(HEART)


    # implements the reaction to controls
    def check(reaction, user):
        return not user.bot and reaction.message == message
    
    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=TIMEOUT,
                                                   check=check)
            if reaction.emoji == LEFT_ARROW and pages_total > 1:
                #trigger typing
                await ctx.trigger_typing()
                
                # calc new page
                curr_page = curr_page - 1
                if curr_page < 0:
                    curr_page = pages_total - 1

                # edit gallery embed
                preview = pixiv.get_illust_byte_streams(illusts[curr_page])[0]

                embed, file = create_embed_file('Search Results',
                                                f'tags: {query_display}',
                                                illusts[curr_page].id,
                                                preview)
                embed.set_footer(text=f'Page {curr_page+1}/{pages_total} id: {illusts[curr_page].id}')

                await message.delete()
                message = await ctx.send(embed=embed, file=file)

                # add reactions
                await message.add_reaction(LEFT_ARROW)
                await message.add_reaction(RIGHT_ARROW)
                await message.add_reaction(HEART)
                
                
            if reaction.emoji == RIGHT_ARROW and pages_total > 1:
                #trigger typing
                await ctx.trigger_typing()
                
                # calc new page
                curr_page = (curr_page + 1) % pages_total

                # edit gallery embed
                preview = pixiv.get_illust_byte_streams(illusts[curr_page])[0]

                embed, file = create_embed_file('Search Results for',
                                                f'tags: {query_display}',
                                                illusts[curr_page].id,
                                                preview)
                embed.set_footer(text=f'Page {curr_page+1}/{pages_total} id: {illusts[curr_page].id}')

                await message.delete()
                message = await ctx.send(embed=embed, file=file)

                # add reactions
                await message.add_reaction(LEFT_ARROW)
                await message.add_reaction(RIGHT_ARROW)
                await message.add_reaction(HEART)


            if reaction.emoji == HEART:
                #trigger typing
                await ctx.trigger_typing()
                await ctx.invoke(client.get_command('search_related'),
                                 illust_id=illusts[curr_page].id)
            
        except asyncio.TimeoutError:
            break
        except Exception as err:
            print("Something else went wrong")
            print(err)
            break
            
    

    

    
    
    
        
        
    
        


    

@client.command(name='get_tag_popular_result')
async def get_tag_popular_result(ctx, *, query: str):

    res = pixiv.search_popular_preview(query)

    content = ""

    for illust in res['illustrations']:
        content += f'{illust.id} -> {illust.title} {illust.total_bookmarks}' + '\n'

    await ctx.send(f'```{content}```')


#FIRST_CAPTURE = 10

@client.command(name='search_related')
async def search_related(ctx, illust_id:int, number=3):
    
    #trigger typing
    await ctx.trigger_typing()

    # query related images
    res = pixiv.fetch_illustration_related(illust_id)
    related = res['illustrations']

    """
    sorted(res['illustrations'][:FIRST_CAPTURE],
                     key=lambda work: work.total_bookmarks,
                     reverse=True)
    """

    # check if query is empty
    if not related:
        await ctx.send("No result found.")
        return
    

    # send number of images as gallery
    await asyncio.wait([
        ctx.invoke(client.get_command('create_gallery'),
                   illust_id=illust.id)
        for illust in related[:number]
        ])







@client.command(name='search_tag')
async def search_tag(ctx, *, tag:str):

    # Create Message Embed Object
    embed=discord.Embed(title="Search Result Tags",
                        description="Please select the the appropriate tags",
                        color=0xff9214)
    
    async with ctx.typing():
        tag_result = pixiv.search_autocomplete(tag)

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

TIMEOUT = 30.0

LEFT_ARROW = '\u2B05'
RIGHT_ARROW = '\u27A1'
HEART = "\u2764"

def create_embed_file(title: str,
                      description: str,
                      image_name:str,
                      file_stream: io.BytesIO) -> Tuple[discord.Embed, discord.File]:
    """
    Creates a discord.Embed with title, description, image_name, and the image's
    BytesIO Stream. To produce a tuple (discord.Embed, discord.File) 
    """
    caption = re.sub('<[^<]+?>', '', description)
    caption = re.sub('http\S+', '', caption)
    embed = discord.Embed(title=title, description=caption)
    embed.set_image(url=f"attachment://{image_name}.jpg")

    # reset image byte stream back to 0
    file_stream.seek(0)
    file = discord.File(fp=file_stream, filename=f"{image_name}.jpg")

    return (embed, file)



@client.command(name='create_gallery')
async def create_gallery(ctx, illust_id:int):
    """
    TODO: Attempts to open file in image_cache
           - if does not exists, download the images
           - if images has multiple panels download as id_p{panel_number}.{ext}
          After react period expires after 30 seconds, images are optionally purged
     - preview images uses Size.LARGE (for now)
    """

    #trigger typing
    await ctx.trigger_typing()

    illust = pixiv.fetch_illustration(illust_id)
    image_binaries = pixiv.get_illust_byte_streams(illust)

    pages_total = len(image_binaries)
    curr_page = 0 # index starts at 0 -> display + 1




    # multi page illustration
    embed, file = create_embed_file(illust.title,
                                    illust.caption,
                                    f"{illust.id}_p{curr_page}",
                                    image_binaries[curr_page])
    embed.set_footer(text=f'Page Index {curr_page+1}/{pages_total}  id: {illust.id}')
    message = await ctx.send(file=file, embed=embed)

    # add reaction emojis
    await message.add_reaction(LEFT_ARROW)
    await message.add_reaction(RIGHT_ARROW)
    await message.add_reaction(HEART)

    # implements the reaction to controls

    def check(reaction, user):
        return not user.bot and reaction.message == message
    
    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=TIMEOUT,
                                                   check=check)
            if reaction.emoji == LEFT_ARROW and pages_total > 1:
                # calc new page
                curr_page = curr_page - 1
                if curr_page < 0:
                    curr_page = pages_total - 1
                
                # edit current embed
                embed, file = create_embed_file(illust.title,
                                    illust.caption,
                                    f"{illust.id}_p{curr_page}",
                                    image_binaries[curr_page])
                embed.set_footer(text=f'Page Index {curr_page+1}/{pages_total} id: {illust.id}')

                # resend message
                await message.delete()
                message = await ctx.send(file=file, embed=embed)

                # add reaction emojis
                await message.add_reaction(LEFT_ARROW)
                await message.add_reaction(RIGHT_ARROW)
                await message.add_reaction(HEART)


            if reaction.emoji == RIGHT_ARROW and pages_total > 1:
                # calc new page
                curr_page = (curr_page + 1) % pages_total

                # edit current embed
                embed, file = create_embed_file(illust.title,
                                    illust.caption,
                                    f"{illust.id}_p{curr_page}",
                                    image_binaries[curr_page])
                embed.set_footer(text=f'Page Index {curr_page+1}/{pages_total} id: {illust.id}')

                # resend message
                await message.delete()
                message = await ctx.send(file=file, embed=embed)

                # add reaction emojis
                await message.add_reaction(LEFT_ARROW)
                await message.add_reaction(RIGHT_ARROW)
                await message.add_reaction(HEART)

            if reaction.emoji == HEART:
                await ctx.invoke(client.get_command('search_related'),
                                 illust_id=illust.id)
            
        except asyncio.TimeoutError:
            break
        except Exception as err:
            print("Something else went wrong")
            print(err)
            break

            
















# Starting Discord Bot
client.run(TOKEN)



























