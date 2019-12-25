import logging
from datetime import timedelta

import discord
from discord.ext import commands
from chatterbot.conversation import Statement


# Set up logging
logger = logging.getLogger(__name__)


class Summon:
    def __init__(self, channel, cmd, resp):
        """
        A summoning to a channel.

        :param channel: The channel the bot has been summoned to.
        :param cmd: The user's command message.
        :param resp: The "summoned" response to the command.
        """

        self.channel = channel
        self.cmd = cmd
        self.resp = resp


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.summons = dict()

    @commands.command()
    async def summon(self, ctx):
        """Summon the bot to listen to this channel."""

        # Respond to the command
        resp = await ctx.send(embed=discord.Embed(
            title='Summon frame opened',
            description='I am now responding to messages in this channel.',
            colour=discord.Colour.green()
        ))

        # Store the summoning
        self.summons[ctx.channel.id] = Summon(
            ctx.channel,
            ctx.message,
            resp
        )

    @commands.command()
    async def unsummon(self, ctx):
        """Stop listening to this channel."""

        # Unsummon
        self.summons[ctx.channel.id] = None

        # Respond to the command
        resp = await ctx.send(embed=discord.Embed(
            title='Summon frame closed',
            description='I am no longer responding to messages in this channel.',
            colour=discord.Colour.red()
        ))

    @commands.Cog.listener()
    async def on_message(self, msg):
        """
        Process a message and send a chatbot response to the channel.

        If the bot doesn't understand, no message will be sent.
        """

        logger.info('Received message "%s"', msg.clean_content)

        # Check if the author is a bot / system message
        if msg.author.bot or msg.type != discord.MessageType.default:
            logger.info('Author is a bot, ignoring')
            return

        # Check if this channel is active
        # TODO: Close summon frame after 5 minutes of inactivity
        if not self.active_for(msg):
            logger.info('Channel is inactive, ignoring')
            return

        # Trigger a typing indicator while chatterbot processes
        await msg.channel.trigger_typing()

        # Build query statement
        statement = await self.query_statement(msg)

        # Get a response
        logger.info('Getting response')
        response = self.bot.chatter.get_response(statement)

        # Send response to channel
        if response.text == '':
            logger.info('Bot did not understand, not sending anything.')
        else:
            logger.info('Sending response to channel')
            await msg.channel.send(response.text)

    def active_for(self, msg):
        """Check if the bot should respond to the given message."""

        # Find the channel's Summon object
        summon = self.summons.get(msg.channel.id)

        if summon is None:
            # Not summoned
            return False

        # Check if the message is after the summon frame opened
        return msg.created_at > summon.resp.created_at

    async def query_statement(self, msg):
        """Build a Statement from the user's message."""

        logger.info('Building query statement')

        # Get previous message
        prev = await self.get_previous(msg)

        return Statement(
            # Use message contents for statement text
            msg.clean_content,
            in_response_to=prev,
            # Use Discord IDs for conversation and person
            conversation=msg.channel.id,
            persona=msg.author.id,
        )

    async def get_previous(self, msg, minutes=5):
        """
        Get the previous message to store in database.

        Find a message in the same channel as the one given, which is directly
        before and occured within X minutes. Return the text of this message
        if it is found, otherwise return None.
        """

        logger.info('Looking for a previous message')

        prev = await msg.channel.history(
            # Find the message directly before this
            limit=1,
            oldest_first=False,
            before=msg,
            # Limit to messages within timeframe
            after=msg.created_at - timedelta(minutes=minutes)
        ).flatten()

        if len(prev) > 0:
            # We found a previous message
            if self.active_for(prev[0]):
                # Valid!
                logger.info('Found "%s"', prev[0].clean_content)
                return  prev[0].clean_content
            else:
                # The message is from before the summon frame opened
                logger.info('No message found within this frame')
        else:
            # We didn't find any messages
            logger.info('No message found')


def setup(bot):
    bot.add_cog(Chat(bot))
