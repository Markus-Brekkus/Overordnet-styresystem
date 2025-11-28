import threading

start_event = threading.Event()
stopp_event = threading.Event()

Ref_iv = int(300)
Kp_iv = int(4000)
Ti_iv = int(0)
Td_iv = int(10)

Ref_ny = Ref_iv
Kp_ny = Kp_iv
Ti_ny = Ti_iv
Td_ny = Td_iv

kommando = '0'
status = '0'

tid = []
tid_raa = []
a_x = []
a_y = []
a_z = []
aks_abs = []  # sqrt(ax**2 + ay**2 + az**2)
ayz_abs = []
rull = []     # rullvinkel psi i grader (om x-aksen)
stamp = []    # stampvinkel theta i grader (om y-aksen)

#Tid/sample håndteres internt i funksonen
avstand = 0
x_aks = 0
y_aks = 0
z_aks = 0
error = 0
power = 0
uP = 0
uI = 0
uD = 0

