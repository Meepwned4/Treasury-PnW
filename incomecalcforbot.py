import requests,json
from bs4 import BeautifulSoup
aaid=''
email = ''
password = ''
apikey = ''


#Info
projects = ['Advanced City Planning','Arms Stockpile','Bauxiteworks','Center for Civil Engineering','City Planning','Emergency Gasoline Reserve','Green Technologies','Intelligence Agency','International Trade Center','Iron Dome','Ironworks','Mass Irrigation','Missile Launch Pad','Moon Landing','Nuclear Research Facility','Pirate Economy','Propaganda Bureau','Recycling Initiative','Space Program','Spy Satellite','Telecommunications Satellite','Uranium Enrichment Program','Vital Defense System']
continents = [' North America ',' South America ',' Africa ',' Antarctica ',' Europe ',' Australia ',' Asia ']
hemespheres = [['NorthAmerica','Europe','Asia'],['SouthAmerica','Africa','Australia']]
months = ['January','Febuary','March','April','May','June','July','August','Suptember','October','November','December']
monthsbuffed = [['December','January','Febuary'],['June','July','August']]
raws = {'coal':'coal_mines','oil':'oil_wells','bauxite':'bauxite_mines','iron':'iron_mines','lead':'lead_mines'}
totalaa = 0
impnames = ['coal_power','oil_power','nuclear_power', 'wind_power', 'coal_mines' , 'oil_wells', 'bauxite_mines','lead_mines', 'uranium_mines','iron_mines', 'farms', 'oil_refineries', 'steel_mills', 'aluminum_refineries', 'munitions_factories', 'police_stations', 'hospitals', 'recycling_centers', 'subways', 'supermarkets', 'banks', 'shopping_malls', 'stadiums']#, 'barracks', 'factories', 'hangars', 'drydocks']
impcosts = [1200,1800,10500,500,400,600,1600,1500,5000,1600,300,4000,4000,2500,3500,750,1000,2500,3250,600,1800,5400,12150]
milnames = ['soldiers', 'tanks', 'aircraft', 'ships', 'missiles', 'nukes']
milcosts =[[1.25,50,500,3750,21000,35000],[1.88,75,750,5625,31500,52500]]
colornames = ['Beige','Gray','Lime','Green','White','Brown','Maroon','Purple','Blue','Red','Orange','Olive','Aqua','Black','Yellow','Pink']
resorces= ['money', 'food', 'coal', 'oil',  'uranium',  'bauxite','iron','lead','gasoline','munitions','aluminum','steel']
colors = {0: 'beige', 1: 'gray', 2: 'lime', 3: 'green', 4: 'white', 5: 'brown', 6: 'maroon', 7: 'purple', 
8: 'blue', 9: 'red', 10: 'orange', 11: 'olive', 12: 'aqua', 13: 'black', 14: 'yellow', 15: 'pink'}
#scrapers

def gettaxscraper(nations,ids):
    nations = nations.find(class_='nationtable').find_all('a')
    for nat in nations:
        if 'alliance' not in nat.get('href'):
            ids.append(nat.get('href').split('=')[-1])
    return ids

def getnatsfromtaxid(taxid):
    nations = BeautifulSoup(requests.get(f'https://politicsandwar.com/index.php?id=15&maximum=50&minimum=0&tax_id={taxid}').content, "html.parser")
    ids = []
    natnum = int(nations.find_all('p',class_='center')[-2].get_text().split(' ')[-2])
    if natnum <=50:
        ids = gettaxscraper(nations,ids)
        return ids
    else:
        maxim = 0
        while natnum>0:
            
            natnum-=50
            nations = BeautifulSoup(requests.get(f'https://politicsandwar.com/index.php?id=15&maximum={maxim+50}&minimum={maxim}&tax_id={taxid}').content, "html.parser")
            ids = gettaxscraper(nations,ids)
            maxim+=50
        return ids
    
