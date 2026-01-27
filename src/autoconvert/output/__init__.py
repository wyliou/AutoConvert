"""Output module - template generation, file writing, batch processing."""

from autoconvert.output.batch import process_batch
from autoconvert.output.file_processor import process_file
from autoconvert.output.reporter import report_batch_summary
from autoconvert.output.template import populate_template
from autoconvert.output.writer import write_output

__all__ = [
    "process_batch",
    "process_file",
    "report_batch_summary",
    "populate_template",
    "write_output",
]
