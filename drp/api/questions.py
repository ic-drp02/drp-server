from flask import request
from flask_restful import Resource, abort

from ..db import db
from ..models import Question, Site, Subject
from ..swag import swag

from .site import serialize_site
from .subject import serialize_subject


@swag.definition("Question")
def serialize_question(question):
    """
    Represents a question.
    ---
    properties:
      id:
        type: integer
      site:
        $ref: "#/definitions/Site"
      specialty:
        type: string
      subject:
        $ref: "#/definitions/Subject"
      text:
        type: string
    """
    return {
        "id": question.id,
        "site": serialize_site(question.site),
        "specialty": question.specialty,
        "subject": serialize_subject(question.subject),
        "text": question.text
    }


class QuestionResource(Resource):

    def get(self, id):
        """
        Gets a question by id.
        ---
        parameters:
          - in: path
            name: id
            type: integer
            required: true
        responses:
          200:
            schema:
              $ref: "#/definitions/Question"
          404:
            description: Not found
        """
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            return abort(404)

        return serialize_question(question)

    def delete(self, id):
        """
        Deletes a question.
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
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            return abort(404)

        db.session.delete(question)
        db.session.commit()

        return "", 204


class QuestionListResource(Resource):

    def get(self):
        """
        Gets a list of all questions.
        ---
        responses:
          200:
            description: Success
            schema:
              type: array
              items:
                $ref: "#/definitions/Question"
        """
        questions = Question.query.all()
        return [serialize_question(question)
                for question in questions]

    def post(self):
        """
        Creates a new question.
        ---
        parameters:
          - in: body
            name: question
            schema:
              type: object
              properties:
                site:
                  type: string
                  required: true
                specialty:
                  type: string
                  required: true
                subject:
                  type: string
                  required: true
                text:
                  type: string
                  required: true
        responses:
          200:
            description: Success
            schema:
              $ref: "#/definitions/Question"
          400:
            description: Invalid request
        """
        body = request.json

        site = body.get("site")
        specialty = body.get("specialty")
        subject = body.get("subject")
        text = body.get("text")

        if site is None or site == "":
            return abort(400, message="Site is required.")

        if specialty is None or specialty == "":
            return abort(400, message="Specialty is required.")

        if subject is None or subject == "":
            return abort(400, message="Subject is required.")

        if text is None or text == "":
            return abort(400, message="Text is required.")

        site = Site.query.filter(Site.name == site).one_or_none()

        if site is None:
            return abort(400, message="Site does not exist.")

        subject = Subject.query.filter(Subject.name == subject).one_or_none()

        if subject is None:
            return abort(400, message="Subject does not exist.")

        question = Question(site=site, specialty=specialty,
                            subject=subject, text=text)

        db.session.add(question)
        db.session.commit()

        return serialize_question(question)
