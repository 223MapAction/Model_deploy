import pytest
from app.models.image_model import ImageModel  # Adjust this import based on your project structure

class TestImageModel:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.image_model = ImageModel(image_name="test_image.jpg", sensitive_structures=["structure1", "structure2"], incident_id="1234")

    def test_init(self):
        assert isinstance(self.image_model, ImageModel)

    def test_image_name(self):
        assert self.image_model.image_name == "test_image.jpg"

    def test_sensitive_structures(self):
        assert self.image_model.sensitive_structures == ["structure1", "structure2"]

    def test_incident_id(self):
        assert self.image_model.incident_id == "1234"