def colorinfo():
    with requests.Session() as session:
        session.post("https://politicsandwar.com/login/", data={"email": email, "password": password, "loginform": "Login"}, timeout=300)
        data = session.get('https://politicsandwar.com/leaderboards/display=color')
        soup = BeautifulSoup(data.content, "html.parser")
        table = soup.find("table", class_="nationtable").find_all("tr")
        color_data = {}
        color_data['month'] = str(soup.find_all('ul')[-3]).split('br/>')[-2].split(' ')[0]
        for row in table[1:]:
            row = [i for i in row if i != "\n"]
            color = row[0].find("img").get("title")
            color_data[color] = {"turn_bonus": row[5].get_text()}
    return color_data
        
def tresureinfo():
    data = requests.get('https://politicsandwar.com/leaderboards/display=treasures') 
    soup = BeautifulSoup(data.content, "html.parser")
    table = soup.find("table", class_="nationtable").find_all("tr")[1:]
    tresures = []
    #print(table)
    for tresure in table:
        things = tresure.find_all('a')
        if things:
            tresures.append({'nation':things[0].get_text(),'alliance':things[1].get_text()})
    return tresures

def projscrap(nation,month):
    req = requests.get("https://politicsandwar.com/nation/id=" + str(nation))
    req2 = str(req.content)
    proj_data = {}
    for proj in projects:
        proj_data[proj]= proj in req2
    table = BeautifulSoup(req.content, "html.parser")
    nation_table = table.find("table", {'class': 'nationtable'})
    value = nation_table.find(text="Radiation Index: ")
    x= str(table.find(attrs={"name": "description"}))
    for continent in continents:
        if continent in x:
            proj_data['continent'] = continent.replace(' ','')
    if proj_data['continent'] == 'Antartica':
        proj_data['foodmulti']= 0.5            
    elif proj_data['continent'] in hemespheres[0] and month in monthsbuffed[0]:
        proj_data['foodmulti']= 1.2
    elif proj_data['continent'] in hemespheres[0] and month in monthsbuffed[1]:
        proj_data['foodmulti']= 0.8
    elif proj_data['continent'] in hemespheres[1] and month in monthsbuffed[0]:
        proj_data['foodmulti']= 0.8
    elif proj_data['continent'] in hemespheres[1] and month in monthsbuffed[1]:
        proj_data['foodmulti']= 1.2
    else:
        proj_data['foodmulti'] = 1
    radopen = value.parent.parent.find_all("td")[1].get_text().split(" R ")
    proj_data["radiation"] = float(radopen[1].split(' ')[-2])+float(radopen[0])
    return proj_data


def citymanagerdata(nation):
    page = "https://politicsandwar.com/city/manager/n=" + nation
    with requests.Session() as session:
        data = session.get(page)
        soup = BeautifulSoup(data.content, "html.parser")
        table = soup.find("table", class_="nationtable").find_all("tr")
        city_data = []
        names = (sub.get_text() for sub in table[0].find_all("a"))
        citynum = 0
        for city in names:
            city_data.append({})
            for row in table[1:]:
                base = row.find_all("td")
                city_data[citynum][base[0].get_text().lower().replace(" ", "_")] = base[citynum+2].get_text()
            citynum+=1
    return city_data
#getrss function

