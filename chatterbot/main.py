import logging
import os.path

import discord
from discord.ext import commands
from chatterbot import ChatBot, trainers


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Discord bot
logger.info('Setting up bot')
bot = commands.Bot(
    command_prefix='c!',
    activity=discord.Game('c!summon')
)


# Set up Chatterbot
do_train = not os.path.exists('database.sqlite3')
bot.chatter = ChatBot(
    'Chatterbot',
    # Store data in SQLite
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///database.sqlite3',
    logic_adapters=[
        # Allow math questions such as "What is 5 squared?"
        'chatterbot.logic.MathematicalEvaluation',
        # General responses learned in database
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': str(),
            'maximum_similarity_threshold': 0.90
        }
    ]
)

if do_train:
    # Do initial training
    logger.info('Training chatterbot')

    # Simple list
    trainer = trainers.ListTrainer(bot.chatter)
    trainer.train([
        'Hello',
        'Hi!',
        'How are you?',
        'Fine, what about you?',
        'I\'m fine, thanks!',
    ])

    # Chatterbot Corpus
    cc_trainer = trainers.ChatterBotCorpusTrainer(bot.chatter)
    cc_trainer.train('chatterbot.corpus')


def launch():
    """Launch the Discord bot."""

    # Load extensions
    logger.info('Loading extensions')
    bot.load_extension('chat')
    bot.load_extension('train')

    # Connect to Discord and start bot
    logger.info('Starting bot')
    bot.run(os.environ['DISCORD_TOKEN'])


if __name__ == '__main__':
    launch()