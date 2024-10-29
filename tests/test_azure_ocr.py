import pytest
from src.azure_ocr_lib import AzureOCR
import os

@pytest.fixture
def azure_ocr():
    return AzureOCR("https://test-endpoint.cognitiveservices.azure.com/", "test-api-key")


@pytest.fixture
def azure_ocr_json(azure_ocr):
    return_obj = AzureOCR("https://test-endpoint.cognitiveservices.azure.com/", "test-api-key")
    return_obj.load_azure_ocr_json("tests/data/ocr/generaldoc-drillreport.json")
    return return_obj

def test_analyze_document_result_none(azure_ocr):
    # confirm that the result is None when the class is created but no analysis has been done
    assert azure_ocr.result is None

def test_analyze_document_result_not_none(azure_ocr):
    assert 1 == 1
    # confirm that the result is not None after the analysis has been done
    # TODO: Mocking the actual analysis
    # azure_ocr.analyze_document("tests/data/ocr/generaldoc-drillreport.pdf")
    # assert azure_ocr.result is not None

def test_load_azure_ocr_json_valid_json(azure_ocr):
    # confirm that the result is not None after loading the json
    azure_ocr.load_azure_ocr_json("tests/data/ocr/generaldoc-drillreport.json")
    assert azure_ocr.result is not None

def test_load_azure_ocr_json_invalid_json(azure_ocr):
    with pytest.raises(FileNotFoundError):
        azure_ocr.load_azure_ocr_json("tests/data/ocr/nonexistent.json")

def test_load_azure_ocr_json_invalid_json_content(azure_ocr):
    with pytest.raises(ValueError):
        azure_ocr.load_azure_ocr_json("tests/data/ocr/invalid_ocr.json")

def test_save_azure_ocr_json(azure_ocr_json):
    filename = "tests/data/ocr/test_generaldoc-drillreport.json"

    azure_ocr_json.save_azure_ocr_json(filename)
    assert os.path.exists(filename)
    # delete file after test
    os.remove(filename)

def test_save_azure_ocr_json_result_none(azure_ocr):
    # since no analysis has been done, there is no result to save
    with pytest.raises(ValueError):
        azure_ocr.save_azure_ocr_json("tests/data/ocr/test_generaldoc-drillreport.json")

def test_save_azure_ocr_json_no_result(azure_ocr):
    # since no analysis has been done, there is no result to save
    with pytest.raises(ValueError):
        azure_ocr.save_azure_ocr_json("tests/data/ocr/test_generaldoc-drillreport.json")

# TODO: test __gest_nested_obj_for_key
# TODO: test __update_max_page_count

def test_get_raw_text_valid(azure_ocr_json):
    assert azure_ocr_json.get_raw_text() == "This is a test document for Azure OCR."

def test_get_raw_text_no_result(azure_ocr):
    with pytest.raises(ValueError):
        azure_ocr.get_raw_text()

def test_get_raw_text_not_supported_model_id(azure_ocr_json):
    with pytest.raises(ValueError):
        azure_ocr_json.get_raw_text(model_id="not-supported-model-id")

def test_get_words_from_page_valid(azure_ocr_json):
    words = azure_ocr_json.get_words_from_page(1)
    validation_words = ["This", "is", "a", "test", "document", "for", "Azure", "OCR."]
    assert len(words) == len(validation_words)
    for i in range(len(words)):
        assert words[i] == validation_words[i]

def test_get_words_from_page_no_result(azure_ocr):
    with pytest.raises(ValueError):
        azure_ocr.get_words_from_page(1)

def test_get_words_from_page_below_min_page(azure_ocr_json):
    with pytest.raises(ValueError):
        azure_ocr_json.get_words_from_page(0)

def test_get_words_from_page_above_max_page(azure_ocr_json):
    with pytest.raises(ValueError):
        azure_ocr_json.get_words_from_page(999)

def test_get_words_from_page_below_min_confidence(azure_ocr_json):
    words = azure_ocr_json.get_words_from_page(1, min_confidence=1.0)
    assert len(words) == 0

# TODO: get_selection_marks_from_page
# TODO: get_lines_from_page
# TODO: get_tables_from_page
# TODO: get_key_value_pairs_from_page
# TODO: get_specific_words_from_page

