__author__ = 'Morten Tengesdal og Kristian Thorsen'
# Dato:2016.08.05
# Oppdatert til Python 3 av K. Thorsen
# Med serieporttraad og med meldingskoe
# Skriptet loggar akselerasjonsdata i X-, Y- og Z-retning i 16-bitsformat og med
# tidsreferanse i 8-bitsformat.
# Meldingsformat STX+(T+samplenr.(2 ASCII HEX-siffer)+X+data(4 ASCII Hex-siffer)
#                                                     Y+data(4 ASCII Hex-siffer)
#                                                     Z+data(4 ASCII Hex-siffer))*N+ETX
# Raadata blir lagra til fil og skalerte data blir plotta.
# Skriptet blir koeyrt saman med prosjektet aks_xyz_loggar_stm32f3_disc paa
# kortet STM32F3Discovery

import threading
import queue
import time
import numpy as np
import serial
import matplotlib.pyplot as mpl
import csv
#from matplotlib.animation import FuncAnimation

# Importerer GUI oppsett
import raakode_gui_metoder
import kommando_status
#start_event = threading.Event()
# --------------------------------------------------------------------------
# Oppsett og Metodar for Liveplotting
# --------------------------------------------------------------------------
#fig, ax = mpl.subplots()
#x_data = []
#y_data = []
#line, =ax.plot([],[],'b-')

datakoe=queue.Queue()


def print_bytes(data):
    print([f"{b:02X}" for b in data])



def seriekomm_egen():
    frame_errors = 0
    while not raakode_gui_metoder.stopp_trigger.is_set():
               
        data = raakode_gui_metoder.serieport.read(21)
        if len(data) == 21 and data[0]==0xFF and data[20]==0xF0:
            datakoe.put(data)
        else:
            print('Frame error')
            frame_errors +=1

        if frame_errors>5:
            seriekomm_resynkroniserar()
            frame_errors = 0

        time.sleep(0.01)

def seriekomm_resynkroniserar():
    while True:
        bitsjekker = raakode_gui_metoder.serieport.read(1)
        if bitsjekker == b'\xFF':
            break
    resterande_beskjed = raakode_gui_metoder.serieport.read(20)
    ramme = bitsjekker+resterande_beskjed
    if ramme[-1] == 0xF0:
        print('Jadda, fikk til resynkronisering!')
        datakoe.put(ramme)
        return ramme
    else:
        print('Tror vi prøver en gang til....')
        return seriekomm_resynkroniserar()

def datakoe_handterer():
    start_sjekk=True
    while not raakode_gui_metoder.stopp_trigger.is_set():
        datakoe_lokal = list(datakoe.get())
        print_bytes(datakoe_lokal)

        # Sjekker hvor mange skritt samplenr. inkrementeres med
        if start_sjekk:
            sample=1
            sample_skritt=0
            
            start_sjekk=False       
        elif datakoe_lokal[1]>sample_prev:
            sample_skritt = datakoe_lokal[1]-sample_prev
        elif datakoe_lokal[1]==0:
            sample_skritt=256-sample_prev
        elif datakoe_lokal[1]<sample_prev:
            sample_skritt=datakoe_lokal[1]+256-datakoe_lokal[1]
        sample=sample+sample_skritt
        print(sample)
        print(datakoe_lokal[1])
        print(sample_skritt)

        sample_prev=datakoe_lokal[1]
        datakoe_lokal[1]=sample

        # Omgjøring av innkommende verdier

        kommando_status.avstand = (datakoe_lokal[3]<<8)|datakoe_lokal[2]
        kommando_status.x_aks = (datakoe_lokal[5]<<8)|datakoe_lokal[4]
        kommando_status.y_aks = (datakoe_lokal[7]<<8)|datakoe_lokal[6]
        kommando_status.z_aks = (datakoe_lokal[9]<<8)|datakoe_lokal[8]
        kommando_status.error = kommando_status.avstand-kommando_status.Ref_ny
        #kommando_status.error = (datakoe_lokal[11]<<8)|datakoe_lokal[10]
        kommando_status.power = (datakoe_lokal[13]<<8)|datakoe_lokal[12]
        kommando_status.uP = (datakoe_lokal[15]<<8)|datakoe_lokal[14]
        kommando_status.uI = (datakoe_lokal[17]<<8)|datakoe_lokal[16]
        kommando_status.uD = (datakoe_lokal[19]<<8)|datakoe_lokal[18]
        datakoe_lokal_hex =  " ".join(f"{b:02X}" for b in datakoe_lokal)
        
        #log_line = (
        #    f"{sample} | "
        #    f"{kommando_status.avstand} | {kommando_status.x_aks} | {kommando_status.y_aks} | {kommando_status.z_aks} | {kommando_status.error} | "
        #    f"{kommando_status.power} | {kommando_status.uP} | {kommando_status.uI} | {kommando_status.uD}\n"
        #)


        #f.write(log_line)
        skrivar.writerow([
            sample, kommando_status.avstand, kommando_status.x_aks, kommando_status.y_aks, kommando_status.z_aks,
            kommando_status.error, kommando_status.power, kommando_status.uP, kommando_status.uI, kommando_status.uD
        ])        
        
        f.flush
        

        



