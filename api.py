# -*- coding: utf-8 -*-
import json, time
from flask import Flask, Response, jsonify, render_template, request
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue

app = Flask(__name__)
subscriptions = []

@app.route('/health/', methods=['GET'])
def health():
    return '200 OK'

@app.route('/', methods=['GET'])
def home():
    return render_template('test.html')

class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]
        
        return "%s\n\n" % "\n".join(lines)

@app.route("/publish/epoch/end/", methods=['POST'])
def publish():
    payload = request.form.get('data')
    try:
        data = json.loads(payload)
    except:
        return {'error':'invalid payload'}

    def notify():
        msg = str(time.time())
        for sub in subscriptions[:]:
            sub.put(payload)
    
    gevent.spawn(notify)
    return "OK"

@app.route("/subscribe/epoch/end/")
def subscribe():
    def gen():
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                event = ServerSentEvent(str(result))
                yield event.encode()
        except GeneratorExit:
            subscriptions.remove(q)

    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.debug = True
    server = WSGIServer(("", 9000), app)
    server.serve_forever()
