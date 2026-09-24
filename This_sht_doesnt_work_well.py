### НА ВВОД ТЕКСТОВЫЙ ФАИЛ НА ПЕРВОЙ СТРОЧКЕ БПМ И РАЗМЕР ЧЕРЕЗ ПРОБЕЛЫ (ДАЖЕ РАЗМЕР (4/4 БУДЕТ 4 : 4))
### В ОСТАЛЬНЫХ ПОСТРОЧНО ДАННЫЕ О НОТЕ ФОРМАТА >АНГЛ_НАЗВАНИЕ_БУКВОЙ ОКТАВА_ЦИФРОЙ ДЛИТЕЛЬНОСТЬ_ТИПО_КАКАЯ<
#  (> A 4 4< ГДЕ 4 ЭТО ЧЕТВЕРТАЯ, 8 ВОСЬМАЯ ИТД)
temp=0
raz=0
tabl={"A":9,"A#":10,"B":11,'C':0, "C#":1, "D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8}
from pathlib import Path
def long (razmernoti, bpm, delitel):
    dln=(((60*delitel)/bpm)/razmernoti)*1000
    return dln
def hz (vnutri, snaruzi):
    i= snaruzi*12 + tabl[vnutri]
    gerz=440*(2**((i-57)/12))
    return gerz
#pips=rf"{str(input())}"     <ЗАБИВАЕТСЯ ПУТЬ К ФАЙЛУ БЕЗ "" (ОНИ САМИ ДЕЛАЮТСЯ)
#file_path = Path(pips) <и без # он бы отсюда его читал
#  C:\Users\RBlack\Documents\testing.txt <эта мой чтоб мне копировать удобно :)
file_path = Path(r"C:\Users\RBlack\Documents\testing.txt") #  <ЭТО ЗАМЕНА 13 СТРОЧКИ ЧТОБЫ ВРУЧНУЮ НЕ ПИСАТЬ 
if file_path.exists():
    with file_path.open(mode="r", encoding="utf-8") as file:
        for line in file:
            if raz == 0:
                stroka = line.rstrip('\n')
                gol=stroka.split()
                temp=int(gol[0])
                raz=int(gol[-1])
            else:
                stroka = line.rstrip('\n')
                nota, octava, dlit=stroka.split()
                octava=int(octava)   
                dlit=float(dlit)
                a=hz(nota, octava)
                b=long(dlit,temp,raz)
                b=round(b)
                print(a,b)
                #ВЫВОДИТ ЧАСТОТУ И ДЛИТЕЛЬНОСТЬ В !!!!!!МИЛИСЕК!!!!!!!
else:
    print(f"Ошибка! Файл не найден по пути: {file_path}")
### |3===============D ###
