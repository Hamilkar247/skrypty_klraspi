# - *- coding: utf-8 - *-
import os
from datetime import datetime, timedelta
import sys
import traceback
from typing import Type
from requests import Session
import requests
from urllib.request import urlopen
import json
import time
from dotenv import load_dotenv

from petla_programu import file_istnienie

def nazwa_programu():
    return "sortowanie_i_usrednianie_pomiarow.py"

def data_i_godzina():
    now = datetime.now()
    current_time = now.strftime("%d/%m/%y %H:%M:%S")
    return current_time

def drukuj(obiekt_do_wydruku):
    try:
        print(data_i_godzina()+" "+nazwa_programu()+" "+str(obiekt_do_wydruku))
    except Exception as e:
        print(e)
        print(traceback.print_exc())

def przerwij_i_wyswietl_czas():
    czas_teraz = datetime.now()
    current_time = czas_teraz.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    sys.exit()

class ExceptionEnvProjektu(Exception):
    pass

def file_istnienie(path_to_file, komunikat):
    if os.path.isdir(path_to_file):
        drukuj(f"{komunikat}")
        raise ExceptionEnvProjektu
    return True

def folder_istnienie(path_to_folder, komunikat):
    if os.path.isdir(path_to_folder):
        drukuj(f"{komunikat}")
        raise ExceptionEnvProjektu
    return True

def zmienna_env_file(tag_in_env, komunikat):
    path_to_file=os.getenv(tag_in_env)
    if os.path.exists(path_to_file) == False:
        drukuj(f"{komunikat}, tag:{tag_in_env}, path:{path_to_file}")#sprawdz czy plik .env istnieje")
        raise ExceptionEnvProjektu
    return path_to_file

def zmienna_env_folder(tag_in_env, komunikat):
    path_to_folder=os.getenv(tag_in_env)
    if os.path.isdir(path_to_folder) == False:
        drukuj(f"{komunikat}, tag:{tag_in_env}, path:{path_to_folder}")#sprawdz czy plik .env istnieje")
        raise ExceptionEnvProjektu
    return path_to_folder

#############

