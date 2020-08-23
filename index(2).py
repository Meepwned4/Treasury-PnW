from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument, MissingAnyRole, CommandOnCooldown
import requests
import incomecalcforbot
import json
from bs4 import BeautifulSoup

aaid = ''
bankaaid = ''  # Offshore id, replace with alliance ID if you want both the cash sent and taxes to be calculated out of the main alliance.
rssname = ['money', 'food', 'coal', 'oil', 'uranium', 'bauxite', 'iron', 'lead', 'gasoline', 'munitions', 'aluminum','steel']
email = ''
password = ''
apikey = ''
token = ''
login_data = {"email": email, "password": password, "loginform": "Login"}
session = requests.Session()

def sendrss(session, email, password, aaid, rsstosend, nation):
    moneydat = {"withrecipient":nation,'withtype':"Nation","withsubmit":"Withdraw", 'withnote':'aid'}
    for rss,amount in rsstosend.items():
        for k,v in rsstosend[rss].items():
            if nation == rss:
                moneydat[f"with{k}"] = round(float(v), 2) #adds every resource and amount to moneydat
    if len(rsstosend) > 1: #checks if sending to more than one person (only applicable to sendtaxupkeep) 
        moneydat['withnote'] = 'raws, not for resale' #if true, changes withnote
    session.post("https://politicsandwar.com/login/", data=login_data, timeout=300) #logs into PnW
    token_data = BeautifulSoup(session.get(f"https://politicsandwar.com/alliance/id={bankaaid}&display=bank").text, "html.parser") #webscrapes bank page
    auth_token = token_data.find('input', {"name":"token"}) #searches for the hidden  auth token
    x = str(auth_token).split('<input name="token" type="hidden" value=') #removes some useless data
    x=x[1] #removes more
    x = x.replace('/>', '') #even more
    x = x.replace('"', '') #even more
    moneydat.update({'token': x}) #adds the auth token to moneydat
    result = session.post(f"https://politicsandwar.com/alliance/id={bankaaid}&display=bank", data=moneydat, timeout=300) #sends the rss, and saves resulting page
    soup_data = BeautifulSoup(result.text, 'html.parser') #webscrapes the resulting page
    success = soup_data.find_all(id="withdrawal-result") #finds the data to show if successful or if any errors occurred
    print(success) #prints results to console
    
client = commands.Bot(command_prefix='t!')

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.command(name='banktransfer', help='example: t!banktransfer The+Syndicate 1 money, 2 food')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def banktransfer(ctx, alliance, *, resources):
    if ctx.channel.name == 'oversight-nagging':
        rsstosend = {}
        aa = ''
        allgood = True
        parts = (alliance.split('+'))
        for i in parts: #turns 'The+Pirate+Syndicate' into 'The Pirate Syndicate'
            aa = aa + i + ' '
        rssparts = (resources.split(', '))
        for i in rssparts: #turns '1 money, 2 food' into rsstosend{'money': '1', 'food': '2'}
            splitrss = i.split()
            rsstosend.update({splitrss[1]:splitrss[0]})
        test = 0
        for k,v in rsstosend.items():
            if k in rssname: #checks if rsstosend has any invalid rss names
                test += 1
            elif k not in rssname:
                test = 0
        if len(rsstosend) != test: #if any invalid nation names detected
            allgood = False
        if not allgood:
            msg = 'You entered an invalid resource'
        if allgood:  
            session.post("https://politicsandwar.com/login/", data={"email": email, "password": password, "loginform": "Login"}, timeout=300) #logs into PnW
            moneydat = {"withrecipient": aa, 'withtype': "Alliance", "withsubmit": "Withdraw", 'withnote':'Bank Transfer'} #sets up moneydat
            for rss,amount in rsstosend.items():
                moneydat[f'with{rss}'] =amount #adds the rss to send to moneydat
            result =  session.post(f"https://politicsandwar.com/alliance/id={bankaaid}&display=bank", data=moneydat, timeout=300) #sends the rss and saves resulting page
            soup_data = BeautifulSoup(result.text, 'html.parser') #webscrapes the page
            success = soup_data.find_all(id="withdrawal-result") #finds the data to show if successful or if any errors occurred
            print(success) #prints result to console
            msg = "You have sent:\n"
            for rss,amount in rsstosend.items():
                msg+= f'{amount} {rss},\n'  
            msg += f'to {aa}' #sets up message to send to discord
        await ctx.send(msg) #sends message to discord


