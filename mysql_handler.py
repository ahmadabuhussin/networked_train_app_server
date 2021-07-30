import pymysql
import datetime
import calendar
import sys

# Open database connection
def db_connect():
    # return pymysql.connect(host="localhost", user="root", password="", database="mydb")
    return pymysql.connect(
        host="database-1.cu0m5ntyjahk.eu-west-1.rds.amazonaws.com",
        port=3306,
        user="root",
        password="12345678",
        database="mydb")

db = db_connect()

# prepare a cursor object using cursor() method
cursor = db.cursor()

STOPS = ["Beer-Sheva", "Ben Gurion Airport", "Tel Aviv", "Herzelia", "Beit Yehoshua", "Netanya", "Haifa", "Akko"]
TRAIN_LINES = [["Tel Aviv", "Herzelia", 15], ["Herzelia", "Beit Yehoshua", 14], ["Beit Yehoshua", "Netanya", 10],
               ["Tel Aviv", "Beit Yehoshua", 29], ["Tel Aviv", "Netanya", 39], ["Herzelia", "Netanya", 24],
               ["Beer-Sheva", "Tel Aviv", 76], ["Beer-Sheva", "Herzelia", 91], ["Beer-Sheva", "Beit Yehoshua", 105],
               ["Beer-Sheva", "Netanya", 115], ["Ben Gurion Airport", "Beer-Sheva", 71], ["Ben Gurion Airport", "Tel Aviv", 22],
               ["Ben Gurion Airport", "Herzelia", 29], ["Ben Gurion Airport", "Beit Yehoshua", 41], ["Ben Gurion Airport", "Netanya", 50],
               ["Haifa", "Netanya", 39], ["Haifa", "Beit Yehoshua", 49], ["Haifa", "Herzelia", 58], ["Haifa", "Tel Aviv", 50],
               ["Akko", "Tel Aviv", 56], ["Akko", "Beer-Sheva", 50], ["Akko", "Haifa", 22], ["Akko", "Netanya", 40],
               ["Akko", "Herzelia", 50], ["Akko", "Ben Gurion Airport", 66]]
HOURS = ["08:00", "08:15", "08:30", "9:00", "10:00", "11:00", "11:30", "12:00", "12:12", "12:44", "13:02", "13:40",
         "14:00", "14:30", "15:00", "16:00", "17:00", "17:27", "17:42", "17:56", "18:03", "18:17", "18:33", "18:59",
         "19:15", "19:30", "19:51", "20:00", "20:30", "21:00", "22:00", "23:00", "23:33"]
TRAIN_MAX_SEATS = 112

def init():
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
  `id` INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
  `user` VARCHAR(45) NOT NULL,
  `password` VARCHAR(45) NOT NULL)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS trains (
  `id` INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
  `fromStop` VARCHAR(45) NOT NULL,
  `toStop` VARCHAR(45) NOT NULL,
  `fromTime` VARCHAR(45) NOT NULL,
  `booked` VARCHAR(1000),
  `booked_users` VARCHAR(1000),
  `taken` VARCHAR(1000))""")


def sign(username, password):
    # checking if user already exist
    cursor.execute("""SELECT id FROM users WHERE user = %s""", username)
    exist_user = cursor.fetchone()
    if not exist_user:
        cursor.execute("""INSERT INTO users(user, password) VALUES(%s, %s)""", (username, password))
        db.commit()
    cursor.execute("""SELECT id FROM users WHERE user = %s and password = %s""", (username, password))
    response = cursor.fetchone()
    if not response:
        raise Exception("wrong username/password")
    return response[0]


def get_stops():
    return [{'label': stop, 'value': stop} for stop in STOPS]

def get_trains(startStop, endStop, tomorrow=False):
    hours = []
    now = datetime.datetime.now()
    matched_train = False
    for start, end, _ in TRAIN_LINES:
        if (start == startStop and end == endStop) or (end == startStop and start == endStop):
            matched_train = True  # we found a matching train line
            for hour in HOURS:
                h, m = hour.split(":")
                if tomorrow or int(h) > now.hour + 3 or (int(h) == now.hour + 3 and int(m) > now.minute):
                    hours.append(hour)
    if hours:  # we found hours today for this train
        dates = []
        weekdays = []
        for i in range(7):
            delta = now + datetime.timedelta(days=i)
            dates.append(str(delta.day) + "/" + str(delta.month) + "/" + str(delta.year))
            weekdays.append(calendar.day_name[delta.weekday()])
        return [dates, hours, weekdays, HOURS]
    if matched_train:  # we found the train line, but time is too late. searching the line tomorrow
        return get_trains(startStop, endStop, True)
    return []

def get_seats(fromStop, toStop, time):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT booked, taken FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """,
                   (fromStop, toStop, time))
    response = cursor.fetchall()
    print('get_seats query res: ' + str(response), file=sys.stdout)
    if not response:
        return [[], []]
    response = response[0]
    saved_seats = []
    taken_seats = []
    if response[0]:
        saved_seats = response[0].split(',')
    if response[1]:
        taken_seats = response[1].split(',')
    return [saved_seats, taken_seats]

