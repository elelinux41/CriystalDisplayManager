from datetime import datetime, date, time, timedelta
from astral.sun import sun
from astral import moon
from astral import LocationInfo
import schedule
from urllib.request import urlopen
from urllib.error import URLError
from time import sleep
import random

ip = "192.168.68.69"

mondphasen = {
    0: "neumond",
    1: "zunehmender_sichelmond",
    2: "zunehmender_halbmond",
    3: "zunehmender_mond",
    4: "vollmond",
    5: "abnehmender_mond",
    6: "abnehmender_halbmond",
    7: "abnehmender_sichelmond"    
}
images = {
    "jupiter.jpg": 3,
    "merkur.jpg": 2,
    "pluto.jpg": 1,
    "qualle.gif": 2,
    "rick_roll.gif": 1,
    "spaceman.gif": 2,
    "torus-illusion.gif": 2,
}

images_list = []
for i,j in images.items():
    images_list += [i for k in range(j)]

city = LocationInfo("Droyßig", "Germany", "Europe/Berlin", 51.043134, 12.029732)

def befehl(befehl):
    addr = f"http://{ip}/set?{befehl}"
    print(addr)
    try:
        urlopen(addr)
    except URLError as e:
        print(e)

def tagesroutine(bis):
    def befehle():
        if all(not (start < datetime.today().time() <= end) for (start, end) in priority_times()):
            befehl("img=%2Fimage%2F"+random.choice(images_list))
            befehl("theme=2")
            sleep(60)
            befehl("theme=1")
    schedule.every(150).seconds.until(bis.isoformat(timespec="seconds")).do(befehle)
    sleep(150)
    befehl("brt=255")


def nächtliche_uhr(bis: time):
    def befehle():
        if all(not (start < datetime.today().time() <= end) for (start, end) in priority_times()):
            mondphase_schalten()
            befehl("theme=1")
    schedule.every(150).seconds.until(bis.isoformat(timespec="seconds")).do(befehle)
    sleep(150)
    befehl("brt=63")

def sonnenaufuntergang():
    befehl("img=%2Fimage%2Fsonnenuntergang.gif")
    befehl("theme=2")

def mondphase_schalten():
    float_phase = moon.phase(datetime.today().date())
    phase = int((float_phase + 1.75) // (7/2))
    phase = 0 if phase == 9 else phase
    befehl("gif=%2Fgif%2F"+mondphasen[phase]+".gif")

def significant_times():
    s = sun(city.observer, date=datetime.today().date(), tzinfo=city.tzinfo)
    if datetime.today().weekday() >= 5:
        wakeup = time(8,30)
    else:
        wakeup = time(8,35)
    if 4 <= datetime.today().weekday() <= 5:
        sleep = time(23)
    else:
        sleep = time(20,30)
    return {
        "sunrise": s["sunrise"].time(),
        "sunset": s["sunset"].time(),
        "wakeup": wakeup,
        "sleep": sleep
    }

def priority_times():
    sigtim = significant_times()
    return [
        (time_diff(sigtim["sunrise"], time(0,1,15), False), time_diff(sigtim["sunrise"], time(23,58,45), False)),
        (time_diff(sigtim["sunset"], time(0,1,15), False), time_diff(sigtim["sunset"], time(23,58,45), False))
    ]

def time_diff(t1: time, t2: time, isoformat: bool):
    """Berechnet die Differenz zwischen zwei datetime.time Objekten als time."""
    today = datetime.today().date()
    dt1 = datetime.combine(today, t1)
    dt2 = datetime.combine(today, t2)
    if isoformat:
        return (datetime(1900,1,1) + (dt1-dt2)).time().isoformat(timespec="seconds")
    else:
        return (datetime(1900,1,1) + (dt1-dt2)).time()

def mitternachtsaufgabe():
    schedule.clear("einmalig")
    sigtim = significant_times()
    schedule.every().day \
        .at(time_diff(sigtim["sunrise"], time(0,1,15), True)) \
        .do(sonnenaufuntergang).tag("einmalig")
    schedule.every().day \
        .at(time_diff(sigtim["sunset"], time(0,1,15), True)) \
        .do(sonnenaufuntergang).tag("einmalig")
    schedule.every().day.at("00:01").do(nächtliche_uhr, bis=sigtim["wakeup"]).tag("einmalig")
    schedule.every().day \
        .at(time_diff(sigtim["wakeup"], time(0,2,30), True)) \
        .do(tagesroutine, bis=sigtim["sleep"]).tag("einmalig")
    schedule.every().day \
        .at(time_diff(sigtim["sleep"], time(0,2,30), True)) \
        .do(nächtliche_uhr, bis=time(minute=3)).tag("einmalig")

print(datetime.now())
mitternachtsaufgabe()
sigtim = significant_times()
if time_diff(sigtim["wakeup"], time(0,2,30), False) < datetime.now().time() < time_diff(sigtim["sleep"], time(0,2,30), False):
    tagesroutine(sigtim["sleep"])
elif time(0,1) < datetime.now().time() < time_diff(sigtim["wakeup"], time(0,2,30), False):
    nächtliche_uhr(sigtim["wakeup"])
else:
    nächtliche_uhr(time(23,59,59))

schedule.every().day.at("00:00:20").do(mitternachtsaufgabe)
while True:
    schedule.run_pending()
    sleep(1)