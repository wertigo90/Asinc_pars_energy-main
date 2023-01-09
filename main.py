import time


def printing(i):
    print(i)

for i in range(10):
    try:
        print("lol")
        time.sleep(1)
    except Exception as ex:
        print("errr")
        break
    finally:
        printing(i)



