import os
import werkzeug
from datetime import datetime
from flask import current_app, request, send_from_directory
from flask_restful import Resource, abort

from ..db import db
from ..models import File, Post
from ..swag import swag


def allowed_file(filename, allowed):
    return '.' in filename \
        and filename.rsplit('.', 1)[1].lower() in allowed


@swag.definition("File")
def serialize_file(file):
    """
    Represents an uploaded file.
    ---
    properties:
      id:
        type: integer
      name:
        type: string
      post:
        type: integer
    """
    return {
        "id": file.id,
        "name": file.name,
        "post": file.post_id
    }


class FileResource(Resource):

    def get(self, id):
        """
        Gets a single file by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          200:
            schema:
              $ref: "#/definitions/File"
          404:
            description: Not found
        """
        file = File.query.filter(File.id == id).one_or_none()
        return serialize_file(file) if file is not None else abort(404)

    def delete(self, id):
        """
        Deletes a single file by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        file = File.query.filter(File.id == id).one_or_none()

        if file is None:
            return abort(404)

        os.remove(os.path.join(
            current_app.config['UPLOAD_FOLDER'], file.filename))

        db.session.delete(file)
        db.session.commit()

        return '', 204


class FileListResource(Resource):

    def get(self):
        """
        Gets a list of all files.
        ---
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/File"
        """
        return [serialize_file(file) for file in File.query.all()]

    def post(self):
        """
        Uploads a new file.
        ---
        parameters:
          - in: formData
            name: file
            type: file
            required: true
            description: The file to upload.
          - in: formData
            name: name
            type: string
            required: true
            description: The logical name of the file
          - in: formData
            name: post
            type: string
            required: true
            description: The associated post

        responses:
          200:
            schema:
              $ref: "#/definitions/File"
        """
        file_content = request.files['file']
        name = request.form['name']
        post_id = request.form['post']

        if name is None:
            return abort(400, message="`name` field is required.")

        if file_content is None:
            return abort(400, message="`file` filed is required.")

        if file_content == "":
            return abort(400, message="A valid file is required.")

        if not allowed_file(name,
                            current_app.config['ALLOWED_FILE_EXTENSIONS']):
            return abort(400, message="Unsupported file type.")

        post = Post.query.filter(Post.id == post_id).one_or_none()
        if post is None:
            return abort(400, message="Invalid post ID, associated post must "
                         "already exist.")

        # Prefix file name with current time to allow mutliple files with the
        # same name
        filename = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f_') + \
            werkzeug.utils.secure_filename(name)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if (os.path.isfile(path)):
            return abort(422, message="a file upload collision occured, "
                         "please try again later")
        file_content.save(path)

        file = File(name=name, filename=filename, post_id=int(post_id))

        db.session.add(file)
        db.session.commit()

        return serialize_file(file)


class RawFileViewResource(Resource):

    def get(self, id):
        """
        Retrieves a single raw file for viewing.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        file = File.query.filter(File.id == id).one_or_none()

        print("File:")
        print(file)

        if file is None:
            return abort(404)

        print(file.filename)
        print(current_app.config['UPLOAD_FOLDER'])

        return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                   file.filename)


class RawFileDownloadResource(Resource):

    def get(self, id):
        """
        Retrieves a single raw file for download.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        file = File.query.filter(File.id == id).one_or_none()

        print("File:")
        print(file)

        if file is None:
            return abort(404)

        print(file.filename)
        print(current_app.config['UPLOAD_FOLDER'])

        return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                   file.filename, as_attachment=True,
                                   attachment_filename=file.name)
