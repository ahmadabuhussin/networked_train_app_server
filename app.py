from flask import Flask, request, jsonify
import mysql_handler as db_handler

app = Flask(__name__)
db_handler.init()


@app.route('/', methods=['GET'])
def app_help():
    return "TEST"


@app.route('/sign', methods=['GET'])
def sign():
    try:
        user = request.args.get('user')
        password = request.args.get('password')
        check_args([user, password])
        response = db_handler.sign(user, password)
        return jsonify(response)
    except Exception as e:
        db_handler.db_connect()
        return jsonify("Error:", str(e))


@app.route('/get_stops', methods=['GET'])
def get_stops():
    return jsonify(db_handler.get_stops())


@app.route('/get_trains', methods=['GET'])
def get_trains():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        check_args([fromStop, fromStop])
        response = db_handler.get_trains(fromStop, toStop)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))


@app.route('/get_seats', methods=['GET'])
def get_seats():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        check_args([fromStop, toStop, time])
        response = db_handler.get_seats(fromStop, toStop, time)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/get_seats_num', methods=['GET'])
def get_seats_num():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        check_args([fromStop, toStop, time])
        response = db_handler.get_seats_num(fromStop, toStop, time)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/seat_status', methods=['GET'])
def seat_status():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        saved = request.args.get('saved')
        check_args([fromStop, toStop, time, seat, saved])
        response = db_handler.seat_status(fromStop, toStop, time, seat, saved)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/seat_booked_status', methods=['GET'])
def seat_booked_status():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        check_args([fromStop, toStop, time, seat])
        response = db_handler.seat_booked_status(fromStop, toStop, time, seat)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))


@app.route('/save_seat', methods=['POST'])
def save_seat():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        user_id = request.args.get('user_id')
        check_args([fromStop, toStop, time, seat, user_id])
        if len(seat.split(",")) > 1:
            user_id = [user_id] * len(seat.split(","))
            user_id = ','.join(user_id)
        db_handler.save_seat(fromStop, toStop, time, seat, user_id)
        return jsonify(True)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/get_user_seats', methods=['GET'])
def get_user_seats():
    try:
        user_id = request.args.get('user_id')
        check_args([user_id])
        response = db_handler.get_user_seats(user_id)
        return jsonify(response)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))


@app.route('/remove_seat', methods=['POST'])
def remove_seat():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        user_id = request.args.get('user_id')
        check_args([fromStop, toStop, time, seat, user_id])
        db_handler.remove_seat(fromStop, toStop, time, seat, user_id)
        return jsonify(True)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/save_taken_seat', methods=['GET'])
def save_taken_seat():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        check_args([fromStop, toStop, time, seat])
        db_handler.save_taken_seat(fromStop, toStop, time, seat)
        return jsonify(True)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))

@app.route('/remove_taken_seat', methods=['GET'])
def remove_taken_seat():
    try:
        fromStop = request.args.get('fromStop')
        toStop = request.args.get('toStop')
        time = request.args.get('time')
        seat = request.args.get('seat')
        check_args([fromStop, toStop, time, seat])
        db_handler.remove_taken_seat(fromStop, toStop, time, seat)
        return jsonify(True)
    except Exception as e:
        db_handler.db = db_handler.db_connect()
        return jsonify("Error:", str(e))


def check_args(args):
    for arg in args:
        if not arg or arg == "":
            raise Exception("wrong input parameters")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
    # app.run(host='192.168.0.100', port=8081, debug=True)

# To run app, in terminal write: flask run -h 192.168.0.103 (change IP)
