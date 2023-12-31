from flask import Blueprint, request, jsonify
from app.services import trips_service, file_service
from datetime import datetime

trips_blueprint = Blueprint("trips", __name__)


@trips_blueprint.route("/upload", methods=["POST"])
def upload():
    """
    Endpoint for uploading a file and ingesting data into the database.

    Returns:
        JSON: A JSON response containing the status and time taken for ingestion.

    Raises:
        400 (Bad Request): If the request does not have a file part or no file is selected.
        400 (Bad Request): If an error occurs during file writing or database ingestion.
    """
    start_time = datetime.now()
    # check if the post request has the file part
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        file_path = file_service.write_file(folder="trips/", file=file)
        trips_service.write_to_database(file_path=file_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    end_time = datetime.now()
    return (
        jsonify(
            {
                "status": "Ingestion finished sucessfully",
                "time": str(end_time - start_time),
            }
        ),
        200,
    )


@trips_blueprint.route("/get_weekly_average", methods=["POST"])
def get_weekly_average():
    """
    Endpoint for retrieving the weekly average data for a specific region or coordinates.

    Returns:
        JSON: A JSON response containing the weekly average data in records format.

    Raises:
        400 (Bad Request): If the request JSON data is malformed or missing required fields.
    """
    start_time = datetime.now()
    data = request.json

    # Validate the request data
    if "region" in data and "coordinates" in data:
        return (
            jsonify(
                {"error": "Please provide either 'region' or 'coordinates', not both"}
            ),
            400,
        )

    if "region" not in data and "coordinates" not in data:
        return (
            jsonify(
                {
                    "error": "Please provide either 'region' or 'coordinates' in the request"
                }
            ),
            400,
        )

    try:
        if "region" in data:
            df = trips_service.get_weekly_average(region=data["region"])
        else:
            coordinates = data.get("coordinates", {})
            first_point = coordinates.get("first_point")
            second_point = coordinates.get("second_point")

            if not (first_point and second_point):
                return (
                    jsonify(
                        {
                            "error": "Both 'first_point' and 'second_point' are required in 'coordinates'"
                        }
                    ),
                    400,
                )
            df = trips_service.get_weekly_average(coordinates=coordinates)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    end_time = datetime.now()
    return (
        jsonify(
            {
                "result": df.iloc[0, 0],
                "time": str(end_time - start_time),
            }
        ),
        200,
    )
