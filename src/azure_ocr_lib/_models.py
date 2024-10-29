from pydantic import BaseModel

class AzureDocIntelTableCell(BaseModel):
    """
    Azure Document Intelligence Table Cell
    """
    row_index: int
    column_index: int
    is_header: bool
    text: str
    # bounding_box: list[float]

class AzureDocIntelTable(BaseModel):
    """
    Azure Document Intelligence Table
    """
    row_count: int
    column_count: int
    cells: list[AzureDocIntelTableCell]

    def get_row(self, row_num: int) -> list[AzureDocIntelTableCell]:
        """Given a row number, return a list of cells in the row.

        Args:
            row_num (int): The row number to extract cells from.

        Returns:
            list: A list of cells in the row.
        """
        return [cell for cell in self.cells if cell.row_index == row_num]

    def get_column(self, col_num: int) -> list[AzureDocIntelTableCell]:
        """Given a column number, return a list of cells in the column.

        Args:
            col_num (int): The column number to extract cells from.

        Returns:
            list: A list of cells in the column.
        """
        return [cell for cell in self.cells if cell.column_index == col_num]