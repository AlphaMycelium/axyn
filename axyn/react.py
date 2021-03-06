import logging
import re

import discord
from discord.ext import commands

# Set up logging
logger = logging.getLogger(__name__)


def is_command(text):
    """Check if the given text appears to be a command."""

    if text.startswith("pls "):
        return True

    return re.match(r"^\w{0,3}[^0-9a-zA-Z\s\'](?=\w)", text) is not None


class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Process a message and react if possible."""

        # Get a chatbot response
        if not self.should_ignore(msg):
            logger.info("Getting reaction")
            emoji, distance = self.bot.reaction_responder.get_response(msg.content)

            if distance <= 2:
                logger.info("Reacting with %s", emoji)
                await msg.add_reaction(emoji)
            else:
                logger.info("Distance %.2f, not reacting", distance)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Learn unicode emoji reactions as responses."""

        logger.info(
            'Received reaction %s on "%s"',
            reaction.emoji,
            reaction.message.clean_content,
        )

        # Use original message for ignore checking
        if self.should_learn_reaction(reaction.message, user):
            # Check if this is a unicode emoji or a custom one
            if type(reaction.emoji) == str:
                logger.info("Learning reaction")
                self.bot.reaction_responder.learn_response(
                    reaction.message.content, reaction.emoji
                )

    def should_ignore(self, msg):
        """Check if the given message should not be reacted to."""

        # Check if the author is a bot / system message
        if msg.author.bot or msg.type != discord.MessageType.default:
            logger.info("Author is a bot, ignoring")
            return True

        if msg.channel.type != discord.ChannelType.private and len(msg.content) < 5:
            logger.info("Message is less than 5 characters, ignoring")
            return True

        if msg.content.startswith("a!"):
            logger.info("Message is an Axyn command, ignoring")
            return True
        if (
            # In DMs, only Axyn commands will be used
            msg.channel.type != discord.ChannelType.private
            and is_command(msg.content)
        ):
            logger.info("Message appears to be a bot command, ignoring")
            return True

        return False

    def should_learn_reaction(self, msg, reaction_user):
        """Check if a reaction on the given message should be learned."""

        if reaction_user.bot:
            logger.info("Reaction is from a bot, not learning it")
            return False

        if reaction_user == msg.author:
            logger.info("Reaction is from message author, not learning it")
            return False

        if msg.author.bot and msg.author != self.bot.user:
            logger.info("Message is from foreign bot, not learning reaction")
            return False

        if len(msg.content) == 0:
            logger.info("Message has no text, not learning reaction")
            return False

        if is_command(msg.content):
            logger.info("Message appears to be a bot command, not learning reaction")
            return False

        return True


def setup(bot):
    bot.add_cog(React(bot))
