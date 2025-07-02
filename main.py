import discord
from discord.ext import commands
from discord import app_commands
import os
from discord.ui import Button, View
from config import *
import aiohttp  # Add this import

# Create the bot instance
intents = discord.Intents.default()
intents.message_content = True  # Needed for receiving messages
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Sync slash commands on bot startup
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    # # Set animated avatar from URL
    # avatar_url = "https://cdn.pfps.gg/pfps/9367-i-am-confused.gif"  # Replace with your GIF URL
    # try:
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(avatar_url) as resp:
    #             if resp.status == 200:
    #                 avatar_bytes = await resp.read()
    #                 await bot.user.edit(avatar=avatar_bytes)
    #                 print("Successfully changed your server avatar.")
    #             else:
    #                 print(f"Failed to fetch avatar from URL. Status: {resp.status}")
    # except Exception as error:
    #     print(f"Oh, something went wrong: {error}")

    # Dynamically load cogs from the cogs directory
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(cog_name)
                print(f'Loaded cog: {cog_name}')
            except Exception as e:
                print(f'Failed to load cog {cog_name}: {e}')

    # Sync slash commands
    await bot.tree.sync()
    print("Slash commands synced successfully!")

    # Set bot presence
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=f"prefix: {PREFIX[0]}")
    )

# Sync slash commands after cog actions
async def sync_commands(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("Slash commands synced successfully!")
    except Exception as e:
        await ctx.send(f"Failed to sync slash commands. Error: {e}")

# Command to load a cog
@bot.command(name='load')
@commands.is_owner()
async def load_cog(ctx, cog: str):
    """Load a cog."""
    try:
        await bot.load_extension(f'cogs.{cog}')
        await ctx.send(f'Cog {cog} loaded successfully!')
        await sync_commands(ctx)  # Sync slash commands after loading a cog
    except Exception as e:
        await ctx.send(f'Failed to load cog {cog}. Error: {e}')

# Command to unload a cog
@bot.command(name='unload')
@commands.is_owner()
async def unload_cog(ctx, cog: str):
    """Unload a cog."""
    try:
        await bot.unload_extension(f'cogs.{cog}')
        await ctx.send(f'Cog {cog} unloaded successfully!')
        await sync_commands(ctx)  # Sync slash commands after unloading a cog
    except Exception as e:
        await ctx.send(f'Failed to unload cog {cog}. Error: {e}')

# Command to reload a cog
@bot.command(name='reload')
@commands.is_owner()
async def reload_cog(ctx, cog: str):
    """Reload a cog."""
    try:
        await bot.unload_extension(f'cogs.{cog}')
        await bot.load_extension(f'cogs.{cog}')
        await ctx.send(f'Cog {cog} reloaded successfully!')
        await sync_commands(ctx)  # Sync slash commands after reloading a cog
    except Exception as e:
        await ctx.send(f'Failed to reload cog {cog}. Error: {e}')



# Command to switch cogs
@bot.command(name='switch')
@commands.is_owner()
async def switch_cogs(ctx, cog_to_unload: str, cog_to_load: str):
    """Switch cogs by unloading one and loading another."""
    try:
        # Unload the specified cog
        await bot.unload_extension(f'cogs.{cog_to_unload}')
        await ctx.send(f'Cog {cog_to_unload} unloaded successfully!')
        
        # Load the new cog
        await bot.load_extension(f'cogs.{cog_to_load}')
        await ctx.send(f'Cog {cog_to_load} loaded successfully!')
        
        # Sync commands
        await sync_commands(ctx)
    except Exception as e:
        await ctx.send(f'Failed to switch cogs. Error: {e}')


# Handle command errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Create a button to list commands
        list_commands_button = Button(label="List Commands", style=discord.ButtonStyle.primary)

        async def list_commands_callback(interaction):
            await ctx.invoke(ctx.bot.get_cog('Info').listcommands)
            await interaction.message.edit(view=None)

        list_commands_button.callback = list_commands_callback

        # Create a view and add the button
        view = View()
        view.add_item(list_commands_button)

        # Error embed
        embed = discord.Embed(
            title="Error 69: Invalid Command",
            description="",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=view)



# Define a ping command
@bot.command(name='ping')
async def ping(ctx):
    """Respond with the bot's latency."""
    latency = round(bot.latency * 1000)  # Convert to milliseconds
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)




# Run the bot with your token
bot.run(BOT_TOKEN)