@client.command(name='taxupkeep', help='example: t!taxupkeep 908 3')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def taxupkeep(ctx, taxid, days):
    if ctx.channel.name == 'oversight-nagging':
        await ctx.send("this will take up to a minute")
        rss = incomecalcforbot.gettaxbracketupkeep(taxid,aaid) #calculates the rss to send to the specified tax bracket
        alliancemem = json.loads(requests.get(f"http://politicsandwar.com/api/alliance-members/?allianceid={aaid}&key={apikey}").text)['nations'] #gets data on all the aa's members
        aacolor = json.loads(requests.get(f"https://politicsandwar.com/api//alliance/id={aaid}&key={apikey}").text)['color'] #gets aa's color
        nationinfo = {}
        rssinfo = {}
        for i in alliancemem:
            nationinfo[i['nation']] = i #makes nationinfo contain the info in alliancemem, but better format
        for k,v in rss.items():
            rssinfo[k] = v #sets rssinfo equal to rss, fixing some issues
        msg ="Upkeep is \n"
        totalrss = {}
        for nation in rssinfo:
            if nationinfo[nation]['color'] != aacolor or nationinfo[nation]['minutessinceactive'] > 4320:
                del rss[nation] #deletes any inactive nations and nations not on aa color
        for i in rssname:
            totalrss[i] = 0 #adds every rss name to totalrss and sets their value to 0
        for nat in rss:
            for name,value in rss[nat].items():
                if value<0:
                    totalrss[name]+= value*int(days) #adds the value to send and multiplies by number of days specified
        for name,rs in totalrss.items():
            if rs<0:
                msg+=f"{name}: {rs}\n" #sets of msg to send
        await ctx.send(msg) #sends msg to discord
      
        
@client.command(name='sendtaxupkeep', help='example: t!sendtaxupkeep 1275 3')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def sendtaxupkeep(ctx, taxid, days):
    if ctx.channel.name == 'oversight-nagging':
        await ctx.send("this will take up to a minute")
        rss = incomecalcforbot.gettaxbracketupkeep(taxid,aaid) #calculates the rss to send to the specified tax bracket
        totalrss = {}
        for i in rssname:
            totalrss[i] = 0 #adds every rss name to totalrss and sets their value to 0
        for nat in rss:
            for name,value in rss[nat].items():
                if value<0:
                    totalrss[name]-= value #adds the value to send to totalrss
        bank = requests.get(f"https://politicsandwar.com/api/alliance-bank/?allianceid={bankaaid}&key={apikey}").json()['alliance_bank_contents'][0] #gets aa bank info
        alliancemem = json.loads(requests.get(f"https://politicsandwar.com/api/alliance-members/?allianceid={aaid}&key={apikey}").text)['nations'] #gets info on aa members
        aacolor = json.loads(requests.get(f"https://politicsandwar.com/api//alliance/id={aaid}&key={apikey}").text)['color'] #gets aa color
        nationrss = {}
        for i in alliancemem:
            nationrss[i['nation']] = i #makes nationinfo contain the info in alliancemem, but better format
        allgood = True
        for name,rs in totalrss.items():
            rs = rs*int(days)
            if rs<0:
                if bank[name]<rs: #checks if aa bank has enough to send
                    allgood = False
        if not allgood:
            msg = 'Your bank doesnt have enough resources to send that'
        else:
            rsstosend = {}
            for nat,rs in rss.items():
                if nationrss[nat]['color'] != aacolor or nationrss[nat]['minutessinceactive'] > 4320:
                    break #pevents inactive nations and nations not on aa color from being added
                rsstosend[nat] = {}
                for rssnamee,resource in rs.items():
                    rsstosend[nat][rssnamee] = 0
                    if resource<0:
                        rsstosend[nat][rssnamee] -= resource #adds any rss needing to be sent to rsstosend
            for nat in rsstosend:
                for rss in rsstosend[nat]:
                    rss *= int(days)
                    if nationrss[nat][rss] == -1: #checks if nation doesn't share bank info with aa, and if so gives them nothing
                        rsstosend[nat][rss] = 0
                    if rsstosend[nat][rss] - float(nationrss[nat][rss]) < 0: #makes sure rsstosend only contains what is needed to sustain the nation for specified days
                        rsstosend[nat][rss] = 0
            nat = []
            filtr_list = []
            filtr = 0
            for nation,rs in rsstosend.items():
                m = ''
                for i in rs:
                    if bank[i] < rs[i]: #makes sure, again, that bank has enough rss to send
                        rs[i] = 0 #if not enough, sets to 0, preventing erros later
                        m = ' Some resources were not sent.'
                    if rs[i] > 0: #checks if rss greater than 0, if true tells for loop to check next rss
                        break
                    else:
                        filtr+= 1 #filter that adds up the rss names to send
                    if filtr == len(rs): #checks if rsstosend will send all 0s to nation
                        filtr_list.append(nation)       #if true, adds the to list
                filtr = 0 #resets filter
            for i in filtr_list:
                del rsstosend[i] #delets nations that would be sent 0 resources in rsstosend
            if rsstosend:
                for nation in rsstosend:
                    sendrss(session, email, password, aaid, rsstosend, nation) #sends the rss to each nation, in turn
                msg = f'You have sent {days} days of resources to nations in tax bracket with id {taxid}.' + m
            else:
                msg = f'Nobody in tax bracket {taxid} needed resources within {days} days.'
        await ctx.send(msg)

