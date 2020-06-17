from flask import Blueprint, request
from flask_restful import Resource, abort

from ..db import db
from ..models import Question, Site, Subject, Grade, User, Post
from ..swag import swag

from .site import serialize_site
from .subject import serialize_subject
from .posts import serialize_post


questions = Blueprint("questions", __name__)


@questions.route("/<int:qid>/resolve/<int:pid>", methods=["POST"])
def resolve(qid, pid):
    question = Question.query.filter(Question.id == qid).one_or_none()

    if question is None:
        return abort(404)

    post = Post.query.filter(Post.id == pid).one_or_none()

    if post is None:
        return abort(400, message="Invalid post ID")

    question.resolved_by = post

    db.session.commit()

    return serialize_question(question)


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
      grade:
        type: string
        enum:
          - consultant
          - spr
          - core_trainee
          - fy2
          - fy1
          - fiy1
      specialty:
        type: string
      subject:
        $ref: "#/definitions/Subject"
      resolved_by:
        $ref: "#/definitions/Post"
      text:
        type: string
    """
    return {
        "id": question.id,
        "site": serialize_site(question.site),
        "grade": question.grade.name.lower(),
        "specialty": question.specialty,
        "subject": serialize_subject(question.subject),
        "text": question.text,
        "resolved_by": serialize_post(question.resolved_by)
        if question.resolved_by is not None else None,
        "user": question.user_id,
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

    def put(self, id):
        """
        Updates a question.
        ---
        parameters:
          - in: path
            name: id
            type: integer
            required: true
          - in: body
            schema:
              type: object
              properties:
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
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            return abort(404)

        body = request.json

        if body is None:
            return abort(400, message="Missing request body.")

        text = body.get("text")

        if text is None or text == "":
            return abort(400, message="Text is required.")

        question.text = text

        db.session.commit()

        return serialize_question(question)


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
        Creates one or more new questions.
        ---
        parameters:
          - in: body
            name: question
            schema:
              type: object
              properties:
                user:
                  type: integer
                site:
                  type: string
                  required: true
                grade:
                  type: string
                  enum:
                    - consultant
                    - spr
                    - core_trainee
                    - fy2
                    - fy1
                    - fiy1
                  required: true
                specialty:
                  type: string
                  required: true
                questions:
                  type: array
                  required: true
                  items:
                    type: object
                    properties:
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
              type: array
              items:
                $ref: "#/definitions/Question"
          400:
            description: Invalid request
        """
        body = request.json

        user = body.get("user")
        site = body.get("site")
        grade = body.get("grade")
        specialty = body.get("specialty")
        questions = body.get("questions")

        if site is None or site == "":
            return abort(400, message="Site is required.")

        if grade is None or grade == "":
            return abort(400, message="Grade is required.")

        if specialty is None or specialty == "":
            return abort(400, message="Specialty is required.")

        if questions is None or questions == []:
            return abort(400, message="At least one question must be given.")

        if user is not None:
            user = User.query.filter(User.id == user).one_or_none()
            if user is None:
                return abort(400, message="User does not exist.")

        site = Site.query.filter(Site.name == site).one_or_none()

        if site is None:
            return abort(400, message="Site does not exist.")

        qs = []

        for question in questions:
            subject = question.get("subject")
            text = question.get("text")

            if subject is None or subject == "":
                return abort(400, message="Text is required.")

            if text is None or text == "":
                return abort(400, message="Text is required.")

            subject = Subject.query.filter(
                Subject.name == subject).one_or_none()

            if subject is None:
                return abort(400, message="Subject does not exist.")

            question = Question(site=site, grade=Grade[grade.upper()],
                                specialty=specialty,
                                subject=subject, text=text, user=user)

            db.session.add(question)
            qs.append(question)

        db.session.commit()

        return [serialize_question(q) for q in qs]
