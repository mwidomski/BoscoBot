import logging
import re
import asteval
import discord
from discord.ext import commands

m_tkrole = re.compile("[-+*/=]([0-9]+$)")
aeval = asteval.Interpreter()

logging.basicConfig(level=logging.INFO)

PREFIX = '.bosco '

client = discord.Client()
bot = commands.Bot(command_prefix=PREFIX)

#TODO: Get Michael to create custom channel for logging bot output
#TODO: Custom error message for invalid commands

### Set a new number of team kills for members with the team kill role
### REQUIRES: manage_roles, manage_messages
@bot.command()
async def teamkills(ctx, member: discord.Member, command: str):
  if m_tkrole.match(command):
    #evaluate command string
    #interpret command
    operand = command[0]
    r_op = command[1:]
    for rl in member.roles:
      if "Team Kills" in rl.name:
        #get existing number
        l_op = rl.name.rsplit(" ",1)[1]
        #evaluate expression
        if operand != "=":
          result = aeval(l_op+operand+r_op)
        else:
          #WARN: calling aeval is technically unnecessary here
          result = int(aeval(r_op))
        #edit existing role
        await rl.edit(name="Team Kills: " + str(result))
        
        print("Set new team kill count for " + member.name + " from " + str(l_op) + " to " + str(result))
        #TODO: Use server name instead of global name
        await ctx.message.author.send("Set new team kill count for " + member.name + " from " + str(l_op) + " to " + str(result))
        break
    else:
      #TODO: create new role
      print("Team kill role is not assigned to this member, cannot edit")
      await ctx.message.author.send("Team kill role is not assigned to this member, cannot edit")
      
    
  else:
    print("Invalid command. Format: .bosco teamkills @<User> [+-*/=]<number>")
    await ctx.message.author.send("Invalid command. Format: .bosco teamkills @<User> [+-*/=]<number>")
    
  #Remove bot command from the channel.
  await ctx.message.delete()
  

#TODO: Get mike troll pic from Michael
#TODO: Maybe just paste the image, don't use Embed
### When called, paste a picture of mike troll in the calling channel
#@bot.command()
#async def mike(ctx):
#  _embed = discord.Embed()
#  #_embed.set("url to image")
#  ctx.channel.send(embed=_embed)


#PM opted in users whenever another user is playing a game
#TODO: Need to store list of opt ins per user. Txt file, db instance?
@client.event()
async def on_member_update():
  
  
  
  
####################RUNNER####################
f = open('token.txt','r')
token = f.read()
bot.run(token)