@client.command(name='upkeep', help='example: t!upkeep 196366')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def upkeep(ctx, natid):
    if ctx.channel.name == 'oversight-nagging':
        await ctx.send("this may take a second")
        rss = incomecalcforbot.getsinglenationupkeep(natid) #calculates upkeep for single nation
        msg ="Upkeep is \n"
        for name,rs in rss.items():
            if rs <0:
                msg+=f"{name}: {round(rs,2)}\n"                    
        await ctx.send(msg)
        
@client.command(name='send', help='example: t!send Minoatia 1 money, 2 steel')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def send(ctx, nation, *, resources):
    if ctx.channel.name == 'oversight-nagging':
        rsstosend = {}
        nat = ''
        allgood = True
        parts = (nation.split('+'))
        for i in parts: #turns 'The+Pirate+Syndicate' into 'The Pirate Syndicate'
            nat += i + ' '
        rssparts = (resources.split(', '))
        for i in rssparts: #turns '1 money, 2 food' into rsstosend{'money': '1', 'food': '2'}
            splitrss = i.split()
            rsstosend.update({splitrss[1]:splitrss[0]})
        test = 0
        rsstosend = {
            nation: rsstosend
            } #changes rsstosend to a dictionary
        for l in rsstosend:
            for k, v in rsstosend[l].items():
                if k in rssname: #checks if any invalid rss names in rsstosend, if yes adds 1 to test
                    test += 1
                elif k not in rssname: #if not, sets test to 0
                    test = 0
        if len(rsstosend) != test: #checks if test was set to 0 any times
            allgood = False
        if not allgood:
            msg = 'You entered an invalid resource'
        if allgood:
            sendrss(session,email, password,aaid,rsstosend,nation) #sends the rss to nation
            msg = "You have sent:\n"
            for nat in rsstosend:
                for k,v in rsstosend[nat].items():
                    msg+= f'{v} {k} '  
            msg += f'to {nation}'
        await ctx.send(msg)

@client.command(name='bank', help='example: t!bank')
@commands.has_any_role('Pentarch', 'Elder', 'Suffet')
async def bank(ctx):
    if ctx.channel.name == 'oversight-nagging':
        bank = requests.get(f"https://politicsandwar.com/api/alliance-bank/?allianceid={bankaaid}&key={apikey}").json()['alliance_bank_contents'][0] #gets aa bank info
        msg = f"Currently in the bank of {bank['name']} is \n"
        for nme,thing in bank.items():
            if nme in rssname:
                msg += f"{nme}: {thing}\n"       
            
        await ctx.send(msg)

@client.listen('on_command_error')
async def on_error(ctx, exc):
    if isinstance(exc, MissingAnyRole):
        await ctx.send('You do not have the necessary permissions to use this command')
    elif isinstance(exc, CommandOnCooldown):
        await ctx.send(f'That command is on cooldown. Try again in {exc.retry_after:,.2f} secs.')
    elif isinstance(exc, MissingRequiredArgument):
        await ctx.send('One or more required Arguments are missing')
client.run(token)