if __name__ == "__main__":

    #fileNamn = 'logg.txt'
    #f = open(fileNamn, 'w')
    #f.write("Tid | Avstand | X | Y | Z | Error | Power | uP | uI | uD\n")

    fileNamn = 'csv_logg.csv'
    f = open(fileNamn,"w",newline="")
    skrivar = csv.writer(f)
    skrivar.writerow([
    "Tid", "Avstand", "X", "Y", "Z", "Error",
    "Power", "uP", "uI", "uD"
    ])


    thread1 = threading.Thread(target=raakode_gui_metoder.sensor_loop)
    thread1.start()

    thread3 = threading.Thread(target=datakoe_handterer)
    thread3.start()

    thread2 = threading.Thread(target=seriekomm_egen)
    thread2.start()



    applikasjon = raakode_gui_metoder.QApplication(raakode_gui_metoder.sys.argv)
    vindu = raakode_gui_metoder.MainWindow()
    vindu.show()
    applikasjon.exec()    

    f, aks_sub = mpl.subplots(6, sharex=True)
    aks_sub[0].plot(kommando_status.tid, kommando_status.a_x)
    aks_sub[1].plot(kommando_status.tid, kommando_status.a_y)
    aks_sub[2].plot(kommando_status.tid, kommando_status.a_z)
    aks_sub[3].plot(kommando_status.tid, kommando_status.aks_abs)
    aks_sub[4].plot(kommando_status.tid, kommando_status.stamp)
    aks_sub[5].plot(kommando_status.tid, kommando_status.rull)
    aks_sub[5].set_xlabel('Tid [sek]')
    aks_sub[1].set_ylabel('Akselerasjon [g]')
    aks_sub[4].set_ylabel('Vinkel [grader]')
    aks_sub[0].set_title('a_x')
    aks_sub[1].set_title('a_y')
    aks_sub[2].set_title('a_z')
    aks_sub[3].set_title('aks_abs - absolutt akselerasjon')
    aks_sub[4].set_title('Stampvinkel (om Y-aksen)')
    aks_sub[5].set_title('Rullvinkel (om X-aksen)')
    aks_sub[0].grid()
    aks_sub[1].grid()
    aks_sub[2].grid()
    aks_sub[3].grid()
    aks_sub[4].grid()
    aks_sub[5].grid()

    mpl.show()    

 # Skriv ut listene for kontroll
    print(kommando_status.tid_raa)
    print(kommando_status.tid)
    print(len(kommando_status.tid))
    #print(kommando_status.a_x_raa)
    #print(len(kommando_status.a_x_raa))
    #print(kommando_status.a_y_raa)
    #print(len(kommando_status.a_y_raa))
    #print(kommando_status.a_z_raa)
    #print(len(kommando_status.a_z_raa))
    print(kommando_status.stamp)
    print(len(kommando_status.a_x))
    print(kommando_status.rull)
    print(len(kommando_status.a_x))

    #ani=FuncAnimation(fig, update, init_func=init, interval=50, blit=True)
    #mpl.show()