class SortoUsredniacz(object):
    def __init__(self, inicjalna):
        self.interval=2
        self.basic_path_ram=os.getenv("basic_path_ram")
        self.folder_usera=f"{self.basic_path_ram}"
        self.folder_sortowania=f"{self.basic_path_ram}/sort_usr"
        self.time=None
        self.sortowanie()

    def sortowanie(self):
        try:
            if os.path.isdir(self.folder_sortowania):
                pass
            else:
                os.mkdir(self.folder_sortowania)
            if os.path.exists(f"{self.basic_path_ram}/pomiary.txt.old"):
                with open(f"{self.basic_path_ram}/pomiary.txt.old", "r") as file:
                    krotki=file.readlines()
                file.close()
                dict_transmitters = {}
                for krotka in krotki:
                    #drukuj(f"__{krotka}__")
                    krotka=str(krotka)
                    #print(f"{krotka}")
                    obj_json=json.loads(krotka)
                    #print(f"obj_krotka_json:{krotka}")
                    #drukuj(obj_json['id'])
                    id=str(obj_json['id'])
                    #drukuj(id)
                    if self.time is None:
                        self.time=obj_json['time']
                    if id in dict_transmitters:
                        lista_pom=dict_transmitters[id]
                        lista_pom.append(obj_json)
                        dict_transmitters[id]=lista_pom
                    else:
                        lista_pom=[]
                        lista_pom.append(obj_json)
                        #print(lista_pom)
                        dict_transmitters[id]=lista_pom
                    #drukuj(dict_transmitters)
                    lista_pom=None
                    obj_json=None
                #drukuj(f"dict: {dict_transmitters}")
                #drukuj(f"lista {lista}")
                #drukuj("-------------")
                dict_transmitters=self.usrednienie(dict_transmitters)
                #wpisanie do pliku
                file=open(f"{self.basic_path_ram}/sort_usr/"+self.time+".txt", "w")
                for key in dict_transmitters:
                    file.write(json.dumps(dict_transmitters[key][0]))
                    file.write("\n")
                file.close()
                os.remove(f"{self.basic_path_ram}/pomiary.txt.old")
            else:
                drukuj("brak pliku z pomiarami")
        except json.decoder.JSONDecodeError as e:
            drukuj(f"wystapil blad {e}")
            traceback.print_exc()
            drukuj("ten problem jest dla mnie nie jasny - kopiuje plik do logow, a problematyczny plik usuwam")
            with open(f"{self.basic_path_ram}/pomiary.txt.old", "r") as file:
                content=file.read()
            logowy=open(f"{self.basic_path_ram}/usrednianie_json_decoder_errory.log", "a")
            logowy.write(data_i_godzina() +"\n")
            logowy.write(content)
            os.remove(f"{self.basic_path_ram}/pomiary.txt.old")
        except Exception as e:
            drukuj(f"Wystapil blad {e}")
            traceback.print_exc()
    
    def usrednienie(self, dict_transmitters):
        drukuj("def: usrednienie")
        file = open(f"{self.basic_path_ram}/sorty.log", "a")
        file.write(f"{data_i_godzina()}\n")
        for key in dict_transmitters:
            file.write(f"id: {key} : hex({hex(int(key))}) -> liczb.do.usr {len(dict_transmitters[key])}\n")
            if len(dict_transmitters[key]) > 0:
                #drukuj(f"{key} -> {dict_transmitters[key]}")
                #drukuj("\n##########")
                lista_pomiarow=dict_transmitters[key]
                lista_pom_temp=[]
                lista_pom_wilg=[]
                for pom in lista_pomiarow:
                    lista_pom_temp.append(pom["temperature_C"])
                    lista_pom_wilg.append(pom["humidity"])
                srednia_temp=self.avg_temp(lista_pom_temp)
                srednia_wilg=self.avg_humd(lista_pom_wilg)
                elm_listy=lista_pomiarow[0]
                #chce zeby koncowka byla 00 sekund
                czas_bez_sekund=elm_listy["time"][:-2]
                czas=czas_bez_sekund+"00"
                elm_listy["time"]=czas
                elm_listy['temperature_C']=srednia_temp
                elm_listy['humidity']=srednia_wilg
                #dorzucam zasieg jako liczbe otrzymanych pakietow(trwa minute wiec powinno byc maksymalnie 6 pomiarow dla danego nadajnika)
                elm_listy['zasieg']=f"{round(((len(lista_pomiarow)*100)/6), 2):.1f}"
                lista_pomiarow=[]
                lista_pomiarow.append(elm_listy)
                dict_transmitters[key]=lista_pomiarow
        return dict_transmitters

    def avg_temp(self, lista_pom_temp):
        suma=0
        try:
            for pom_temp in lista_pom_temp:
                ####if else dodany ze wzgledu na to że - dla debiana(raspbian) zwraca mi literal temp "25.9 C" a dla ubuntu float 25.9
                #print(f"{type(pom_temp)}")
                #print(f"{pom_temp}")
                if type(pom_temp) == str:     
                    #print("tutej mam str")
                    czynnik=float(pom_temp.split(" ")[0])
                else: #raczej tu będzie po prostu float jeśli nie string
                    #print("tutej mam float")
                    czynnik=pom_temp
                suma=suma+float(czynnik)
                #print(f"suma: {suma}")
            wynik=suma/len(lista_pom_temp)
            #drukuj(wynik)
            wynik=f"{round(wynik,2):.1f}"
            #drukuj(f"wynik {wynik}")
            wynik=wynik+" C"
            #print(f"wynik: {wynik}")
            if type(wynik) == str:
                return wynik # ma zwrocic int
            else:
                KeyError
        except KeyError as e:
            drukuj(f"zwracana wartosc musi byc stringiem - czy twoj nim jest? {e}")
            traceback.print_exc()
        except Exception as e:
            drukuj(f"mozlwie ze temp nie ma liczby {e}")
            traceback.print_exc()

    def avg_humd(self, lista_pom_wilg):
        suma=0
        try:
            for pom_wilg in lista_pom_wilg:
                czynnik=pom_wilg
                suma=suma+pom_wilg
            wynik=suma/len(lista_pom_wilg)
            #drukuj(wynik)
            wynik=int(round(wynik)) 
            #drukuj(f"wynik {wynik}")
            if type(wynik) == int:
                return wynik # ma zwrocic int
            else:
                KeyError
        except KeyError as e:
            drukuj(f"zwracana wartosc musi byc intem {e}")
            traceback.print_exc()
        except Exception as e:
            drukuj(f"mozlwie ze temp nie ma liczby {e}")
            traceback.print_exc()

    #obecnie nieuzywany - do usunieacia
    def dostosuj_format_czasu(self, czas):
        #drukuj("====================================")
        #drukuj(czas)
        #drukuj("=============%%%=======================")
        obj_datetime=datetime.strptime(czas, "%Y-%m-%d %H:%M:%S")#"%d/%m/%y %H:%M:%S"))
        #drukuj(obj_datetime)
        #drukuj(type(obj_datetime))
        #drukuj("====================================")
        format_daty_docelowy=datetime.strftime(obj_datetime, "%d/%m/%y %H:%M:%S")
        return format_daty_docelowy

def main():
    basic_path_ram=""
    flara_skryptu=""
    try:
        drukuj(f"------{nazwa_programu()}--------")
        if os.name=="posix":
            drukuj("posix")
            dotenv_path="./.env"
            file_istnienie(dotenv_path, "sprawdz czy plik .env istnieje")
            load_dotenv(dotenv_path)
            basic_path_ram=zmienna_env_folder("basic_path_ram", ".env - sprawdz basic_path_ram")
            
            iteracji=0
            while True:
                if iteracji < 3:
                    iteracji=iteracji+1
                else:
                    drukuj("przerwij")
                    break
                flara_skryptu=f"{basic_path_ram}/{nazwa_programu()}.flara"
                with open(flara_skryptu, "w") as file:
                    file.write(f"{str(os.getpid())}")
                file.close()
                inicjalna=False
                if os.path.exists(f"{basic_path_ram}/pomiary.txt.old"):
                    sortousredniacz=SortoUsredniacz(inicjalna)
                    break
                else:
                    drukuj("brak pomiaru")
                time.sleep(1)
        else:
            drukuj("oprogramuj tego windowsa ziom")
    except ExceptionEnvProjektu as e:
        drukuj(f"exception {e}")
        drukuj(f"sprawdz czy dobrze wpisales dane w .env (albo czy w ogole je wpisales ...)")
        traceback.print_exc()
    except Exception as e:
        drukuj(f"exception {e}")
        drukuj(f"sprawdz czy .env widziany jest w crontabie")
        #os.remove(fal)
        traceback.print_exc()
    if os.path.isdir(basic_path_ram):
        if os.path.exists(flara_skryptu):
            os.remove(flara_skryptu)
            drukuj("usuwam flare")

if __name__ == "__main__":
    main()
