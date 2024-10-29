from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

from ._models import AzureDocIntelTableCell, AzureDocIntelTable

from functools import wraps
import json
import os

def require_azure_ocr_result(func):
    """
        Decorator that checks if `self.result` exists before executing the wrapped function.
        Raises ValueError if `self.result` is None.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.result is None:
            raise ValueError("No Azure OCR result found.")
        return func(self, *args, **kwargs)

    return wrapper

class AzureOCR:
    def __init__(self, endpoint: str, api_key: str):
        self.__doc_intel_client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(api_key))
        self.result = None
        self.max_page_count = 1

    def analyze_document(self, file: str, language: str = "en", model_id: str = "prebuilt-document") -> None:
        """Takes a filename as input, run OCR on it and stores the resulting object in `self.result`.

        WARNING: Charges will occur in Azure when you run this function.

        Args:
            file (str): a filename
            language (str, optional): The language to parse the file. Defaults to "en".
            model_id (str, optional): The model ID to use. Defaults to "prebuilt-document".

        Returns:
            None
        """
        with open(file, "rb") as f:
            # TODO: support URL as input
            poller = self.__doc_intel_client.begin_analyze_document(
                model_id=model_id, analyze_request=f, content_type="application/octet-stream", locale=language
            )
            self.result = poller.result()
            self.__update_max_page_count()



    def load_azure_ocr_json(self, filename: str) -> None:
        """Load an Azure OCR JSON file and stores the resulting object in `self.result`.

        Args:
            filename (str): The filename of the Azure OCR JSON file.

        Returns:
            None

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        if not os.path.exists(filename):
            raise FileNotFoundError(f"The file {filename} does not exist.")

        with open(filename, "r") as f:
            self.result = json.load(f)

        # if "analyzeResult" not in self.result:
        #     raise ValueError("The JSON file does not contain an 'analyzeResult' key. This is not a valid Azure OCR JSON file.")

    @require_azure_ocr_result
    def save_azure_ocr_json(self, filename: str) -> None:
        """Save an Azure OCR dict object and save it as a json.

        Args:
            filename (str): The filename of the json you want to save to.

        Returns:
            None

        Raises:
            ValueError: If no Azure OCR result was found.
        """
        with open(filename, "w") as f:
            json.dump(self.result.as_dict(), f, indent=4)

    # --------------------------
    # Helper Functions
    # ---------------------------
    @require_azure_ocr_result
    def __get_nested_obj_for_key(self, key: str) -> dict | None:
        """Given a key, return the nested object found (max depth 1) in the Azure OCR result. If none is found,
        return None.

        NOTE: Assumes `self.result` is not None
        Args:
            key (str): The key you want to search for in the Azure OCR result.

        Returns:
            dict | None: The nested object with the key, or None if we can't find it in self.result["anaylzeResult"]
                         or self.result.
        """
        # TODO: handle nested objects with more than 1 depth

        ANALYZE_RESULT_STR = "analyzeResult"

        found_nested_obj = None
        if ANALYZE_RESULT_STR in self.result:
            if key in self.result[ANALYZE_RESULT_STR]:
                found_nested_obj = self.result[ANALYZE_RESULT_STR][key]
        else:
            if key in self.result:
                found_nested_obj = self.result[key]
        return found_nested_obj

    @require_azure_ocr_result
    def __update_max_page_count(self) -> None:
        """Return the maximum page count found in the Azure OCR result.

        Returns:
            int: The maximum page count found in the Azure OCR result.
        """
        # self.max_page_count
        max_page_count = 1
        if pages := self.__get_nested_obj_for_key("pages"):
            max_page_count = max([page["page"] for page in pages])

        self.max_page_count = max_page_count

    # --------------------------
    # Page Functions
    #---------------------------

    @require_azure_ocr_result
    def get_raw_text(self) -> str:
        """Given an Azure OCR result object, return the raw text generated from Azure OCR. If none
        is provided, it will attempt to get the OCR object stored when the analyze_document function
        was run.

        Args:

        Raises:
            ValueError: If no Azure OCR result was found.

        Returns:
            str: the raw string produced from Azure Document Intelligence OCR.
        """
        # TODO: handle the various prebuilt models and how they store content.
        if self.result["modelId"] == "prebuilt-document":
            return self.result["analyzeResult"]["content"]
        elif self.result["modelId"] == "prebuilt-layout":
            return self.result["content"]
        else:
            raise ValueError("Non Implemented model_id found in Azure OCR result.")

    @require_azure_ocr_result
    def get_words_from_page(self, page_number: int = -1, minimal_confidence: float = 0.0) -> list[str]:
        """Given a page number, return a list of words found in the page.

        NOTE: page numbers start at 1.

        Args:
            page_number (int): The page number to extract words from. -1 to get all pages.
            minimal_confidence (float, optional): The minimal confidence level to extract words. Defaults to 0.0.

        Returns:
            list: A list of words found in the page.
        """

        # check if the page_number is valid
        if page_number != -1:
            if (page_number == 0 or
                    page_number < -1 or
                    page_number > self.max_page_count):
                raise ValueError(f"Invalid page number. Page number must be between 1 and {self.result['analyzeResult']['pageCount']}.")

        words = []
        for page in self.result["analyzeResult"]["pages"]:
            if page_number == -1 or page["page"] == page_number:
                for word in page["words"]:
                    if word["confidence"] >= minimal_confidence:
                        words.append(word["content"])
        return words

    @require_azure_ocr_result
    def get_selection_marks_from_page(self, page_number: int = -1, minimal_confidence: float = 0.0) -> list[bool]:
        """Given a page number, return a list of selection marks found in the page.

        NOTE: page numbers start at 1.

        Args:
            page_number (int): The page number to extract selection marks from. -1 to get all pages.
            minimal_confidence (float, optional): The minimal confidence level to extract selection marks. Defaults to 0.0.

        Returns:
            list: A list of selection marks found in the page.
        """

        selection_marks = []

        page_nested_obj = self.__get_nested_obj_for_key("pages")
        if page_nested_obj is None:
            # no pages found
            return selection_marks

        for page in page_nested_obj:
            if page_number == -1 or page["page"] == page_number:
                for selection_mark in page["selectionMarks"]:
                    if selection_mark["confidence"] >= minimal_confidence:
                        selection_marks.append(selection_mark["state"] == "selected")
        return selection_marks

    @require_azure_ocr_result
    def get_lines_from_page(self, page_number: int = -1) -> list[str]:
        """Given a page number, return a list of lines found in the page.

        NOTE: page numbers start at 1.
        NOTE: lines in Azure Document Intelligence do not have a confidence value.

        Args:
            page_number (int): The page number to extract lines from. -1 to get all pages.

        Returns:
            list: A list of lines found in the page.
        """

        lines = []

        page_nested_obj = self.__get_nested_obj_for_key("pages")
        if page_nested_obj is None:
            # no pages found
            return lines

        for page in page_nested_obj:
            if page_number == -1 or page["page"] == page_number:
                for line in page["lines"]:
                    lines.append(line["content"])
        return lines

    @require_azure_ocr_result
    def get_tables_from_page(self, page_number: int = -1) -> list[AzureDocIntelTable]:
        """Given a page number, return a list of tables found in the page.

        NOTE: page numbers start at 1.

        Args:
            page_number (int): The page number to extract tables from. -1 to get all pages.

        Returns:
            list: A list of tables found in the page.
        """

        tables = []

        tables_nested_obj = self.__get_nested_obj_for_key("tables")
        if tables_nested_obj is None:
            # no pages found
            return tables

        for table in tables_nested_obj:
            # TODO: check if there is every a case where a table spans multiple pages
            if page_number == -1 or table["boundingRegions"][0]["pageNumber"] == page_number:
                azure_cells = []
                for cell in table["cells"]:
                    if page_number == -1 or cell["boundingRegions"][0]["pageNumber"] == page_number:
                        azure_cells.append(
                            AzureDocIntelTableCell(
                                row_index=cell["rowIndex"],
                                column_index=cell["columnIndex"],
                                is_header="kind" in cell,
                                text=cell["content"],
                            )
                        )
                tables.append(
                    AzureDocIntelTable(
                        row_count=table["rowCount"],
                        col_count=table["columnCount"],
                        cells=azure_cells
                    )
                )
        return tables

    @require_azure_ocr_result
    def get_key_value_pairs_from_page(self, page_number: int = -1) -> dict:
        """Given a page number, return a dictionary of key value pairs found in the page.

        NOTE: page numbers start at 1.

        Args:
            page_number (int): The page number to extract key value pairs from. -1 to get all pages.

        Returns:
            dict: A dictionary of key value pairs found in the page.
        """

        key_value_pairs = {}

        kv_nested_obj = self.__get_nested_obj_for_key("keyValuePairs")
        if kv_nested_obj is None:
            # no pages found
            return key_value_pairs

        for key_value_pair in kv_nested_obj:
            if page_number == -1 or key_value_pair["boundingRegions"][0]["pageNumber"] == page_number:
                key = key_value_pair["key"]["content"]
                value = key_value_pair["value"]["content"]
                key_value_pairs[key] = value
        return key_value_pairs

    @require_azure_ocr_result
    def get_specific_fields(self, field_names: list[str], minimum_value_confidence: float = 0.0) -> dict:
        """Given a list of field names, return a dictionary of field names and their values.

        Args:
            field_names (list[str]): A list of field names to extract.
            minimum_value_confidence (float, optional): The minimal confidence level to extract selection marks. Defaults to 0.0.

        Returns:
            dict: A dictionary of field names and their values.
        """

        #TODO: fuzzy matching fields?
        fields = {}

        kv_nested_obj = self.__get_nested_obj_for_key("keyValuePairs")
        if kv_nested_obj is None:
            # no pages found
            return fields

        for field in kv_nested_obj:
            key_name = field["key"]["content"]
            if key_name in field_names:
                if field["value"]["confidence"] >= minimum_value_confidence:
                    fields[key_name] = field["value"]["content"]
        return fields