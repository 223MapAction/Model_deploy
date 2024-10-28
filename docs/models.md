# Image Model

This document provides an overview of the `ImageModel` component used in the Map Action project. The `ImageModel` is a Pydantic model that represents image data for processing and prediction in the API.

## Attributes

-   **image_name** (str): The name or path where the image is stored. This is used to fetch the image for analysis.
-   **sensitive_structures** (List[str]): A list of structures or areas in the image that are considered sensitive. This information is used to provide contextual analysis based on the prediction results.
-   **incident_id** (str): A unique identifier for the incident depicted in the image. This is used for tracking and storing results in the database.
-   **zone** (str): The geographic zone related to the image and incident.
-   **latitude** (float): The latitude coordinate of the incident location.
-   **longitude** (float): The longitude coordinate of the incident location.

The `ImageModel` is integral to the API's functionality, as it encapsulates all necessary data for image processing and prediction tasks.

For more detailed information, refer to the `image_model.py` file in the `app/models/` directory.
