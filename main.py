import os
from datetime import datetime as dt
from flask import Flask
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
api = Api(app)
baseDir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ReminderModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    appointment_type = db.Column(db.String(10))
    appointment = db.Column(db.DateTime,)
    address = db.Column(db.String(100),)
    description = db.Column(db.String(150),)
    people_concerned = db.Column(db.String(100))
    creation_date = db.Column(db.DateTime, default=dt.now)

    def __repr__(self):
        return f"Reminder(name = {self.name}, appointment_type = {self.appointment_type}, appointment = {self.appointment}, address = {self.address}, description = {self.description}, people_concerned = {self.people_concerned})"

#db.create_all()

reminder_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'appointment_type': fields.String,
    'appointment': fields.DateTime,
    'address': fields.String,
    'description': fields.String,
    'people_concerned': fields.String,
    'creation_date': fields.DateTime
}

reminder_post_args = reqparse.RequestParser()
reminder_post_args.add_argument("id", type=int)
reminder_post_args.add_argument("name", type=str, help="Name required", required=True)
reminder_post_args.add_argument("appointment_type", type=str)
reminder_post_args.add_argument('appointment', type=lambda x: dt.strptime(x,'%Y-%m-%dT%H:%M:%S'))
reminder_post_args.add_argument("address", type=str)
reminder_post_args.add_argument("description", type=str)
reminder_post_args.add_argument("people_concerned", type=str)
reminder_post_args.add_argument("creation_date", type=dt)

reminder_put_args = reqparse.RequestParser()
reminder_put_args.add_argument("name", type=str, help="Name required", required=True)
reminder_put_args.add_argument("appointment_type", type=str)
reminder_put_args.add_argument('appointment', type=lambda x: dt.strptime(x,'%Y-%m-%dT%H:%M:%S'))
reminder_put_args.add_argument("address", type=str)
reminder_put_args.add_argument("description", type=str)
reminder_put_args.add_argument("people_concerned", type=str)

reminder_delete_args = reqparse.RequestParser()
reminder_delete_args.add_argument("name", type=str, help="Name required", required=True)

class ReminderResource(Resource):
    def get(self):
        reminders = ReminderModel.query.all()
        return marshal(reminders, reminder_fields)

    def post(self):
        try:
            args = reminder_post_args.parse_args()
            reminder = ReminderModel(id=args['id'], name=args['name'], 
                                     appointment_type=args['appointment_type'], 
                                     appointment=args['appointment'], address=args['address'], 
                                     description=args['description'], 
                                     people_concerned=args['people_concerned'], 
                                     creation_date=args['creation_date'])
            db.session.add(reminder)
            db.session.commit()
        except BadRequest as error:
            print(error.data)
            return error.data, 400
        except IntegrityError as error:
            print(error)
            return error.orig.args[0], 400

        return marshal(reminder, reminder_fields)

    def put(self):
        try:
            ignore_props = ['id', 'name', 'query', 'metadata', 'query_class']
            args = reminder_put_args.parse_args()
            reminder_to_update = ReminderModel.query.filter(ReminderModel.name.like(args['name'])).first()

            if reminder_to_update is None:
                return "Reminder not found", 404

            props = [p for p in dir(ReminderModel) if not p.startswith('_') and p not in ignore_props]
            for prop in props:
                if prop in args and args[prop] is not None:
                    setattr(reminder_to_update, prop, args[prop])
                    print(f'{prop}: {args[prop]}')

            db.session.add(reminder_to_update)
            db.session.commit()
            return marshal(reminder_to_update, reminder_fields)
        except BadRequest as error:
            print(error.data)
            return error.data, 400

    def delete(self):
        try:
            args = reminder_delete_args.parse_args()
            reminder_to_delete = ReminderModel.query.filter(ReminderModel.name.like(args['name'])).first()

            if reminder_to_delete is None:
                return "Reminder not found", 404

            db.session.delete(reminder_to_delete)
            db.session.commit()
        except BadRequest as error:
            print(error.data)
            return error.data, 400
        
        return marshal(reminder_to_delete, reminder_fields)

api.add_resource(ReminderResource, '/reminder')

if __name__ == '__main__':
    app.run(debug=True)
