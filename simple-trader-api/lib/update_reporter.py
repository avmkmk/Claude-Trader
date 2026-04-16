"""
Update Reporter

Generates human-readable summary reports from pipeline execution statistics.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from lib.update_metadata_db import UpdateMetadataDB

logger = logging.getLogger(__name__)


class UpdateReporter:
    """Generates human-readable execution summary reports"""

    def __init__(self, metadata_db: UpdateMetadataDB, start_time: datetime):
        """
        Initialize reporter.

        Args:
            metadata_db: UpdateMetadataDB instance for querying statistics
            start_time: Pipeline start time (datetime object)
        """
        self.db = metadata_db
        self.start_time = start_time

    def generate_report(self, retry_results: Optional[Dict] = None) -> str:
        """
        Generate and print human-readable summary report.

        Args:
            retry_results: Optional dict with 'success' and 'failed' counts from retry phase

        Returns:
            Report string
        """
        # Get statistics from database
        stats = self.db.get_run_statistics()

        # Calculate execution time
        end_time = datetime.now()
        elapsed_seconds = (end_time - self.start_time).total_seconds()
        elapsed_str = self._format_time(elapsed_seconds)

        # Build report
        report_lines = []
        report_lines.append("\n" + "=" * 70)
        report_lines.append("DATA UPDATE PIPELINE - EXECUTION SUMMARY")
        report_lines.append("=" * 70)
        report_lines.append("")

        # Main statistics
        report_lines.append(f"Total Stocks:        {stats['total']}")
        report_lines.append(f"Up to Date:          {stats['up_to_date']}")
        report_lines.append(f"Needs Update:        {stats['needs_update']}")
        report_lines.append("")

        # Success/failure counts
        if retry_results:
            # After retry phase
            successful = stats['total'] - stats['failed']
            failed = stats['failed']
            report_lines.append(f"Successfully Updated: {successful}")
            report_lines.append(f"Failed:               {failed}")

            if retry_results.get('retry_success', 0) > 0:
                report_lines.append(
                    f"  (Recovered by retry: {retry_results['retry_success']})"
                )
        else:
            # Before retry phase
            report_lines.append(f"Status Update Pending (check after retry phase)")

        report_lines.append("")

        # Failed stocks with error messages
        failed_stocks = self._get_failed_stocks_with_errors()
        if failed_stocks:
            report_lines.append("Failed Stocks (with errors):")
            for symbol, error in failed_stocks:
                # Truncate error message to 60 chars
                truncated_error = error[:60] + ("..." if len(error) > 60 else "")
                report_lines.append(f"  - {symbol}: {truncated_error}")
            report_lines.append("")

        # Execution time
        report_lines.append(f"Execution Time:      {elapsed_str}")
        report_lines.append("")

        # Log file location
        log_file = "data_updates.log"
        report_lines.append(f"Log File:            {log_file}")

        report_lines.append("=" * 70)
        report_lines.append("")

        # Combine and print
        report = "\n".join(report_lines)
        print(report)
        logger.info(report)

        return report

    def _get_failed_stocks_with_errors(self) -> list:
        """
        Get list of failed stocks with their error messages.

        Returns:
            List of tuples: (symbol, error_message)
        """
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT symbol, error_message FROM data_updates WHERE status = 'failed'"
        )
        rows = cursor.fetchall()
        return [(row['symbol'], row['error_message'] or "Unknown error") for row in rows]

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Format seconds into MM:SS format.

        Args:
            seconds: Elapsed time in seconds

        Returns:
            Formatted time string
        """
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"
