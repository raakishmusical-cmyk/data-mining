import os
import csv
import pandas as pd
import zipfile
from pathlib import Path
from backend.utils.logger import logger

HEADERS = [
    "Organization Name", "Salutation", "First Name", "Last Name", "Title",
    "Email", "Secondary Email", "Phone", "Mobile", "Fax", "Skype ID",
    "Website", "Instagram", "Facebook", "LinkedIn", "Twitter", "YouTube",
    "Street", "City", "State", "Zip Code", "Country", "Industry"
]

class ExcelWorker:
    def init_filepaths(self, district: str, keyword: str, output_dir: str = "Output/Mining") -> tuple[str, str]:
        """Creates unique names for CSV and Excel outputs."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_district = re.sub(r'[^a-zA-Z0-9_]', '_', district)
        safe_keyword = re.sub(r'[^a-zA-Z0-9_]', '_', keyword)
        
        base_name = f"{safe_district}_{safe_keyword}_{timestamp}"
        
        csv_path = os.path.join(output_dir, f"{base_name}.csv")
        xlsx_path = os.path.join(output_dir, f"{base_name}.xlsx")
        
        # Ensure directories exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize CSV with headers
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(HEADERS)
            
        return csv_path, xlsx_path

    def write_batch(self, csv_path: str, rows: list[list]) -> bool:
        """Appends rows to the CSV file. Retries on lock errors."""
        import time
        for attempt in range(5):
            try:
                with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(rows)
                return True
            except PermissionError:
                logger.warning(f"CSV {csv_path} locked by another process (e.g. Excel). Retrying in 1s...")
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Failed writing rows to CSV: {e}")
                break
        return False

    def compile_csv_to_excel(self, csv_path: str, xlsx_path: str) -> bool:
        """Compiles a written CSV to a clean styled Excel workbook."""
        try:
            if not os.path.exists(csv_path):
                return False
                
            df = pd.read_csv(csv_path)
            
            # Ensure columns are in the exact order specified
            # Fill missing columns
            for col in HEADERS:
                if col not in df.columns:
                    df[col] = "N/A"
                    
            df = df[HEADERS]
            
            # Save to Excel
            with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Leads")
                
                # Auto-adjust column widths
                workbook = writer.book
                worksheet = writer.sheets["Leads"]
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
                    
            return True
        except Exception as e:
            logger.error(f"Failed to compile Excel file: {e}", exc_info=True)
            return False

    def create_zip_archive(self, file_paths: list[str], zip_output_path: str) -> bool:
        """Compresses multiple files into a single ZIP file."""
        try:
            os.makedirs(os.path.dirname(zip_output_path), exist_ok=True)
            with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for fp in file_paths:
                    if os.path.exists(fp):
                        zipf.write(fp, arcname=os.path.basename(fp))
            logger.info(f"Created ZIP archive: {zip_output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create ZIP: {e}")
            return False

import re
excel_worker = ExcelWorker()
