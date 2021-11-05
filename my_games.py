#!/usr/bin/env python
# coding: utf-8


import requests
import json
import os
import urllib.request
import pandas as pd
import re
import pymysql
from datetime import datetime, timedelta

PGNfolder = "./PGN"

def get_PGN(player):
    #Gets the pgn files from the chesscom api and saves it locally by month file
    pgn_archives = requests.get('https://api.chess.com/pub/player/'+player.lower()+'/games/archives')
    #garantees that the player will always be lowercase, in case the user writes it differently
    print("Solving %s online data..." % player)
    try:
        #print(json.loads(pgn_archives.content)["archives"])
        skip_refiller = True #this variable helps to check if I have to remove the last month and redownload it
        if not os.path.exists(PGNfolder):
            #check if the main /pgn folder exist, if not it creates
            os.makedirs(PGNfolder)
            
        for month_url in json.loads(pgn_archives.content)["archives"]:
            #goes through all the archives and check each month
            user_folder = PGNfolder + '/' + month_url.split("/")[-4]
            folderpath = user_folder + "/" + month_url.split("/")[-2] + "-" + month_url.split("/")[-1]

            if not os.path.exists(user_folder):
                #checks if the name folder existis, if not it will create
                os.makedirs(user_folder)
            
            if not os.path.exists(folderpath+".txt"):
                #check if the month file exists, if not it will create
                urllib.request.urlretrieve(month_url+'/pgn', folderpath+".txt")
                print("New folder found %s" % folderpath)
                skip_refiller = False #it's a completely new month, it won't redownload it
        
        if skip_refiller: #if the newest month already exists, it will remove it and download a new one
            #if I played some games in july, it wil remove the "july" file and download it with new games
            os.remove(folderpath + ".txt")
            urllib.request.urlretrieve(month_url+'/pgn', folderpath+".txt")
            print("Refilling folder %s" % folderpath)
        
        print("%s data solved." % player)
        return(True)
    except KeyError: #if the given player doesn't have an archive nor exists, it'll return as player not found and boolean False
        print("player not found")
        return(False)
    
def extract_data(filepath):
    #Loads the PGN files from the local folders
    #print("Reading PGN")
    with open(filepath) as f:
        #print(f.readlines())
        return f.readlines()
    
def data_delimiter(data):
    #Returns two lists: One with the beginnings and another with the endings of each game in a data list
    start = []
    end = []
    
    for i,j in enumerate(data):

        if j.startswith("[Event"):
            start.append(i)
            if i != 0:
                end.append(i - 2)

    end.append(len(data))

    return(start, end)

#The game itself comes in a really strange format, so I make it cleaner and return only the important information
def PGNExtract(data):
    s = data.split(" ")
    
    game = "1."
    
    for i, j in enumerate(s):
        
        if j != "1.":
            if ("1-0" in j) or ("0-1" in j) or ("1/2-1/2" in j):
                j = j[:-1]
                game = game + " " + j

            elif ("{" not in j) and ("}" not in j) and ("..." not in j):
                game = game + " " + j            
            
    return(game)

def pieceMoveCounter(moves, playerColor, timeControl_is, id_):
    #This function counts how many time I moved each piece
    s = moves.split(" ")
    
    pieceMoves[id_] = {"Q" : 0,
                       "N" : 0,
                       "R" : 0,
                       "K" : 0,
                       "B" : 0,
                       "p" : 0,
                       "O_O" : 0,
                       "O_O_O" : 0,
                       "x" : 0,
                       "check" : 0}
    
    if playerColor == "White":
        somador = 1
        
    elif playerColor == "Black":
        somador = 2
    
    for i, move in enumerate(s):
        if "." in move:
            if ("1-0" in s[i + somador]) or ("1/2-1/2" in s[i+somador]) or ("0-1" in s[i+somador]):
                break
            else:
                #print(s[i+somador])
                if "+" in s[i+somador]:
                    pieceMoves[id_]["check"] += 1

                if "x" in s[i+somador]:
                    pieceMoves[id_]["x"] += 1

                if "Q" in s[i+somador]:
                    pieceMoves[id_]["Q"] += 1

                elif "N" in s[i+somador]:
                    pieceMoves[id_]["N"] += 1

                elif "R" in s[i+somador]:
                    pieceMoves[id_]["R"] += 1

                elif "K" in s[i+somador]:
                    pieceMoves[id_]["K"] += 1

                elif "B" in s[i+somador]:
                    pieceMoves[id_]["B"] += 1

                elif "O-O-O" in s[i+somador]:
                    pieceMoves[id_]["O_O_O"] += 1

                elif "O-O" in s[i+somador]:
                    pieceMoves[id_]["O_O"] += 1

                else:
                    pieceMoves[id_]["p"] += 1

