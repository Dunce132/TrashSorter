from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route("/get")
def hello():
    print(request.args.get("trash"))
    print(request.args.get("recycle"))
    print(request.args.get("compost"))
    return "Trash: " + str(request.args.get("trash") + '\t\tRecycle: ' + str(request.args.get("recycle")) + '\t\tCompost: ' + str(request.args.get("compost")))


@app.route('/data', methods=['POST'])
def received_data():
    data = request.get_json()
    print(data)
    trash_count = data.get('trash', 0)
    recycle_count = data.get('recycle', 0)
    compost_count = data.get('compost', 0)
    print("Trash: " + str(trash_count) + "\nRecycle: " + str(recycle_count) + "\nCompost: " + str(compost_count))
    socketio.emit('garbage_data', {'trash': trash_count, 'recycle': recycle_count, 'compost': compost_count})
    return jsonify(success=True),200


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=80)
    socketio.run(app, debug=True)