def getnatrss(city_data,war,nation,proj_data,color_data,treasures):
    rss = {}
    for i in resorces:
        rss[i] = 0
    pop=0
    gross = 0    
    totalupkeep = 0
    for city in city_data:
        pop += int(city['population'].replace(',',''))
        #raws
        for x,y in raws.items():
            try:
                rss[x] +=(int(city[y])*3)* (1 + ((0.5 * (int(city[y]) - 1)) /9))
            except KeyError:
                ()
        try:
            rss['uranium'] +=(proj_data['Uranium Enrichment Program']+1)*(int(city['uranium_mines'])*3)* (1 + ((0.5 * (int(city['uranium_mines']) - 1)) /4))
        except KeyError:
            ()
        commerce = float(city['commerce'].strip('%'))
        moneypop = int(city['population'].replace(',',''))
        gross +=  (((commerce/50) * 0.725)+0.725) * moneypop
        for i in range(len(impnames)):
            try:
                totalupkeep += int(city[impnames[i]])*impcosts[i]
            except KeyError:
                ()
        foodadd =12*(int(city['farms'])*(float(city['land'].replace(',',''))/(500-(proj_data['Mass Irrigation']*100))))*(1 + ((0.5 * (int(city['farms']) - 1)) /19))*(1-(proj_data['radiation']/1000))     
        foodadd = foodadd*proj_data['foodmulti']
        rss['food'] +=foodadd
        #manus
        rss['oil'] -= (proj_data['Emergency Gasoline Reserve']+1)*(int(city['oil_refineries'])*3)* (1 + ((0.5 * (int(city['oil_refineries']) - 1)) /4))
        rss['coal'] -= ((proj_data['Ironworks']*0.36)+1)*(int(city['steel_mills'])*3)* (1 + ((0.5 * (int(city['steel_mills']) - 1)) /4))
        rss['iron'] -= ((proj_data['Ironworks']*0.36)+1)*(int(city['steel_mills'])*3)* (1 + ((0.5 * (int(city['steel_mills']) - 1)) /4))
        rss['bauxite'] -= ((proj_data['Bauxiteworks']*0.36)+1)*(int(city['aluminum_refineries'])*3)* (1 + ((0.5 * (int(city['aluminum_refineries']) - 1)) /4))
        rss['lead'] -= ((proj_data['Arms Stockpile']*0.34)+1)*(int(city['munitions_factories'])*6)* (1 + ((0.5 * (int(city['munitions_factories']) - 1)) /4))
        #powers/food
        wind = int(city['wind_power'])
        nukepw = int(city['nuclear_power'])
        oilpw = int(city['oil_power'])
        coalpw =int(city['coal_power'])
        infra = float(city['infrastructure'].replace(',',''))
        windpowers = 0
        while wind>0 and infra>0:
            wind -=1
            infra -= 250
            windpowers +=1
        nukepowers = 0
        while nukepw>0and infra>0:
            nukepw -=0.5
            infra -=1000
            nukepowers +=1
        oilpowers = 0
        while oilpw>0and infra>0:
            oilpw -=0.5
            infra -=100
            oilpowers +=1
        coalpowers = 0
        while coalpw>0and infra>0:
            coalpw -=0.5
            infra -=100
            coalpowers +=1
        rss['coal'] -= coalpowers*1.2    
        rss['oil'] -= oilpowers*1.2
        rss['uranium'] -= nukepowers*1.2
    if war == 1:
        rss['food']-=(int(nation['soldiers'])/500)
    else:        
        rss['food']-=(int(nation['soldiers'])/750)
    rss['food'] -= pop/1000
    for i,y in rss.items():
        rss[i]=round(rss[i],2)
    milupkeep = 0
    for i in range(len(milnames)):
        milupkeep += int(nation[milnames[i]])*milcosts[war][i]
    if nation['domestic_policy'] == 4:
        milupkeep = milupkeep*0.95
    if nation['domestic_policy'] == 2:
        gross = gross*1.01
    incomebuff = 1
    for tresue in treasures:
        if nation['nation'] == tresue['nation']:
            incomebuff+=0.05
        elif nation['alliance'] == tresue['alliance']:
            incomebuff+=0.03
    gross = gross*incomebuff
    totalupkeep += milupkeep
    nation_color = nation['color']
    nation_color = colors[nation_color].capitalize()
    colorbonus = color_data[nation_color]
    rss['money'] = (gross - totalupkeep) + (12*(int(colorbonus['turn_bonus'].replace(',','').replace('$',''))))
    return rss

def getanationsupkeep(nation,color_data,treasures):  
    city_data = citymanagerdata(nation['nation'].replace(' ','+'))
    proj_data = projscrap(nation['nation_id'],color_data['month'])
    if int(nation['offensive_wars'])+int(nation['defensive_wars']) >0:
        war =1
    else:
        war = 0
    rss = getnatrss(city_data,war,nation,proj_data,color_data,treasures)     
    return rss

