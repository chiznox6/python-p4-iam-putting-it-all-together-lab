#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

# -------------------------
# SIGNUP
# -------------------------
class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = User(
                username=data['username'],
                bio=data.get('bio'),
                image_url=data.get('image_url')
            )
            user.password_hash = data['password']

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already exists']}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

# -------------------------
# CHECK SESSION
# -------------------------
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'errors': ['Not logged in']}, 401

        user = User.query.get(user_id)
        if not user:
            return {'errors': ['User not found']}, 401

        return user.to_dict(), 200

# -------------------------
# LOGIN
# -------------------------
class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.authenticate(data['password']):
            return {'errors': ['Invalid username or password']}, 401

        session['user_id'] = user.id
        return user.to_dict(), 200

# -------------------------
# LOGOUT
# -------------------------
class Logout(Resource):
    def delete(self):
        if 'user_id' not in session:
            return {'errors': ['Not logged in']}, 401

        session.pop('user_id')
        return '', 204

# -------------------------
# RECIPES
# -------------------------
class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'errors': ['Unauthorized']}, 401

        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'errors': ['Unauthorized']}, 401

        data = request.get_json()
        user = User.query.get(user_id)
        try:
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user=user
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

# -------------------------
# ADD RESOURCES
# -------------------------
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
