import asyncio

import discord
import sqlalchemy
from discord.ext import bridge, commands

from database.create import connection, ctf_table, ctf_teams


class SelectMenu(discord.ui.Select):
    def __init__(
        self,
        data: list,
        options: list,
        table: sqlalchemy.Table,
        team_name: str,
        leader: str,
        members,
        disabled=False,
    ):
        self.data = data
        self.members = members
        self.leader = leader
        self.table = table
        self.team_name = team_name
        super().__init__(placeholder="Choose a ctf to join", options=options, disabled=disabled)

    async def callback(self, interaction):
        ctf_name = None
        for i in self.data:
            if self.values[0] == str(i[0]):
                ins = self.table.insert().values(
                    name=self.team_name,
                    leader=self.leader,
                    members=self.members,
                    ctf_id=i[0],
                )
                ctf_name = i[1]

                connection.execute(ins)

        await interaction.response.send_message(
            f"succesfully registered {self.team_name} with {interaction.user.mention} as team leader to {ctf_name}"
        )
        await interaction.message.edit(
            view=discord.ui.View(
                SelectMenu(
                    self.data,
                    self.options,
                    self.table,
                    self.team_name,
                    self.leader,
                    self.members,
                    True,
                )
            )
        )


class JoinCTF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command(description="join a ctf with a team or solo")
    async def join(
        self,
        ctx,
        team: discord.Option(str, "your team name"),
        teammates: discord.Option(int, "number of people in the team"),
    ):
        await ctx.response.defer()

        def check(m: discord.Message):
            return m.author == ctx.author and m.mentions[0] is not None

        teams = [ctx.author]

        try:
            for i in range(teammates - 1):
                await ctx.channel.send("Mention your teammate")

                msg = await self.bot.wait_for("message", check=check, timeout=20.0)

                teams.append(msg.mentions[0])
        except asyncio.TimeoutError:
            return await ctx.followup.send("timed out because you were too slow")

        if ctf_table is None:
            return await ctx.respond("failed to get ctf table")

        if ctf_teams is None:
            return await ctx.respond("failed to initialize database")

        res = connection.execute(sqlalchemy.select(ctf_table).where(ctf_table.c.active is True)).fetchall()

        if not res:
            return await ctx.respond("no active ctfs found in the database")

        options = []

        member_ids = [p.id for p in teams]

        if len(res) > 1:
            for i in res:
                j = list(i)

                select = discord.SelectOption(label=str(j[1]), value=str(j[0]), description=str(j[2]))
                options.append(select)

            view = discord.ui.View()
            view.add_item(SelectMenu(res, options, ctf_teams, team, str(ctx.author.id), member_ids))

            return await ctx.channel.send("which ctf do you want to join?", view=view)

        ins = ctf_teams.insert().values(name=team, leader=str(ctx.author.id), members=member_ids, ctf_id=res[0][0])

        connection.execute(ins)

        member = f"{teams[0].mention}"
        for t in range(1, len(teams)):
            member += ", " + teams[t].mention

        await ctx.followup.send(f"team {team} joined with {member} to the ctf {res[0][1]}")


def setup(bot):
    bot.add_cog(JoinCTF(bot))