def getaaincome(): 
    gsnations = requests.get('https://politicsandwar.com/api/v2/nations/'+apikey+'/&alliance_id='+aaid).json()['data']  
    color_data = colorinfo()
    treasures = tresureinfo()
    aarss ={}
    for i in resorces:
            aarss[i] = 0
    for nation in gsnations:
        rss = getanationsupkeep(nation,color_data,treasures)
        for key,value in rss.items():
            aarss[key]+=value
    return aarss

def getsinglenationupkeep(natid):
    nation = requests.get('https://politicsandwar.com/api/nation/id='+natid+'&key='+apikey).json()
    if nation['success'] == False:
        return {"no nation found":-1}
    nation['nation'] = nation['name']
    nation['nation_id'] = nation['nationid']
    nation['offensive_wars'] = nation['offensivewars']
    nation['defensive_wars'] = nation['defensivewars']
    color = ['beige','gray','lime','green','white','brown','maroon','purple','blue','red','orange','olive','aqua','black','yellow','pink']
    for i in range(len(colors)):
        if nation['color'] == color[i]:
            nation['color'] = i
            continue
    upkeep = getanationsupkeep(nation,colorinfo(),tresureinfo())
    return upkeep

def gettaxbracketupkeep(taxid,aaid):
    ids = getnatsfromtaxid(taxid)
    gsnations = requests.get('https://politicsandwar.com/api/v2/nations/'+apikey+'/&v_mode=0&alliance_id='+aaid).json()['data']
    filterednats = []
    for nation in gsnations:
        if str(nation['nation_id']) in ids and int(nation['alliance_position'])>1 and int(nation['color'])>1:
            filterednats.append(nation)   #filters out grey nations and applicants.
    aarss ={}
    color_data = colorinfo()
    tresures = tresureinfo()
    for nation in filterednats:
        aarss[nation['nation']] = getanationsupkeep(nation,color_data,tresures)      
    return aarss
    

            ids = gettaxscraper(nations,ids)
            maxim+=50
        return ids
    
def colorinfo():
    with requests.Session() as session:
        session.post("https://politicsandwar.com/login/", data={"email": email, "password": password, "loginform": "Login"}, timeout=300)
        data = session.get('https://politicsandwar.com/leaderboards/display=color')
        soup = BeautifulSoup(data.content, "html.parser")
        table = soup.find("table", class_="nationtable").find_all("tr")
        color_data = {}
        color_data['month'] = str(soup.find_all('ul')[-3]).split('br/>')[-2].split(' ')[0]
        for row in table[1:]:
            row = [i for i in row if i != "\n"]
            color = row[0].find("img").get("title")
            color_data[color] = {"turn_bonus": row[5].get_text()}
    return color_data
        
def tresureinfo():
    data = requests.get('https://test.politicsandwar.com/leaderboards/display=treasures') 
    soup = BeautifulSoup(data.content, "html.parser")
    table = soup.find("table", class_="nationtable").find_all("tr")[1:]
    tresures = []
    #print(table)
    for tresure in table:
        things = tresure.find_all('a')
        if things:
            tresures.append({'nation':things[0].get_text(),'alliance':things[1].get_text()})
    return tresures

def projscrap(nation,month):
    nation = '234558'
    month = 'March'
    req = requests.get("https://politicsandwar.com/nation/id=" + str(nation))
    req2 = str(req.content)
    proj_data = {}
    for proj in projects:
        proj_data[proj]= proj in req2
    table = BeautifulSoup(req.content, "html.parser")
    nation_table = table.find("table", {'class': 'nationtable'})
    value = nation_table.find(text="Radiation Index: ")
    x= str(table.find(attrs={"name": "description"}))
    for continent in continents:
        if continent in x:
            proj_data['continent'] = continent.replace(' ','')
    if proj_data['continent'] == 'Antartica':
        proj_data['foodmulti']= 0.5            
    elif proj_data['continent'] in hemespheres[0] and month in monthsbuffed[0]:
        proj_data['foodmulti']= 1.2
    elif proj_data['continent'] in hemespheres[0] and month in monthsbuffed[1]:
        proj_data['foodmulti']= 0.8
    elif proj_data['continent'] in hemespheres[1] and month in monthsbuffed[0]:
        proj_data['foodmulti']= 0.8
    elif proj_data['continent'] in hemespheres[1] and month in monthsbuffed[1]:
        proj_data['foodmulti']= 1.2
    else:
        proj_data['foodmulti'] = 1
    radopen = value.parent.parent.find_all("td")[1].get_text().split(" R ")
    proj_data["radiation"] = float(radopen[1].split(' ')[-2])+float(radopen[0])
    return proj_data