def get_seats_num(fromStop, toStop, time):
    seats = get_seats(fromStop, toStop, time)
    available = TRAIN_MAX_SEATS - len(seats[0]) - len(seats[1])
    print('get_seats_num response: ' + str(available), file=sys.stdout)
    print('get_seats_num params: fromStop: ' + fromStop + ' ;toStop: ' + toStop + ' ;time: ' + time, file=sys.stdout) 
    return available

def seat_status(fromStop, toStop, time, seat_number, saved):
    try:
        if saved == "0":
            print('seat_status, removing seat ' + seat_number + 'from train ' + str(fromStop) + ' to ' + str(toStop) + ' at ' + str(time), file=sys.stdout)
            remove_taken_seat(fromStop, toStop, time, seat_number)
        elif saved == "1":
            print('seat_status, saving seat ' + seat_number + 'from train ' + str(fromStop) + ' to ' + str(toStop) + ' at ' + str(time), file=sys.stdout)
            save_taken_seat(fromStop, toStop, time, seat_number)
    except Exception as e:
        print('seat_status got an error... recovering', file=sys.stdout)
    if saved == "0":
        return "available"
    else:
        return "occupied"
    

def seat_booked_status(fromStop, toStop, time, seat_number):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT * FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """, (fromStop, toStop, time))
    response = cursor.fetchall()
    print('seat_booked_status query res: ' + str(response), file=sys.stdout)
    if not response or len(response) == 0:
        return "not booked"
    response = response[0]
    booked_seats = []
    saved_seats = []
    if response[4]:
        booked_seats = response[4].split(",")
    if response[6]:
        saved_seats = response[6].split(",")
    print('seat_booked_status this is booked_seats: ' + str(booked_seats), file=sys.stdout)
    print('seat_booked_status this is saved_seats: ' + str(saved_seats), file=sys.stdout)
    if seat_number in booked_seats or seat_number in saved_seats:
        return "booked"
    else:
        return "not booked"

def save_seat(fromStop, toStop, time, seat_number, user_id):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT * FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """, (fromStop, toStop, time))
    response = cursor.fetchone()
    print('got here')
    print('save_seat query res: ' + str(response), file=sys.stdout)
    # if int(seat_number) < 0 or int(seat_number) < 0:
    #     raise Exception("Wrong input parameters")
    if response:
        print('get_seats response is not null', file=sys.stdout)
        # specific train was saved before in db, editing and checking it
        booked_seats = response[4]
        booked_users = response[5]
        taken_seats = response[6]
        if seat_number in taken_seats.split(",") or seat_number in booked_seats.split(","):
            print("exception - seat is already booked/taken", file=sys.stdout)
            raise Exception("seat is already booked/taken")
        if len(taken_seats.split(",")) + len(booked_seats.split(",")) >= TRAIN_MAX_SEATS:
            print("exception - train is full", file=sys.stdout)
            raise Exception("train is full")
        if booked_seats != "":
            print("save_seat booked_seats list is not empty, adding seat " + seat_number + "with user_id " + user_id, file=sys.stdout)
            booked_seats += "," + seat_number
            booked_users += "," + user_id
        else:
            print("save seat booked_seats list is empty, setting booked_seats=" + seat_number + "and booked_users=" + user_id, file=sys.stdout)
            booked_seats = seat_number
            booked_users = user_id
        print('save_seat UPDATE vars: \nbooked seats: ' + str(booked_seats) + '\nbooked_users: ' + str(booked_users) + '\nfromStop: ' + str(fromStop) 
                + '\ntoStop: ' + str(toStop) + '\n time: ' + str(time), file=sys.stdout)
        cursor.execute("""UPDATE trains SET booked = %s, booked_users = %s WHERE fromStop = %s and toStop = %s and fromTime = %s;""",
                       (booked_seats, booked_users, fromStop, toStop, time))
    else:
        print("got to else")
        # inserting train's row
        print('save_seat INSERT vars: \nbooked seats: ' + seat_number + '\nbooked_users: ' + user_id + '\nfromStop: ' + str(fromStop) 
                                + '\ntoStop: ' + str(toStop) + '\n time: ' + str(time), file=sys.stdout)
        cursor.execute("""INSERT INTO trains(fromStop, toStop, fromTime, booked, booked_users, taken) 
                VALUES(%s, %s, %s, %s, %s, %s)""", (fromStop, toStop, time, seat_number, user_id, ""))
    db.commit()


