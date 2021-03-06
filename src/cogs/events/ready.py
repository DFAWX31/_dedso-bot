from discord.ext import commands

from database.create import create


class ReadyEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"logged in as { self.bot.user }")
        ctf_table, ctf_teams = create()

        if ctf_table is not None and ctf_teams is not None:
            print("Succesfully connected to the database")


def setup(bot):
    bot.add_cog(ReadyEvent(bot))
