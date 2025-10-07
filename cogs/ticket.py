import discord, asyncio
from discord.ext import commands
from config import PREFIX, EMBED_THUMBNAIL

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='open', description="Open a support ticket")
    async def open_ticket(self, ctx):
        # Define guild roles
        guild = ctx.guild
        mod_role = discord.utils.get(guild.roles, name="Organizing Committee")
        everyone_role = guild.default_role

        # Checks if the user already has an open ticket channel
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{ctx.author.name}")
        if existing_channel:
            embed = discord.Embed(
                title="Ticket Already Open",
                description=f"You already have a ticket open: {existing_channel.mention}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await ctx.send(embed=embed)
            return

        # Ensure the "Tickets" category exists or create it
        tickets_category = discord.utils.get(guild.categories, name="Tickets")
        if tickets_category is None:
            tickets_category = await guild.create_category("Tickets")

        # Creates a new private channel for the user and mods
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            category=tickets_category,
            overwrites={
                everyone_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            },
            topic=str(ctx.author.id)  # Store opener's user ID in the topic
        )

        # Confirmation embed in the channel where the command was used
        embed = discord.Embed(
            title="Ticket Created",
            description=f"Your ticket has been created: {ticket_channel.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

        # Instructional embed in the ticket channel, with pings
        ticket_embed = discord.Embed(
            title="Welcome to Your Support Ticket",
            description=(
                f"{ctx.author.mention}, this channel is dedicated for your support.\n\n"
                "Please provide a brief description of your issue, and the <@&1130051976189722680> will respond shortly.\n\n"
                f"Type `{PREFIX[0]}close` or `/close` to close this ticket when your issue is resolved."
            ),
            color=discord.Color.blue()
        )
        ticket_embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ticket_channel.send(
            content=f"{ctx.author.mention} <@&1130051976189722680>",
            embed=ticket_embed
        )

    @commands.hybrid_command(name='close', description="Close your open ticket")
    async def close_ticket(self, ctx, *, mod_message: str = None):
        if "ticket" in ctx.channel.name:
            # Get the opener's user ID from the channel topic
            opener_id = None
            if ctx.channel.topic and ctx.channel.topic.isdigit():
                opener_id = int(ctx.channel.topic)
            opener = None
            if opener_id:
                opener = await self.bot.fetch_user(opener_id)
            closing_embed = discord.Embed(
                title="Closing Ticket",
                description="This ticket will be closed in [5] second(s).",
                color=discord.Color.orange()
            )
            closing_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            closing_message = await ctx.send(embed=closing_embed)
            for i in range(5, 0, -1):
                await asyncio.sleep(1)
                closing_embed.description = f"This ticket will be closed in [{i}] second(s)."
                await closing_message.edit(embed=closing_embed)
            await ctx.channel.delete()
            # DM the opener if found, else fallback to the command user
            embed = discord.Embed(
                title="Ticket Closed",
                description="Your ticket has been closed. If you need further assistance, feel free to open another ticket!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            if mod_message:
                embed.add_field(name="Message from the OCs", value=mod_message, inline=False)
            if opener:
                await opener.send(embed=embed)
            else:
                await ctx.author.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Invalid Channel",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
