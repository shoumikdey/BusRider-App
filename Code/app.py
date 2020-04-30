from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, StringField
import time
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SECRET_KEY'] = 'hi'
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQLAlchemy(app)


class Bus_route_no(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String)
    route = db.Column(db.String)
    slots = db.Column(db.String)


class Tickets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_route = db.Column(db.String)
    route = db.Column(db.String)
    cost = db.Column(db.Integer)
    ref = db.Column(db.String)

    def __init__(self, bus_route, route, cost, ref):
        self.bus_route = bus_route
        self.route = route
        self.cost = cost
        self.ref = ref


class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_route = db.Column(db.String)
    route_count = db.Column(db.String)

    def __init__(self, bus_route, route_count):
        self.bus_route = bus_route
        self.route_count = route_count


class Tracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String)
    current_pos = db.Column(db.String)

    def __init__(self, bus_no, current_pos):
        self.bus_no = bus_no
        self.current_pos = current_pos


class Form(FlaskForm):
    bus = SelectField('bus', choices=[])
    origin = SelectField('origin', choices=[])
    destination = SelectField('destination', choices=[])
    cost = IntegerField(render_kw={"disbled": ""})


class Count_Form(FlaskForm):
    ref = StringField(render_kw={"placeholder": "Reference no"})
    bus = StringField(render_kw={"placeholder": "Bus No", "disabled": ""})
    origin = StringField(render_kw={"placeholder": "Origin", "disabled": ""})
    dest = StringField(render_kw={"placeholder": "Destination", "disabled": ""})
    cost = StringField(render_kw={"placeholder": "Cost", "disabled": ""})


class Bus_Seat_Form(FlaskForm):
    bus = SelectField('bus', choices=[], render_kw={"placeholder": "Bus no"})
    stop = SelectField('stop', choices=[], render_kw={"placeholder": "Bus Stop"})
    capacity = StringField(render_kw={"placeholder": "Capacity", "disabled": ""})


class Track_Form(FlaskForm):
    bus = SelectField('bus', choices=[])
    pos = StringField(render_kw={"placeholder": "Current Stop", "disabled": ""})


def get_route(bus, orig, dest):
    route = Bus_route_no.query.filter_by(bus_no=bus).first().route.split('-')
    s = ""
    for i in route[int(orig):int(dest)]:
        s += i + '-'
    s += route[int(dest)]
    return s


def update_count(origin, dest, count):
    # count = count.split['-']
    print(type(count))
    for i in range(int(origin), int(dest)):
        count[i] = int(count[i])
        count[i] += 1
        count[i] = str(count[i])
    s = ""
    for i in count[int(origin):int(dest)]:
        s += i + '-'
    # s += count[int(dest):]
    for i in count[int(dest):-1]:
        s += i + '-'
    s += count[len(count) - 1]
    return s


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/book/', methods=['GET', 'POST'])
def book():
    form = Form()
    buses = [(res.bus_no, res.bus_no) for res in Bus_route_no.query.all()]
    form.bus.choices = buses

    # print(list(enumerate(stop)))
    form.origin.choices = list(enumerate(Bus_route_no.query.filter_by(bus_no=buses[0][1]).first().route.split('-')))
    form.destination.choices = form.origin.choices

    if request.method == 'POST':
        refer = hashlib.sha256(str.encode(str(int(time.time()))))
        refer = str(refer.hexdigest())[:5]
        count = Count.query.filter_by(bus_route=form.bus.data).first()
        count.route_count = update_count(form.origin.data, form.destination.data, count.route_count.split('-'))
        db.session.commit()
        print(sum(list(map(int, count.route_count.split('-')))))

        tkt_upd = Tickets(form.bus.data, get_route(form.bus.data, form.origin.data, form.destination.data),
                          form.cost.data, refer)  # sum(list(map(int, count.route_count.split('-')))))
        print(tkt_upd.id)
        db.session.add(tkt_upd)
        db.session.commit()
        stop = Bus_route_no.query.filter_by(bus_no=form.bus.data).first().route.split('-')
        ticket_data = {
            'ref': refer,
            'bus': form.bus.data,
            'origin': stop[int(form.origin.data)],
            'dest': stop[int(form.destination.data)],
            'cost': form.cost.data
        }
        return render_template('confirmation.html', data=ticket_data)

        # ticket_id = Tickets.quer
        # return get_route(form.bus.data, form.origin.data, form.destination.data)

    return render_template('book.html', form=form)


@app.route('/book/<bus_no>')
def router(bus_no):
    routes = Bus_route_no.query.filter_by(bus_no=bus_no).first().route.split('-')
    # routeArr =
    # return jsonify({'origin' : str([route.route for route in routes][0])})
    arr = []
    i = 0
    for origin in routes:
        obj = {}
        obj['id'] = i
        obj['origin'] = origin
        arr.append(obj)
        i += 1
    return jsonify({'stops': arr})


@app.route('/retrieve_booking/', methods=['GET', 'POST'])
def retrieve_booking():
    form = Count_Form()

    return render_template('get_booking.html', form=form)


@app.route('/retrieve_booking/<ref>')
def get_details(ref):
    info = Tickets.query.filter_by(ref=ref).first()
    print(info.bus_route)
    arr = []
    # for inf in info:
    obj = {'bus_route': info.bus_route, 'origin': info.route.split('-')[0], 'dest': info.route.split('-')[-1], 'cost': info.cost}
    arr.append(obj)
    print(arr)
    return jsonify({'info': arr})


@app.route('/view_count/')
def view_count():
    cap_form = Bus_Seat_Form()
    buses = [(res.bus_no, res.bus_no) for res in Bus_route_no.query.all()]
    cap_form.bus.choices = buses
    cap_form.stop.choices = list(enumerate(Bus_route_no.query.filter_by(bus_no=buses[0][0]).first().route.split('-')))
    return render_template('count.html', form=cap_form)


@app.route('/view_count/<bus>')
def get_stop(bus):
    routes = Bus_route_no.query.filter_by(bus_no=bus).first().route.split('-')
    # routeArr =
    # return jsonify({'origin' : str([route.route for route in routes][0])})
    arr = []
    i = 0
    for origin in routes:
        obj = {}
        obj['id'] = i
        obj['origin'] = origin
        arr.append(obj)
        i += 1
    return jsonify({'stops': arr})


@app.route('/view_count/<bus>/<stop>')
def get_count(bus, stop):
    counter = Count.query.filter_by(bus_route=bus).first().route_count.split('-')
    arr = []
    obj = {}
    obj['count'] = counter[int(stop)]
    print(jsonify({'counter': arr}))
    return jsonify({'counter': counter[int(stop)]})


@app.route('/contact/')
def contact():
    return render_template('contact.html')


@app.route('/tracker/')
def tracker():
    form = Track_Form()
    bus = [(res.bus_no, res.bus_no) for res in Bus_route_no.query.all()]
    form.bus.choices = bus
    return render_template('tracker.html', form=form)

@app.route('/tracker/<bus>')
def get_pos(bus):
    pos = Tracker.query.filter_by(bus_no=bus).first().current_pos
    return jsonify({'pos':pos})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
