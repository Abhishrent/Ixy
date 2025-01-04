import discord, asyncio
from discord.ext import commands
from config import PREFIX


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='ujuri', description="Open a support ticket")
    async def open_ticket(self, ctx):
        # Define guild roles
        guild = ctx.guild
        mod_role = discord.utils.get(guild.roles, name="mods")
        everyone_role = guild.default_role

        # Checks if the user already has an open ticket channel
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{ctx.author.name}")
        if existing_channel:
            await ctx.send(f"You already have a ticket open: {existing_channel.mention}")
            return

        # Creates a new private channel for the user and mods
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            category=discord.utils.get(guild.categories, name="Tickets"),
            overwrites={
                everyone_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )

        await ctx.send("Ticket created! Check your ticket channel.")
        await ticket_channel.send(f"Hello {ctx.author.mention}! This channel is dedicated to assisting you. Please provide a brief description of your issue, and our support team will respond shortly. \n\n`(Type '{PREFIX[0]} bhayo' in case you change your mind or would like to close this request.)`")

    @commands.hybrid_command(name='bhayo', description="Close your open ticket")
    async def close_ticket(self, ctx):
        if "ticket" in ctx.channel.name:
            closing_message = await ctx.send("This ticket will be closed in [5] second(s).")
            for i in range(5, 0, -1):
                await asyncio.sleep(1) 
                await closing_message.edit(content=f"This ticket will be closed in [{i}] second(s)")
            await ctx.channel.delete()
            await ctx.author.send("Your ticket has been closed. If you need further assistance, feel free to open another ticket!")
        else:
            await ctx.send("This command can only be used in a ticket channel.")


async def setup(bot):
    await bot.add_cog(Support(bot))
