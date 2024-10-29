from src.azure_ocr_lib.azure_ocr import AzureOCR
from decouple import config

def main():
    endpoint = config("AZURE_DOC_INTEL_ENDPOINT")
    api_key = config("AZURE_DOC_INTEL_API_KEY")

    azure_ocr = AzureOCR(endpoint, api_key)
    # azure_ocr.analyze_document("tests/data/ocr/single_line_test_document.pdf", model_id="prebuilt-layout")
    # azure_ocr.save_azure_ocr_json("tests/data/ocr/single_line_test_document_layout.json")
    azure_ocr.load_azure_ocr_json("tests/data/ocr/single_line_test_document_layout.json")
    print(azure_ocr.get_raw_text())

    print(azure_ocr.result.keys())

    azure_ocr = AzureOCR("https://test-endpoint.cognitiveservices.azure.com/", "test-api-key")
    # azure_ocr.get_raw_text()
    azure_ocr.load_azure_ocr_json("tests/data/ocr/generaldoc-drillreport.json")
    # result = azure_ocr.analyze_document("tests/data/ocr/generaldoc-drillreport.pdf")
    # azure_ocr.save_azure_ocr_json("tests/data/ocr/generaldoc-drillreport.json", result)
    # print("Azure OCR JSON saved successfully.")

    print(azure_ocr.get_raw_text())

    print(azure_ocr.result.keys())


if __name__ == "__main__":
    main()