def remove_seat(fromStop, toStop, time, seat_number, user_id):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT * FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """, (fromStop, toStop, time))
    response = cursor.fetchone()
    print('remove_seat this is query res: ' + str(response), file=sys.stdout)
    if int(seat_number) < 0 or int(seat_number) < 0:
        raise Exception("Wrong input parameters")
    if not response:
        raise Exception("No matching train found")
    booked_seats = response[4].split(",")
    booked_users = response[5].split(",")
    if seat_number not in booked_seats:
        raise Exception("Cannot remove. this seat is not saved")
    for i in range(len(booked_seats)):
        if seat_number == booked_seats[i] and user_id != booked_users[i]:
            raise Exception("Cannot remove. This seat is saved by another user!")
        if seat_number == booked_seats[i] and user_id == booked_users[i]:
            if i == 0:
                if len(booked_seats) == 1:
                    booked_seats = ""
                    booked_users = ""
                else:
                    booked_seats = response[4].replace(seat_number + ",", "", 1)
                    booked_users = response[5].replace(user_id + ",", "", 1)
            else:
                booked_seats = response[4].replace("," + seat_number, "", 1)
                booked_users = response[5].replace("," + user_id, "", 1)
            # updating the train with current seats
            print('remove_seat UPDATE \nfromStop: ' + str(fromStop) + '\ntoStop: ' + str(toStop) + '\n time: ' + str(time) + '\nseat_number: '
                    + str(seat_number) + '\nuser_id: ' + str(user_id), file=sys.stdout)
            cursor.execute("""UPDATE trains SET booked = %s, booked_users = %s WHERE fromStop = %s and toStop = %s and fromTime = %s;""",
                           (booked_seats, booked_users, fromStop, toStop, time))
            db.commit()
            return

def get_user_seats(user_id):
    cursor.execute("""SELECT * FROM trains""")
    response = cursor.fetchall()
    trains = []
    for row in response:
        cur_users = row[5].split(",")
        for i in range(len(cur_users)):
            if user_id == cur_users[i]:
                trains.append([row[1], row[2], row[3], row[4].split(",")[i]])
    trains.sort(key=lambda x: int(x[3]))
    trains.sort(key=lambda x: x[2])
    return trains


def save_taken_seat(fromStop, toStop, time, seat_number):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT * FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """, (fromStop, toStop, time))
    response = cursor.fetchone()
    print('save_taken_seat query result: ' + str(response), file=sys.stdout)
    if int(seat_number) < 0 or int(seat_number) < 0:
        raise Exception("Wrong input parameters")
    if response:
        # specific train was saved before in db, editing and checking it
        booked_seats = response[4]
        taken_seats = response[6]
        if seat_number in taken_seats.split(",") or seat_number in booked_seats.split(","):
            raise Exception("seat is already booked/taken")
        if len(taken_seats.split(",")) + len(booked_seats.split(",")) >= TRAIN_MAX_SEATS:
            raise Exception("train is full")
        if taken_seats != "":
            taken_seats += "," + seat_number
        else:
            taken_seats = seat_number
        cursor.execute("""UPDATE trains SET taken = %s WHERE fromStop = %s and toStop = %s and fromTime = %s;""",
                       (taken_seats, fromStop, toStop, time))
    else:
        # inserting train's row
        print('save_taken_seat UPDATE fromStop: ' + str(fromStop) + '\ntoStop: ' + str(toStop) + '\n time: ' + str(time) + '\nseat_number: ' + str(seat_number), file=sys.stdout)
        cursor.execute("""INSERT INTO trains(fromStop, toStop, fromTime, booked, booked_users, taken) VALUES(%s, %s, %s, %s, %s, %s)""",
                       (fromStop, toStop, time, "", "", seat_number))
    db.commit()


def remove_taken_seat(fromStop, toStop, time, seat_number):
    fromStop = fromStop.lower()
    toStop = toStop.lower()
    cursor.execute("""SELECT * FROM trains WHERE fromStop = %s and toStop = %s and fromTime = %s """, (fromStop, toStop, time))
    response = cursor.fetchone()
    print('remove_taken_seat response: ' + str(response), file=sys.stdout)
    if int(seat_number) < 0 or int(seat_number) < 0:
        raise Exception("Wrong input parameters")
    if not response:
        raise Exception("No matching train found")
    taken_seats = response[6].split(",")
    if seat_number not in taken_seats:
        raise Exception("Cannot remove. this seat is not taken")
    for i in range(len(taken_seats)):
        if seat_number == taken_seats[i]:
            if i == 0:
                if len(taken_seats) == 1:
                    taken_seats = ""
                else:
                    taken_seats = response[6].replace(seat_number + ",", "")
            else:
                taken_seats = response[6].replace("," + seat_number, "")
            # updating the train with current seats
            cursor.execute("""UPDATE trains SET taken = %s WHERE fromStop = %s and toStop = %s and fromTime = %s;""",
                           (taken_seats, fromStop, toStop, time))
            print('remove_taken_seat UPDATE vars: \ntaken_seats: ' + str(taken_seats) + '\nfromStop: ' + str(fromStop) 
                                    + '\ntoStop: ' + str(toStop) + '\n time: ' + str(time), file=sys.stdout)
            db.commit()
            return

def close():
    # disconnect from server
    db.close()
