import discord
import logging
import tweepy
from asyncurban import UrbanDictionary
from discord.commands import Option
import random
from gravesbotconfig import TOKEN, BOT_ID, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CONSUMER_SECRET,TWITTER_CONSUMER_KEY
import pickle
import time
bot = discord.Bot()

""" This sends the "Delete" emoji follow up
Usually used on tweets, reddit posts, etc
Any time we want the user to be able to delete what the bot said"""
async def SendDelete(message,ctx):
    deleteFile = "deleteFile.pickle"
    async for x in ctx.channel.history():
        if str(x.author.id) == BOT_ID:
            await x.add_reaction(emoji="❌")
            message_id = str(x.id)
            break
    sender = str(ctx.user.id)
    try:
        with open(deleteFile, 'rb') as f:
            deleteable = pickle.load(f)
            f.close()
            deleteable[message_id] = sender
            f = open(deleteFile, 'wb')
            pickle.dump(deleteable, f)
            f.close()
    except:
        logging.exception("DeleteLogging: ")
        f = open(deleteFile, 'wb')
        deleteable = {message_id:sender}
        pickle.dump(deleteable, f)
        f.close()

"""This serves no purpose but it is a template and can be removed"""
#@bot.slash_command()
#async def hello(
#    ctx: discord.ApplicationContext,
#    name: Option(str, "Enter your name"),
#    gender: Option(str, "Choose your gender", choices=["Male", "Female", "Other"]),
#    age: Option(int, "Enter your age", min_value=1, max_value=99, default=18)
#    # passing the default value makes an argument optional
#    # you also can create optional argument using:
#    # age: Option(int, "Enter your age") = 18
#):
#    await ctx.respond(f"Hello {name}! Your gender is {gender} and you are {age} years old.")


""" Urbandictionary """
@bot.slash_command()
async def blockchain_urban(
        ctx: discord.ApplicationContext,
        term: Option(str, "Enter word"),
        result: Option(int, "Enter the result number", min_value=0, max_value=10, default=0)

):
    try:
        urban = UrbanDictionary()
        ### This can be removed probably, you are no longer able to call urbandictionary without specifying a word
        if term=="NONEADDED":
            word = await urban.get_random()
        else:
            if result != 0: #Default if the user does not request a different definition
                word = await urban.search(term)
                print(word[result].definition)
                definition = (word[result].definition)
                example = (word[result].example)
                wordTitle = (word[result].word).title()
                permalink = (word[result].permalink)
            else:  #This is for if the user doesnt like the first definition and wants to request another
                word = await urban.get_word(term)
                definition = str(word.definition)
                example = str(word.example)
                wordTitle= str(word.word).title()
                permalink = word.permalink
        """ Limits to message lengths. Longer than 1028 breaks discord."""
        if len(definition) > 1000:
            definition = definition[0:1000] + " ..."
        if len(example) > 1000:
            example = example[0:1000] + " ..."
        embed = discord.Embed(title=wordTitle,url=permalink)
        embed.add_field(name="Definition",
                        value=definition,
                        inline=False)
        embed.add_field(name="Example",
                    value=example,
                        inline=False)

        await ctx.respond(embed=embed)
        await urban.close()
    except:
        logging.exception("Urban: ")
        await ctx.respond("{} not found.".format(term.title()))

""" Twitter search
I dont remember how any of this works, but it does so just leave it."""
@bot.slash_command()
async def blockchain_tw(
        ctx: discord.ApplicationContext,
        user: Option(str, "Enter username")
):
    statuses = []
    consumer_key, consumer_secret, access_token, access_token_secret = TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    if user[0] == '#':
        hashtag = user
        thing = api.search(hashtag, rpp=1)
        for i in thing:
            # fullstatus = "https://twitter.com/" + str(i.user.screen_name) + "/status/" + str(i.id)
            statuses.append(i)
    else:

        num = 0

        try:
            thing = api.get_user(screen_name=str(user))
            profilepic = thing.profile_image_url

            pub = api.user_timeline(screen_name=str(user),exclude_replies=True, count=1000, tweet_mode='extended')
            for i in pub:
                if (not i.retweeted) and ('RT @' not in i.full_text):
                    statuses.append(i)
        except:
            logging.exception("Twitter Error: ")
            message = await ctx.respond("Error finding tweets for {}".format(user))
            await SendDelete(message, ctx)

            return
    try:

        status = random.choice(statuses)
        status = "https://twitter.com/%s/status/" % (
            status.user.screen_name) + str(status.id)
        message = await ctx.respond(status)

        await SendDelete(message, ctx)
        return
    except:
        logging.exception("Twitter error: ")
        message = await ctx.respond("No tweets found for {}".format(user))
        await SendDelete(message, ctx)
        pass

""" Functions for reactions
Currently only supports when a user clicks the "delete" emoji, but will eventually control resharing
from the reddit news channel or any twitter bots"""
@bot.event
async def on_raw_reaction_add(payload):

    """This is for deletables"""
    if (payload.emoji.name == "❌" and str(payload.user_id) != BOT_ID):
        try:
            deleteFile = "deleteFile.pickle"

            with open(deleteFile, 'rb') as f:
                deleteable = pickle.load(f)
                f.close()
            reacted_messageid = str(payload.message_id)
            reacted_user = payload.user_id
            reacted_channel = payload.channel_id

            ##This Breaks for DMs for some reason idfk. Nobody should be DMing the bot but could be fixed eventually
            if deleteable[reacted_messageid] == str(reacted_user):
                channel = bot.get_channel(reacted_channel)
                msg = await channel.fetch_message(payload.message_id)
                await msg.delete()

        except:
            logging.exception("Error")

bot.run(TOKEN)
