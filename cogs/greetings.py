import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command('namaste')
    async def namaste(self, ctx):
        await ctx.message.add_reaction("🙏")
        await ctx.send(f'Namaste {ctx.author.display_name} 🙏')

    @commands.command('aich')
    async def aich(self, ctx):
        await ctx.message.add_reaction("🥵")
        await ctx.send(f'Aich k ho k ho {ctx.author.display_name} 😏')


    @commands.command(name='hello', aliases=['Hello', 'HELLO'])
    async def hello(self, ctx):
        await ctx.message.add_reaction("👋")
        await ctx.send(f'Hello {ctx.author.display_name} 👋')

    @commands.command(name='hola', aliases=['Hola', 'HOLA'])
    async def hola(self, ctx):
        await ctx.message.add_reaction("💃")
        await ctx.send(f'¡Hola {ctx.author.display_name}! 💃')

    @commands.command(name='bonjour', aliases=['Bonjour', 'BONJOUR'])
    async def bonjour(self, ctx):
        await ctx.message.add_reaction("🥖")
        await ctx.send(f'Bonjour {ctx.author.display_name} 🥖')

    @commands.command(name='ciao', aliases=['Ciao', 'CIAO'])
    async def ciao(self, ctx):
        await ctx.message.add_reaction("🤌")
        await ctx.send(f'Ciao {ctx.author.display_name} 🤌')

    @commands.command(name='konnichiwa', aliases=['Konnichiwa', 'KONNICHIWA'])
    async def konnichiwa(self, ctx):
        await ctx.message.add_reaction("🎌")
        await ctx.send(f'こんにちは {ctx.author.display_name} 🎌')

    @commands.command(name='nihao', aliases=['Nihao', 'NIHAO'])
    async def nihao(self, ctx):
        await ctx.message.add_reaction("🏮")
        await ctx.send(f'你好 {ctx.author.display_name} 🏮')

    @commands.command(name='annyeong', aliases=['Annyeong', 'ANNYEONG'])
    async def annyeong(self, ctx):
        await ctx.message.add_reaction("🇰🇷")
        await ctx.send(f'안녕하세요 {ctx.author.display_name} 🇰🇷')

    @commands.command(name='salaam', aliases=['Salaam', 'SALAAM'])
    async def salaam(self, ctx):
        await ctx.message.add_reaction("☪️")
        await ctx.send(f'السلام عليكم {ctx.author.display_name} ☪️')

    @commands.command(name='shalom', aliases=['Shalom', 'SHALOM'])
    async def shalom(self, ctx):
        await ctx.message.add_reaction("✡️")
        await ctx.send(f'שלום {ctx.author.display_name} ✡️')
        
    @commands.command(name='aloha', aliases=['Aloha', 'ALOHA'])
    async def aloha(self, ctx):
        await ctx.message.add_reaction("🌺")
        await ctx.send(f'Aloha {ctx.author.display_name} 🌺')
        
    @commands.command(name='guten', aliases=['Guten', 'GUTEN'])
    async def guten(self, ctx):
        await ctx.message.add_reaction("🍺")
        await ctx.send(f'Guten Tag {ctx.author.display_name} 🍺')
        
    @commands.command(name='sawadee', aliases=['Sawadee', 'SAWADEE'])
    async def sawadee(self, ctx):
        await ctx.message.add_reaction("🙏")
        await ctx.send(f'สวัสดี {ctx.author.display_name} 🙏')

    @commands.command(name='sup')
    async def k_chha(self, ctx):
        await ctx.message.add_reaction("👍")
        await ctx.send(f'Sup {ctx.author.display_name}!')

async def setup(bot):
    await bot.add_cog(General(bot))