from flask import current_app, send_from_directory
from flask_restful import Resource, abort

from ..models import File


def allowed_file(filename, allowed):
    return '.' in filename \
        and filename.rsplit('.', 1)[1].lower() in allowed


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

        if file is None:
            return abort(404)

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

        if file is None:
            return abort(404)

        return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                   file.filename, as_attachment=True,
                                   attachment_filename=file.name)