def citymanagerdata(nation):
    nation = 'The Red Menace'
    page = "https://politicsandwar.com/city/manager/n=" + nation
    with requests.Session() as session:
        data = session.get(page)
        soup = BeautifulSoup(data.content, "html.parser")
        table = soup.find("table", class_="nationtable").find_all("tr")
        city_data = []
        names = (sub.get_text() for sub in table[0].find_all("a"))
        citynum = 0
        for city in names:
            city_data.append({})
            for row in table[1:]:
                base = row.find_all("td")
                city_data[citynum][base[0].get_text().lower().replace(" ", "_")] = base[citynum+2].get_text()
            citynum+=1
    return city_data
#getrss function

def getnatrss(city_data,war,nation,proj_data,color_data,treasures):
    rss = {}
    war = 0
    for i in resorces:
        rss[i] = 0
    pop=0
    gross = 0    
    totalupkeep = 0
    for city in city_data:
        pop += int(city['population'].replace(',',''))
        #raws
        for x,y in raws.items():
            try:
                rss[x] +=(int(city[y])*3)* (1 + ((0.5 * (int(city[y]) - 1)) /9))
            except KeyError:
                ()
        try:
            rss['uranium'] +=(proj_data['Uranium Enrichment Program']+1)*(int(city['uranium_mines'])*3)* (1 + ((0.5 * (int(city['uranium_mines']) - 1)) /4))
        except KeyError:
            ()
        commerce = float(city['commerce'].strip('%'))
        moneypop = int(city['population'].replace(',',''))
        gross +=  (((commerce/50) * 0.725)+0.725) * moneypop
        for i in range(len(impnames)):
            try:
                totalupkeep += int(city[impnames[i]])*impcosts[i]
            except KeyError:
                ()
        foodadd =12*(int(city['farms'])*(float(city['land'].replace(',',''))/(500-(proj_data['Mass Irrigation']*100))))*(1 + ((0.5 * (int(city['farms']) - 1)) /19))*(1-(proj_data['radiation']/1000))     
        foodadd = foodadd*proj_data['foodmulti']
        rss['food'] +=foodadd
        #manus
        rss['oil'] -= (proj_data['Emergency Gasoline Reserve']+1)*(int(city['oil_refineries'])*3)* (1 + ((0.5 * (int(city['oil_refineries']) - 1)) /4))
        rss['coal'] -= ((proj_data['Ironworks']*0.36)+1)*(int(city['steel_mills'])*3)* (1 + ((0.5 * (int(city['steel_mills']) - 1)) /4))
        rss['iron'] -= ((proj_data['Ironworks']*0.36)+1)*(int(city['steel_mills'])*3)* (1 + ((0.5 * (int(city['steel_mills']) - 1)) /4))
        rss['bauxite'] -= ((proj_data['Bauxiteworks']*0.36)+1)*(int(city['aluminum_refineries'])*3)* (1 + ((0.5 * (int(city['aluminum_refineries']) - 1)) /4))
        rss['lead'] -= ((proj_data['Arms Stockpile']*0.34)+1)*(int(city['munitions_factories'])*6)* (1 + ((0.5 * (int(city['munitions_factories']) - 1)) /4))
        #powers/food
        wind = int(city['wind_power'])
        nukepw = int(city['nuclear_power'])
        oilpw = int(city['oil_power'])
        coalpw =int(city['coal_power'])
        infra = float(city['infrastructure'].replace(',',''))
        windpowers = 0
        while wind>0 and infra>0:
            wind -=1
            infra -= 250
            windpowers +=1
        nukepowers = 0
        while nukepw>0and infra>0:
            nukepw -=0.5
            infra -=1000
            nukepowers +=1
        oilpowers = 0
        while oilpw>0and infra>0:
            oilpw -=0.5
            infra -=100
            oilpowers +=1
        coalpowers = 0
        while coalpw>0and infra>0:
            coalpw -=0.5
            infra -=100
            coalpowers +=1
        rss['coal'] -= coalpowers*1.2    
        rss['oil'] -= oilpowers*1.2
        rss['uranium'] -= nukepowers*1.2
    if war == 1:
        rss['food']-=(int(nation['soldiers'])/500)
    else:        
        rss['food']-=(int(nation['soldiers'])/750)
    rss['food'] -= pop/1000
    for i,y in rss.items():
        rss[i]=round(rss[i],2)
    milupkeep = 0
    for i in range(len(milnames)):
        milupkeep += int(nation[milnames[i]])*milcosts[war][i]
    if nation['domestic_policy'] == 4:
        milupkeep = milupkeep*0.95
    if nation['domestic_policy'] == 2:
        gross = gross*1.01
    incomebuff = 1
    for tresue in treasures:
        if nation['nation'] == tresue['nation']:
            incomebuff+=0.05
        elif nation['alliance'] == tresue['alliance']:
            incomebuff+=0.03
    gross = gross*incomebuff
    totalupkeep += milupkeep
    nation_color = nation['color']
    nation_color = colors[nation_color].capitalize()
    colorbonus = color_data[nation_color]
    rss['money'] = (gross - totalupkeep) + (12*(int(colorbonus['turn_bonus'].replace(',','').replace('$',''))))
    return rss

