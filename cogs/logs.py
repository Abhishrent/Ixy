import discord
from discord.ext import commands
from config import LOG_CHANNEL_ID

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, *, title=None, description=None, fields=None, color=discord.Color.dark_embed()):
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color)
            if fields:
                for name, value in fields:
                    embed.add_field(name=name, value=value, inline=True)
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.send_log(
            message.guild,
            title="Message",
            description=None,
            fields=[
                ("User", message.author.mention),
                ("Channel", message.channel.mention),
                ("Content", message.content or "*No content*")
            ],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        await self.send_log(
            before.guild,
            title="Edit",
            description=None,
            fields=[
                ("User", before.author.mention),
                ("Channel", before.channel.mention),
                ("Before", before.content or "*No content*"),
                ("After", after.content or "*No content*")
            ],
            color=discord.Color.orange()
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        await self.send_log(
            message.guild,
            title="Delete",
            description=None,
            fields=[
                ("User", message.author.mention),
                ("Channel", message.channel.mention),
                ("Content", message.content or "*No content*")
            ],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        await self.send_log(
            reaction.message.guild,
            title="Reaction +",
            description=None,
            fields=[
                ("User", user.mention),
                ("Emoji", str(reaction.emoji)),
                ("Channel", reaction.message.channel.mention)
            ],
            color=discord.Color.blurple()
        )

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        await self.send_log(
            reaction.message.guild,
            title="Reaction -",
            description=None,
            fields=[
                ("User", user.mention),
                ("Emoji", str(reaction.emoji)),
                ("Channel", reaction.message.channel.mention)
            ],
            color=discord.Color.blurple()
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(
            member.guild,
            title="Join",
            description=None,
            fields=[("User", member.mention)],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            member.guild,
            title="Leave",
            description=None,
            fields=[("User", member.mention)],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        fields = []
        if before.nick != after.nick:
            fields.append(("Nick", f"{before.nick} → {after.nick}"))
        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                fields.append(("+Roles", ", ".join(r.name for r in added)))
            if removed:
                fields.append(("-Roles", ", ".join(r.name for r in removed)))
        if fields:
            fields.insert(0, ("User", after.mention))
            await self.send_log(
                after.guild,
                title="Member Update",
                description=None,
                fields=fields,
                color=discord.Color.gold()
            )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.send_log(
            role.guild,
            title="Role +",
            description=None,
            fields=[("Role", role.name)],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.send_log(
            role.guild,
            title="Role -",
            description=None,
            fields=[("Role", role.name)],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        await self.send_log(
            after.guild,
            title="Role Update",
            description=None,
            fields=[
                ("Before", before.name),
                ("After", after.name)
            ],
            color=discord.Color.gold()
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log(
            channel.guild,
            title="Channel +",
            description=None,
            fields=[
                ("Name", channel.name),
                ("Type", str(channel.type))
            ],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log(
            channel.guild,
            title="Channel -",
            description=None,
            fields=[
                ("Name", channel.name),
                ("Type", str(channel.type))
            ],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.send_log(
            after.guild,
            title="Channel Update",
            description=None,
            fields=[
                ("Before", before.name),
                ("After", after.name)
            ],
            color=discord.Color.gold()
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(
            guild,
            title="Ban",
            description=None,
            fields=[("User", user.mention)],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log(
            guild,
            title="Unban",
            description=None,
            fields=[("User", user.mention)],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        fields = []
        if before.channel != after.channel:
            fields.append(("Channel", f"{before.channel} → {after.channel}"))
        if before.self_mute != after.self_mute:
            fields.append(("Self Mute", f"{before.self_mute} → {after.self_mute}"))
        if before.self_deaf != after.self_deaf:
            fields.append(("Self Deaf", f"{before.self_deaf} → {after.self_deaf}"))
        if fields:
            fields.insert(0, ("User", member.mention))
            await self.send_log(
                member.guild,
                title="Voice Update",
                description=None,
                fields=fields,
                color=discord.Color.blurple()
            )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.send_log(
            invite.guild,
            title="Invite +",
            description=None,
            fields=[
                ("By", invite.inviter.mention if invite.inviter else "Unknown"),
                ("URL", invite.url)
            ],
            color=discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.send_log(
            invite.guild,
            title="Invite -",
            description=None,
            fields=[("URL", invite.url)],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.send_log(
            channel.guild,
            title="Webhooks Update",
            description=None,
            fields=[("Channel", channel.mention)],
            color=discord.Color.gold()
        )

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        await self.send_log(
            after,
            title="Guild Update",
            description=None,
            fields=[
                ("Before", before.name),
                ("After", after.name)
            ],
            color=discord.Color.gold()
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        fields = [("User", ctx.author.mention), ("Command", str(ctx.command))]
        if ctx.message.content:
            fields.append(("Content", ctx.message.content))
        await self.send_log(
            ctx.guild,
            title="Command",
            description=None,
            fields=fields,
            color=discord.Color.blurple()
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self.send_log(
            ctx.guild,
            title="Command Error",
            description=None,
            fields=[
                ("User", ctx.author.mention),
                ("Command", str(ctx.command)),
                ("Error", str(error))
            ],
            color=discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_application_command(self, interaction):
        # Log slash command usage
        if not interaction.guild or not interaction.user:
            return
        fields = [
            ("User", interaction.user.mention),
            ("Command", interaction.command.qualified_name if interaction.command else "Unknown"),
        ]
        if interaction.data and "options" in interaction.data:
            options = interaction.data["options"]
            if options:
                opts_str = ", ".join(f"{opt['name']}: {opt.get('value', '')}" for opt in options)
                fields.append(("Options", opts_str))
        await self.send_log(
            interaction.guild,
            title="Slash Command",
            description=None,
            fields=fields,
            color=discord.Color.blurple()
        )

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        # Log slash command completion (for hybrid and app commands)
        if not interaction.guild or not interaction.user:
            return
        fields = [
            ("User", interaction.user.mention),
            ("Command", command.qualified_name if hasattr(command, "qualified_name") else str(command)),
        ]
        if interaction.data and "options" in interaction.data:
            options = interaction.data["options"]
            if options:
                opts_str = ", ".join(f"{opt['name']}: {opt.get('value', '')}" for opt in options)
                fields.append(("Options", opts_str))
        await self.send_log(
            interaction.guild,
            title="Slash Command Completion",
            description=None,
            fields=fields,
            color=discord.Color.blurple()
        )

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