#Here I take the game as a text and make it return as a list with formated data so i can upload to the database what I really need
def transform_data(data, start, end, player):

    pattern = "\"(.*?)\"" #pattern for regular expression delimiting data between ""
    allGames = []
    for i in range(0, len(start)):
        
        inGame = []
        game = data[start[i]:end[i]] #game delimitation  
        if game[10].startswith("[ECOUrl"):
            whitePlayer = re.search(pattern, game[4]).group(1)
            if whitePlayer == player: #se o player estiver de brancas
                inGame.append(whitePlayer) #append player
                inGame.append("White") #append player color
                inGame.append(re.search(pattern, game[5]).group(1)) #append black player

            else: #se o player estiver de pretas
                inGame.append(re.search(pattern, game[5]).group(1)) #append black player
                inGame.append("Black") #append player color
                inGame.append(whitePlayer) #append opponent

            winner = re.search(pattern, game[16]).group(1) #get winner and winning reason eg: white won by resignation
            winner = winner.split(" ")

            if winner[0] == player: #if the player won the match
                inGame.append('Winner') #indicates that the player won
                inGame.append(winner[-1]) #winning reason

            elif winner[0] == 'Game': #if it was a draw
                inGame.append('Draw') #indicates that the player drew
                inGame.append(winner[-1]) #winning reason

            else:
                inGame.append('Loser') #indicates that the player lost
                inGame.append(winner[-1]) #winning reason

            if whitePlayer == player: #se o player estiver de brancas
                inGame.append(re.search(pattern, game[13]).group(1)) #player ELO
                inGame.append(re.search(pattern, game[14]).group(1)) #opponent ELO

            else: #Se o jogador estiver de pretas
                inGame.append(re.search(pattern, game[14]).group(1)) #Player ELO
                inGame.append(re.search(pattern, game[13]).group(1)) #Opponent ELO

            inGame.append(re.search(pattern, game[15]).group(1)) #Defines time control
            dateObject = datetime.strptime(re.search(pattern, game[2]).group(1), "%Y.%m.%d") #Defines date in UTC
            time_utc = re.search(pattern, game[12]).group(1) #get the time in UTC

            #Here converts time UTC to UTC-3, since I'm brazilian and the chesscom uses UTC
            utc_dt = dateObject.strftime("%d/%m/%Y") + " " + time_utc
            utc_dt = datetime.strptime(utc_dt, "%d/%m/%Y %H:%M:%S")
            utc_br = utc_dt - timedelta(hours=3)

            inGame.append(utc_br.strftime("%d/%m/%Y")) #Set date as dd/mm/YYYY

            inGame.append(utc_br.strftime("%H:%M:%S")) #insert time into the list

            pattern2 = "\"https://www.chess.com/openings/(.*?)\"" #gets the link our of the equation
            substring = re.search(pattern2, game[10]).group(1) #same
            
            pattern2 = "(.*?)\."

            #Game opening variations has too much granilarity
            #so i need to make it more consise to easily understand my games
            try: #this will try to remove the ...nf3 stuff
                substring = re.search(pattern2, substring).group(1)
                substring = substring.replace("-1", "")
                substring = substring.replace("-2", "")
                substring = substring.replace("-3", "")
                substring = substring.replace("-4", "")
                substring = substring.replace("-5", "")
                substring = substring.replace("-6", "")
            except: #if there's no stuff like this, continues normally
                substring = substring.replace("-1", "")
                substring = substring.replace("-2", "")
                substring = substring.replace("-3", "")
                substring = substring.replace("-4", "")
                substring = substring.replace("-5", "")
                substring = substring.replace("-6", "")

            #A chess opening usually has 4 name variations:
            #Opening, defense, game or attack
            #Here I'm certain it will remove all granularity after that
            #which makes the code above kinda superfluous
            if "Opening" in substring: 
                pattern2 = "(.*?)-Opening" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Opening"#same
                #print(substring)
                
            if "Defense" in substring:
                pattern2 = "(.*?)-Defense" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Defense"#same
                #print(substring)
                
            if "Game" in substring:
                pattern2 = "(.*?)-Game" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Game"#same
                #print(substring)
            
            if "Attack" in substring:
                pattern2 = "(.*?)-Attack" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Attack"#same

            inGame.append(substring)
                
            gamePGN = PGNExtract(game[-1]) #get the game PGN
                
            inGame.append(gamePGN) #pgn transformed into a string
            
            try: #the id from the game link is the id in the database
                pattern2 = "\"https://www.chess.com/game/live/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            except:
                pattern2 = "\"https://www.chess.com/game/daily/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            
            
            #Here it goes to the function to count how many times I moved each piece
            pieceMoveCounter(gamePGN, inGame[1], inGame[-6], inGame[-1])

            allGames.append(inGame)

    return(allGames)

