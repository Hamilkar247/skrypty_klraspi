# - *- coding: utf-8 - *-

import os
import sys
import traceback
from datetime import datetime
import time
import subprocess
import shutil
from dotenv import load_dotenv
from funkcje_pomocnicze import FunkcjePomocnicze, ExceptionEnvProjektu, ExceptionNotExistFolder, ExceptionWindows

##########################

def nazwa_programu():
    return "pomiar_rtl_433.py"

def funkcje_pomocnicze_inicjalizacja():
    fp=FunkcjePomocnicze(nazwa_programu())
    return fp

##########################

class PomiarRTL433():

    def __init__(self):
        self.fp=funkcje_pomocnicze_inicjalizacja()

    def kopiowanie_pomiar_txt(self):
        if os.path.exists(self.file_path):
            shutil.copyfile(self.file_path, self.file_path+".old")
            os.remove(self.file_path)
        fdp=open(self.file_data_pomiaru, "w")
        fdp.write(f"{self.minuta}\n")

    def start(self,  basic_path_ram):
        self.fp.drukuj(" - - - - - - -")
        self.fp.drukuj(nazwa_programu())
        self.file_path=f"{basic_path_ram}/pomiary.txt"
        file=open(self.file_path, "a")
        file.close()
        command=f"rtl_433 -s 2.5e6 -f 868.5e6 -H 30 -R 75 -R 150 -F json".split(" ")
        self.minuta=datetime.now().minute
        print(f"{self.minuta}")
        self.file_data_pomiaru=f"{basic_path_ram}/pomiary_minuta.txt"
        fdp=open(self.file_data_pomiaru, "w")
        fdp.write(f"{self.minuta}\n")
        fdp.close()
        with subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
            self.kopiowanie_pomiar_txt()
            for line in p.stdout:
                #ech=lineit(" ")
                self.fp.drukuj(f"minuta:{self.minuta}")
                obecna_minuta=datetime.now().minute
                if self.minuta != obecna_minuta:
                    self.fp.drukuj("kopiuje plik")
                    self.minuta = obecna_minuta

                    #shutil.copyfile(self.file_path, self.file_path+".old")
                    #os.remove(self.file_path)
                    #fdp=open(self.file_data_pomiaru, "w")
                    #fdp.write(f"{self.minuta}\n")
                file=open(self.file_path, "a")
                file.write(f"{line}")
                file.close()
    
        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)
    
def main():
    fp=FunkcjePomocnicze(nazwa_programu())
    basic_path_ram=""
    flara_skryptu=""
    odpalamy_pomiar=False
    try:
        fp.drukuj(f"------{nazwa_programu()}--------")
        if os.name=="posix":
            dotenv_path="../env_programu"
            fp.file_istnienie(dotenv_path, "sprawdz czy plik env_programu istnieje")
            load_dotenv(dotenv_path)
            basic_path_ram=fp.zmienna_env_folder("basic_path_ram", "env_programu - sprawdz basic_path_ram")
            flara_skryptu=f"{basic_path_ram}/{nazwa_programu()}.flara"
            flara_file=None
            if os.path.exists(flara_skryptu) == False:
                fp.drukuj("nie istnieje dzialajacy program pomiar")
                odpalamy_pomiar=True        
            else:
                pid=fp.get_pid_from_flara_file(flara_skryptu)
                fp.drukuj(pid)
                if fp.sprawdz_czy_program_o_tym_pid_dziala(pid) == False:
                    os.remove(flara_skryptu)
                    odpalamy_pomiar=True
                else:
                    odpalamy_pomiar=False
            if odpalamy_pomiar==True:
                flara_file=open(flara_skryptu, "w")
                fp.drukuj(f"os.getpid(): {os.getpid()}")
                flara_file.write(f"{os.getpid()}")
                flara_file.close()
                pomiarRTL433=PomiarRTL433()
                pomiarRTL433.start(basic_path_ram)
        else:
            fp.drukuj("oprogramuj tego windowsa w koncu")
            raise fp.exceptionWindows
        if odpalamy_pomiar==True:
            fp.usun_flare(basic_path_ram, flara_skryptu)
    except subprocess.CalledProcessError as e:
        fp.drukuj(f"exception {e}")
        fp.drukuj(f"jakies przerwanie w dzialanie")
        traceback.print_exc()
        error_file=open(f"{basic_path_ram}/reset_portu_usb.py.error", "w")
        error_file.write(fp.data_i_godzina())
        fp.usun_flare(basic_path_ram, flara_skryptu)
    except ExceptionEnvProjektu as e:
        fp.drukuj(f"exception {e}")
        fp.drukuj(f"sprawdz czy dobrze wpisales dane w env_programu (albo czy w ogole je wpisales ...)")
        traceback.print_exc()
        fp.usun_flare(basic_path_ram, flara_skryptu)
    except ExceptionWindows as e:
        fp.drukuj(f"exception {e}")
        fp.drukuj(f"Brak wersji oprogramowania na windowsa - wymaga analizy i/lub dopisania kodu")
        traceback.print_exc()
        fp.usun_flare(basic_path_ram, flara_skryptu)
    except Exception as e:
        fp.drukuj(f"exception {e}")
        fp.drukuj(f"zwskazowka do czytającego - sprawdz czy env_programu widziany jest w crontabie")
        #os.remove(fal)
        traceback.print_exc()
        fp.usun_flare(basic_path_ram, flara_skryptu)

if __name__ == "__main__":
    main()
