from flask import request
from flask_restful import Resource, abort

from sqlalchemy.exc import IntegrityError

from ..db import db
from ..models import Subject
from ..swag import swag


@swag.definition("Subject")
def serialize_subject(subject):
    """
    Represents a question subject.
    ---
    properties:
      id:
        type: integer
      name:
        type: string
    """
    return {
        "id": subject.id,
        "name": subject.name,
    }


class SubjectResource(Resource):

    def delete(self, id):
        """
        Deletes a subject.
        ---
        parameters:
          - in: path
            name: id
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        subject = Subject.query.filter(Subject.id == id).one_or_none()

        if subject is None:
            return abort(404)

        db.session.delete(subject)
        db.session.commit()

        return "", 204


class SubjectListResource(Resource):

    def get(self):
        """
        Gets a list of all subjects.
        ---
        responses:
          200:
            description: Success
            schema:
              $ref: "#/definitions/Subject"
        """
        subjects = Subject.query.all()
        return [serialize_subject(subject) for subject in subjects]

    def post(self):
        """
        Creates a new subject.
        ---
        parameters:
          - in: body
            name: subject
            schema:
              type: object
              properties:
                name:
                  type: string
                  required: true
        responses:
          200:
            description: Success
            schema:
              $ref: "#/definitions/Subject"
          422:
            description: Unprocessable entry
        """
        body = request.json

        name = body.get("name")

        if name is None:
            return abort(400, message="Name is required.")

        subject = Subject(name=name)

        db.session.add(subject)

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(
                    422, message="A subject with this name already exists.")
            else:
                raise

        return serialize_subject(subject)
