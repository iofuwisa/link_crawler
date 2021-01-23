import datetime

f = None

def oepn():
    global f
    f = open('log.txt', 'w')

def printE(text):
    global f
    dt_now = datetime.datetime.now()
    log_text = dt_now.strftime('%Y-%m-%d %H:%M:%S.%f E:   ') + text
    print(log_text)
    f.write(log_text + "\n")

def printI(text):
    global f
    
    dt_now = datetime.datetime.now()
    log_text = dt_now.strftime('%Y-%m-%d %H:%M:%S.%f I:   ') + text
    print(log_text)
    f.write(log_text + "\n")

if __name__ == '__main__':
    print("this is log module.")