def db_connect():
    #informacoes para acessar o banco de dados (preciso deixar mais seguro)
    host="Desculpa"
    user="Github"
    password="Mas hoje não"
    database="Ainda resolverei isso"

    try: #conecta no banco de dados MariaDB no RDS
        conn = pymysql.connect(host=host, user=user, passwd=password, db=database, connect_timeout=5)
        print("Connecting database")
    except pymysql.MySQLError as e:
        print(e)

    return(conn)
    
    
#Update the chess moves to the database
def dbUpdate_chess_moves(cur, conn):
    
    print("Inserting counter database")
    for i in pieceMoves:

        sql = "SELECT * FROM chesscom.chess_moves WHERE id = %s"
        adr = (i, )

        cur.execute(sql, adr) #busca no banco de dados

        myresult = cur.fetchone() #pega resultado da busca

        if myresult == None: #caso nao esteja
            sql = "INSERT INTO chesscom.chess_moves (id, Q, N, R, K, B, p, O_O, O_O_O, x, chck) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            
            val = (str(i), int(pieceMoves[i]["Q"]), int(pieceMoves[i]["N"]), int(pieceMoves[i]["R"]), int(pieceMoves[i]["K"]), \
                   int(pieceMoves[i]["B"]), int(pieceMoves[i]["p"]), int(pieceMoves[i]["O_O"]), int(pieceMoves[i]["O_O_O"]), \
                   int(pieceMoves[i]["x"]), int(pieceMoves[i]["check"]))

            
            try:
                cur.execute(sql, val) #insere no banco de dados
                #print("Inserting counter database")
            
            except:
                None
                #print("Insert error")
                
        else:
            None
                
    conn.commit()
        
        
def main(player):
    
    playerExists = get_PGN(player) #tries to download player PGN data
    if playerExists: #If the player exists, then:        
    
        conn = db_connect()
        cur = conn.cursor()

        df = pd.DataFrame(columns=dfColumns)

        with os.scandir(PGNfolder + "/" + player.lower()) as folders: #goes through all the player month files
            for file in folders:

                data = extract_data(file) #load each month file into the memory
                start, end = data_delimiter(data) #defines the limits of each data part as two lists

                allGames = transform_data(data, start, end, player) #Go through all the chess games and return it as a list of lists
                
                df2 = pd.DataFrame(data=allGames, columns=dfColumns) #Append the month to the games dataframe
                df = df.append(df2, ignore_index=True)

        print("Trying to insert into database")
        for i in range(0, df.shape[0]):

            sql = "SELECT * FROM chesscom.chess_games WHERE id = %s"
            adr = (df.iloc[i]['id'], )

            cur.execute(sql, adr) #busca no banco de dados

            myresult = cur.fetchone() #pega resultado da busca
            if myresult == None: #caso nao esteja
                sql = "INSERT INTO chesscom.chess_games (player, playerColor, oponent, result, winningReason, playerElo, oponentElo, timeControl, date, time, opening, pgn, id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                
                val = (str(df.iloc[i]['player']), str(df.iloc[i]['playerColor']), str(df.iloc[i]['oponent']), \
                       str(df.iloc[i]['result']), str(df.iloc[i]['winningReason']), int(df.iloc[i]['playerElo']), \
                       int(df.iloc[i]['oponentElo']), str(df.iloc[i]['timeControl']), str(df.iloc[i]['date']), \
                       str(df.iloc[i]['time']), str(df.iloc[i]['opening']), str(df.iloc[i]['pgn']), str(df.iloc[i]['id']))
                

                try:
                    cur.execute(sql, val) #insere no banco de dados

                except:
                    None
                    
            conn.commit()

        dbUpdate_chess_moves(cur, conn)
                
    else: #If the player does not exist, it stops
        print("There's no %s data on chess.com" % player)

    print("end")   
    cur.close()
    conn.close()
    
    
#Pandas dataframe column names
dfColumns = ["player", "playerColor", "oponent", "result", "winningReason", "playerElo", "oponentElo", "timeControl", 'date', 'time', 'opening', 'pgn', 'id']


pieceMoves = {} #Piece movoves bones. It's going to be filled with a dictionary of how many times I moved each piece in each game

if __name__ == "__main__":
    main("Hallsand")