def getanationsupkeep(nation,color_data,treasures):  
    city_data = citymanagerdata(nation['nation'].replace(' ','+'))
    proj_data = projscrap(nation['nation_id'],color_data['month'])
    if int(nation['offensive_wars'])+int(nation['defensive_wars']) >0:
        war =1
    else:
        war = 0
    rss = getnatrss(city_data,war,nation,proj_data,color_data,treasures)     
    return rss

def getaaincome(): 
    gsnations = requests.get('http://politicsandwar.com/api/v2/nations/'+apikey+'/&alliance_id='+aaid).json()['data']  
    color_data = colorinfo()
    treasures = tresureinfo()
    aarss ={}
    for i in resorces:
            aarss[i] = 0
    for nation in gsnations:
        rss = getanationsupkeep(nation,color_data,treasures)
        for key,value in rss.items():
            aarss[key]+=value
    return aarss

def getsinglenationupkeep(natid):
    nation = requests.get('http://politicsandwar.com/api/nation/id='+natid+'&key='+apikey).json()
    if nation['success'] == False:
        return {"no nation found":-1}
    nation['nation'] = nation['name']
    nation['nation_id'] = nation['nationid']
    nation['offensive_wars'] = nation['offensivewars']
    nation['defensive_wars'] = nation['defensivewars']
    color = ['beige','gray','lime','green','white','brown','maroon','purple','blue','red','orange','olive','aqua','black','yellow','pink']
    for i in range(len(colors)):
        if nation['color'] == color[i]:
            nation['color'] = i
            continue
    upkeep = getanationsupkeep(nation,colorinfo(),tresureinfo())
    return upkeep

def gettaxbracketupkeep(taxid,aaid):
    ids = getnatsfromtaxid(taxid)
    gsnations = requests.get('http://politicsandwar.com/api/v2/nations/'+apikey+'/&v_mode=0&alliance_id='+aaid).json()['data']
    filterednats = []
    for nation in gsnations:
        if str(nation['nation_id']) in ids and int(nation['alliance_position'])>1 and int(nation['color'])>1:
            filterednats.append(nation)   #filters out grey nations and applicants.
    aarss ={}
    color_data = colorinfo()
    tresures = tresureinfo()
    for nation in filterednats:
        aarss[nation['nation']] = getanationsupkeep(nation,color_data,tresures)      
    return aarss
    
