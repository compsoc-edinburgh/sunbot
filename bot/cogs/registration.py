from discord.ext import commands
import discord
import aiohttp
import os

API_SECRET = os.getenv("API_KEY")


class Registration(commands.Cog):
    """Commands !"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = int(os.environ.get("GUILD"))
        self.role_ids = [int(os.environ.get("MEMBER_ROLE"))]
        self.check_in_id = int(os.environ.get("CHECK_IN_MESSAGE"))
        self.guild = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(self.guild_id)
        self.roles = [self.guild.get_role(role) for role in self.role_ids]
        print("[REGISTRATION] Setup Registration check-in")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == self.check_in_id:
            if payload.emoji.name == "HTB":
                await payload.member.send(
                    "Thanks for starting check-in! You'll need an invite code, which you can get from https://register.2021.hacktheburgh.com/hacker/invites. Reply with `!checkin <email> <invite_code>` to confirm your registration. _Note: this must be the email you used to register_"
                )
                print(
                    f"[REGISTRATION] Starting registration for {payload.member.name}#{payload.member.discriminator}"
                )

    @commands.command()
    @commands.dm_only()
    async def checkin(self, ctx, email, code):
        """Checks in hacker registration

        Sends a verification email to the email to a registered hacker

        Parameters
        ----------
        email: email used in registration
        """
        print(email)
        print(code)
        async with aiohttp.ClientSession() as session:
            params = {
                "email": email,
            }
            headers = {
                "Authorization": f"Bearer 0f40b95ce5c946f98425e8abc446899b/{API_SECRET}"
            }

            async with session.get(
                "https://register.2021.hacktheburgh.com/api/v1/applicants/by_email",
                params=params,
                headers=headers,
            ) as resp:
                body = await resp.json()
                if body["ok"]:
                    async with session.get(
                        "https://register.2021.hacktheburgh.com/api/v1/invites/list",
                        params={"id": body["data"]["user_id"]},
                        headers=headers,
                    ) as resp:
                        invites = await resp.json()
                        if body["ok"]:
                            matching_invites = [
                                inv for inv in invites["data"] if inv["code"] == code
                            ]
                            if len(matching_invites) > 0:
                                member = self.guild.get_member(ctx.author.id)
                                await member.add_roles(*self.roles)
                                await ctx.send(
                                    "You're all set! Welcome to Hack the Burgh 2021!"
                                )
                                print(
                                    f"[REGISTRATION] Member {ctx.author.name}#{ctx.author.discriminator} joined as Hacker"
                                )
                            else:
                                raise commands.BadArgument(
                                    message="That didn't work! Make sure you're using a valid invite code"
                                )
                        else:
                            raise commands.BadArgument(
                                message="That didn't work! Make sure you're using a valid invite code"
                            )

                else:
                    if "<" in email:
                        print(
                            f"[REGISTRATION] {ctx.author.name}#{ctx.author.discriminator} doesn't know how to use angle brackets"
                        )
                        raise commands.BadArgument(
                            message="Please remove the angle brackets `<`,`>` from your command."
                        )
                    print(
                        f"[REGISTRATION] Unable to find registration for {ctx.author.name}#{ctx.author.discriminator}"
                    )
                    raise commands.BadArgument(
                        message="That didn't work! Make sure you used the same email as you used to register."
                    )

    @checkin.error
    async def checkin_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "email":
                await ctx.send("You need to specify an email: `!checkin <email>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        else:
            print("[REGISTRATION] ERROR")
            print(error)


def setup(bot):
    bot.add_cog(Registration(bot))
