import csv
import json
from pathlib import Path
import logging # <-- Import logging module

from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render 

# Get an instance of a logger
logger = logging.getLogger(__name__) # <-- Logger instance
logger.setLevel(logging.INFO) # Set logger to process INFO level messages (Recommended setting for visibility)

# Assuming your views.py is inside an app directory, or directly accessible from the project root.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the definitive list of all 20 columns using the short, clean camelCase keys
ALL_CLIENT_HEADERS = [
    "sr", "clientName", "gstin", "clientType", "senior", 
    "multiRegistration", "member", "turnover", "papilioId", 
    "gstr9Status", "gstr9cStatus", "proposalStatus", 
    "targetDate", "gstr9Arn", "gstr9Date", "gstr9cArn", 
    "gstr9cDate", "mailSent", "papilioUpdate", "remarks",
]


def _read_clients_from_csv():
    """Read main client data from input_csv.csv and return list of dicts."""
    csv_path = BASE_DIR / "input_csv.csv"
    if not csv_path.exists():
        return []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_clients_to_csv(clients):
    """Overwrite input_csv.csv with provided client dicts, ensuring all headers are present."""
    csv_path = BASE_DIR / "input_csv.csv"
    
    headers = ALL_CLIENT_HEADERS

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for row in clients:
            writer.writerow(row)


def _read_single_column_csv(filename):
    """Read a simple one-column CSV (header + values) into a list of strings."""
    path = BASE_DIR / filename
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # skip header if present
        return [r[0] for r in rows[1:] if r]


def _write_single_column_csv(filename, header, values):
    """Write a single list of values into a one-column CSV file."""
    path = BASE_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([header])
        for v in values:
            writer.writerow([v])


@require_http_methods(["GET"])
def api_clients(request):
    """
    GET: return all clients as JSON list.
    """
    clients = _read_clients_from_csv()
    return JsonResponse({"clients": clients})


@csrf_exempt
def api_clients_save(request):
    """
    POST: accept full clients array and overwrite input_csv.csv.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    clients = [] 
    
    try:
        # Load the raw payload and decode it
        raw_body = request.body.decode("utf-8") or "{}"
        payload = json.loads(raw_body)
        
        clients = payload.get("clients", []) 
        
        if not isinstance(clients, list):
            raise ValueError("clients must be a list")

        # --- DEBUG LOGGING (Changed to WARN/ERROR for visibility) ---
        logger.warning(f"--- API CLIENTS SAVE TRIGGERED (Visible Log) ---")
        logger.warning(f"Received {len(clients)} client records.")

        if clients:
            # Log statuses for the first 5 clients to check for the reset issue
            for i in range(min(1, len(clients))):
                client = clients[i]
                logger.warning(
                    f"Client {i+1} Statuses: "
                    f"Name='{client.get('clientName', 'N/A')}', "
                    f"GSTR-9='{client.get('gstr9Status', 'MISSING')}', "
                    f"GSTR-9C='{client.get('gstr9cStatus', 'MISSING')}', "
                    f"Senior='{client.get('senior', 'MISSING')}'"
                    f"Member='{client.get('member', 'MISSING')}'"
                    f"Turnover='{client.get('turnover', 'MISSING')}'"
                    f"Papilio ID='{client.get('papilioId', 'MISSING')}'"
                    f"Proposal Status='{client.get('proposalStatus', 'MISSING')}'"
                    f"Target Date='{client.get('targetDate', 'MISSING')}'"
                    f"GSTR-9 ARN='{client.get('gstr9Arn', 'MISSING')}'"
                    f"GSTR-9 Date='{client.get('gstr9Date', 'MISSING')}'"
                    f"GSTR-9C ARN='{client.get('gstr9cArn', 'MISSING')}'"
                    f"GSTR-9C Date='{client.get('gstr9cDate', 'MISSING')}'"
                    f"Mail Sent='{client.get('mailSent', 'MISSING')}'"
                    f"Papilio Update='{client.get('papilioUpdate', 'MISSING')}'"
                )
            
            # Check for missing headers (sparse data check)
            first_client_keys = set(clients[0].keys())
            missing_keys = set(ALL_CLIENT_HEADERS) - first_client_keys
            if missing_keys:
                 logger.error(f"CRITICAL: Data payload is missing required keys: {missing_keys}")

        # --- END DEBUG LOGGING ---

    except Exception as exc: 
        logger.error(f"Error processing client save payload: {exc}", exc_info=True)
        return JsonResponse({"error": f"Invalid JSON payload: {str(exc)}"}, status=400)

    _write_clients_to_csv(clients)
    return JsonResponse({"status": "ok", "count": len(clients)})

@csrf_exempt
@require_http_methods(["POST"])
def api_clear_clients(request):
    """
    POST: Overwrites input_csv.csv with an empty list, clearing all client data 
    while preserving the header row structure.
    """
    logger.warning("--- CLEAR ALL CLIENT DATA TRIGGERED ---")
    try:
        # Write an empty list, forcing the CSV file to contain only the headers.
        _write_clients_to_csv([]) 
        return JsonResponse({"status": "ok", "message": "All client data cleared."})
    except Exception as exc:
        logger.error(f"Error clearing client data: {exc}", exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)




@require_http_methods(["GET"])
def api_master_data(request):
    """
    GET master/reference lists from CSVs.
    """
    data = {
        "seniors": _read_single_column_csv("seniors.csv"),
        "members": _read_single_column_csv("members.csv"),
        "proposalStatuses": _read_single_column_csv(
            "proposal_status_master.csv"
        ),
        "gstr9Statuses": _read_single_column_csv("gstr_status_master.csv"),
        "gstr9cStatuses": _read_single_column_csv("gstr_status_master.csv"),
        "customColumns": _read_single_column_csv("custom_columns.csv"),
    }
    return JsonResponse(data)


@csrf_exempt
def api_master_data_save(request):
    """
    POST updated masterData and persist it back into CSVs.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception as exc: 
        logger.error(f"Error processing master data save payload: {exc}", exc_info=True)
        return JsonResponse({"error": f"Invalid JSON payload: {str(exc)}"}, status=400)

    # Logging master data save to ensure the lists are populated
    logger.warning(f"Saving Master Data: Seniors={len(payload.get('seniors', []))}, Statuses={len(payload.get('gstr9Statuses', []))}")


    _write_single_column_csv(
        "seniors.csv", "Senior", payload.get("seniors", [])
    )
    _write_single_column_csv(
        "members.csv", "Member", payload.get("members", [])
    )
    _write_single_column_csv(
        "proposal_status_master.csv",
        "Proposal Status",
        payload.get("proposalStatuses", []),
    )
    _write_single_column_csv(
        "gstr_status_master.csv",
        "GSTR Status",
        payload.get("gstr9Statuses", []),
    )
    
    _write_single_column_csv(
        "custom_columns.csv",
        "Custom Column",
        payload.get("customColumns", []),
    )

    return JsonResponse({"status": "ok"})



@csrf_exempt
@require_http_methods(["POST"])
def api_add_senior(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        seniors = _read_single_column_csv("seniors.csv")

        if name in seniors:
            return JsonResponse({"error": "Senior already exists"}, status=400)

        seniors.append(name)
        _write_single_column_csv("seniors.csv", "Senior", seniors)

        return JsonResponse({"status": "ok", "seniors": seniors})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_senior(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()

        seniors = _read_single_column_csv("seniors.csv")

        if name not in seniors:
            return JsonResponse({"error": "Senior not found"}, status=404)

        seniors.remove(name)
        _write_single_column_csv("seniors.csv", "Senior", seniors)

        return JsonResponse({"status": "ok", "seniors": seniors})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def api_add_member(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()

        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        members = _read_single_column_csv("members.csv")

        if name in members:
            return JsonResponse({"error": "Member already exists"}, status=400)

        members.append(name)
        _write_single_column_csv("members.csv", "Member", members)

        return JsonResponse({"status": "ok", "members": members})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_member(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()

        members = _read_single_column_csv("members.csv")

        if name not in members:
            return JsonResponse({"error": "Member not found"}, status=404)

        members.remove(name)
        _write_single_column_csv("members.csv", "Member", members)

        return JsonResponse({"status": "ok", "members": members})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ---------- PROPOSAL STATUS API ----------
@csrf_exempt
@require_http_methods(["POST"])
def api_add_proposal_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        if not status:
            return JsonResponse({"error": "No status given"}, status=400)

        statuses = _read_single_column_csv("proposal_status.csv")

        if status in statuses:
            return JsonResponse({"error": "Status already exists"}, status=400)

        statuses.append(status)
        _write_single_column_csv("proposal_status.csv", "proposalStatus", statuses)

        return JsonResponse({"proposalStatuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_proposal_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        statuses = _read_single_column_csv("proposal_status.csv")
        statuses = [s for s in statuses if s != status]

        _write_single_column_csv("proposal_status.csv", "proposalStatus", statuses)

        return JsonResponse({"proposalStatuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ---------- GSTR-9 STATUS API ----------
@csrf_exempt
@require_http_methods(["POST"])
def api_add_gstr9_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        statuses = _read_single_column_csv("gstr9_status.csv")

        if status in statuses:
            return JsonResponse({"error": "Status already exists"}, status=400)

        statuses.append(status)
        _write_single_column_csv("gstr9_status.csv", "gstr9Status", statuses)

        return JsonResponse({"gstr9Statuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_gstr9_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        statuses = _read_single_column_csv("gstr9_status.csv")
        statuses = [s for s in statuses if s != status]

        _write_single_column_csv("gstr9_status.csv", "gstr9Status", statuses)

        return JsonResponse({"gstr9Statuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ---------- GSTR-9C STATUS API ----------
@csrf_exempt
@require_http_methods(["POST"])
def api_add_gstr9c_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        statuses = _read_single_column_csv("gstr9c_status.csv")

        if status in statuses:
            return JsonResponse({"error": "Status already exists"}, status=400)

        statuses.append(status)
        _write_single_column_csv("gstr9c_status.csv", "gstr9cStatus", statuses)

        return JsonResponse({"gstr9cStatuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_gstr9c_status(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        status = body.get("status", "").strip()

        statuses = _read_single_column_csv("gstr9c_status.csv")
        statuses = [s for s in statuses if s != status]

        _write_single_column_csv("gstr9c_status.csv", "gstr9cStatus", statuses)

        return JsonResponse({"gstr9cStatuses": statuses})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_add_custom_column(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        column_name = body.get("name", "").strip()

        if not column_name:
            return JsonResponse({"error": "Column name is required"}, status=400)

        columns = _read_single_column_csv("custom_columns.csv")

        if column_name in columns:
            return JsonResponse({"error": "Custom column already exists"}, status=400)

        columns.append(column_name)
        _write_single_column_csv("custom_columns.csv", "Custom Column", columns)

        return JsonResponse({"status": "ok", "customColumns": columns})

    except Exception as e:
        logger.error(f"Error adding custom column: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_remove_custom_column(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        column_name = body.get("name", "").strip()

        columns = _read_single_column_csv("custom_columns.csv")

        if column_name not in columns:
            return JsonResponse({"error": "Custom column not found"}, status=404)

        columns.remove(column_name)
        _write_single_column_csv("custom_columns.csv", "Custom Column", columns)

        return JsonResponse({"status": "ok", "customColumns": columns})

    except Exception as e:
        logger.error(f"Error removing custom column: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

import pandas as pd
# Add these imports at the top of your views.py if not already present:
# from django.core.files.storage import default_storage
# from django.core.files.base import ContentFile
# from tempfile import NamedTemporaryFile 
# --- Mapping Definitions ---
# The keys must EXACTLY match the column headers in your uploaded Excel sheet.
# Based on your input:
EXCEL_COLUMN_MAPPING = {
    'Sr': 'sr', 
    'Client Name': 'clientName',
    'GSTIN': 'gstin',
    'Client Type': 'clientType',
    'Senior': 'senior',
    'Multi Registraion': 'multiRegistration',
    'Member': 'member',
    ' Turnover ': 'turnover', # Note the spaces
    ' Papilio ID ': 'papilioId', # Note the spaces
    'GSTR-9': 'gstr9Status',
    'GSTR-9C': 'gstr9cStatus',
    'Billing Sheet': 'proposalStatus', 
    'Target Date Return to be kept ready for filing': 'targetDate',
    'GSTR-9 ARN': 'gstr9Arn',
    'GSTR-9 Date': 'gstr9Date',
    'GSTR-9C ARN': 'gstr9cArn',
    'GSTR-9C Date': 'gstr9cDate',
    'Completion mail Sent to Client': 'mailSent',
    'Update of Papilio Service': 'papilioUpdate',
    'Remarks': 'remarks'
}
# Define the final, standardized order of columns (as before)
FINAL_HEADERS = ALL_CLIENT_HEADERS 

# --- Data Cleaning Helpers (Insert these, as well) ---
# def _clean_turnover(value):
#     """Converts string values like '1.5 Cr' to numeric float."""
#     if pd.isna(value) or value == '': return 0.0
#     value = str(value).replace('₹', '').replace(',', '').strip()
#     if 'Cr' in value: return float(value.replace('Cr', '').strip()) * 10000000
#     if 'L' in value: return float(value.replace('L', '').strip()) * 100000
#     try: return float(value)
#     except ValueError: return 0.0

def _clean_status(value):
    """Standardizes GSTR status values for internal use."""
    if pd.isna(value) or str(value).strip() == '': return 'Pending'
    upper_value = str(value).upper().replace(' ', '').replace('-', '').strip()
    if 'WIP' in upper_value or 'INPROGRESS' in upper_value: return 'In Progress'
    if 'NA' in upper_value or 'NOTAPPLICABLE' in upper_value: return 'Not Applicable'
    if 'FILED' in upper_value: return 'Filed'
    return value.strip()

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["POST"])
def api_upload_tracker(request):
    """
    POST: Accepts an uploaded Excel/CSV file, extracts data from the Tracker sheet,
    maps headers, cleans data, and overwrites input_csv.csv.
    """
    logger.warning("--- API UPLOAD TRACKER STARTED ---")

    if 'file' not in request.FILES:
        logger.error("No file uploaded.")
        return JsonResponse({"error": "No file uploaded."}, status=400)

    uploaded_file = request.FILES['file']
    
    try:
        with pd.ExcelFile(uploaded_file) as xls:
            sheet_name = 'Tracker'
            if sheet_name not in xls.sheet_names:
                sheet_name = xls.sheet_names[0] 
                logger.warning(f"DEBUG: 'Tracker' sheet not found. Using first sheet: {sheet_name}")

            # FIX: Use header=2 to specifically fetch Excel Row 3 as column names
            df = pd.read_excel(xls, sheet_name=sheet_name, header=2) 
            
            # 1a. Initial Column Cleaning (before mapping)
            df.columns = df.columns.astype(str).str.strip()
            
            # --- DEBUGGING STEP 1: Check Raw Headers and Data ---
            logger.warning(f"DEBUG 1: Sheet '{sheet_name}' loaded. Shape: {df.shape}")
            logger.warning(f"DEBUG 1: Raw Columns Read by Pandas: {list(df.columns)}")
            # --- END DEBUGGING STEP 1 ---

            # --- CRITICAL FIX 1: Filter out blank rows based on 'Sr'/'Client Name' ---
            CRITICAL_COLS_TO_CHECK = ['Client Name'] 
            
            # Drop rows where ALL values are NaN (first general cleanup)
            df.dropna(how='all', inplace=True)
            
            available_critical_cols = [col for col in CRITICAL_COLS_TO_CHECK if col in df.columns]
            
            if available_critical_cols:
                # Filter: Keep rows where AT LEAST ONE of the critical columns is NOT Null/Empty
                is_critical_missing = df[available_critical_cols].isnull().all(axis=1)
                df = df[~is_critical_missing] 
            
            logger.warning(f"DEBUG: DataFrame shape after cleaning empty rows: {df.shape}")

            if 'Sr' in df.columns:
                # Identify rows where the 'Sr' column exactly matches the string 'Sr' (case-insensitive)
                # We also check for NaN/None and force conversion to string first for safety.
                is_redundant_header_row = df['Sr'].astype(str).str.strip().str.lower() == 'sr'
                
                # Filter the DataFrame to KEEP ONLY rows that are NOT redundant headers
                df = df[~is_redundant_header_row] 
                
                logger.warning(f"DEBUG: {is_redundant_header_row.sum()} redundant header/separator rows removed.")
            # --- END CRITICAL FIX 1 ---
            
            
            # --- NEW LOGIC: Remove redundant header/separator rows (Pattern: 'Client Name' == 'not applicable') ---
            if 'Client Name' in df.columns:
                # Identify rows where 'Client Name' is the specific cleanup string
                is_redundant_header_row = df['Client Name'].astype(str).str.strip().str.lower() == 'not applicable'
                
                # Filter the DataFrame to KEEP ONLY rows that are NOT redundant headers
                df = df[~is_redundant_header_row] 
                
                logger.warning(f"DEBUG: {is_redundant_header_row.sum()} redundant header/separator rows removed.")
            
            # --- END NEW LOGIC ---

            # 2. Process the data and map headers
            
            # 2a. Rename columns
            df.rename(columns=EXCEL_COLUMN_MAPPING, inplace=True)
            
            # 2b. Select and reorder columns, filling missing API columns with empty strings
            df_final = df.reindex(columns=FINAL_HEADERS).fillna('')

            # 2c. Apply data cleaning 
            df_final['turnover'] = df_final['turnover']
            df_final['multiRegistration'] = df_final['multiRegistration'].replace({'Multiple': 'Yes', 'Single': 'No', '': 'No'})
            df_final['gstr9Status'] = df_final['gstr9Status'].apply(_clean_status)
            df_final['gstr9cStatus'] = df_final['gstr9cStatus'].apply(_clean_status)
            df_final['proposalStatus'] = df_final['proposalStatus'].apply(_clean_status)
            
            # --- DEBUGGING STEP 3: Check Final Mapped Data ---
            if not df_final.empty:
                final_first_row = df_final.iloc[0].to_dict()
                log_mapped_data = {k: final_first_row.get(k, 'MISSING') for k in ['sr', 'clientName', 'gstin', 'turnover', 'gstr9Status', 'member']}
                logger.warning(f"DEBUG 3: First row data (AFTER MAPPING/CLEANING): {log_mapped_data}")
            # --- END DEBUGGING STEP 3 ---

            records = df_final.to_dict('records')

    except Exception as e:
        logger.error(f"Error during data processing/mapping: {e}", exc_info=True)
        return JsonResponse({"error": f"Error processing data mapping: {e}"}, status=500)

    # 3. Overwrite the central CSV data file
    try:
        _write_clients_to_csv(records)
        logger.warning(f"Successfully loaded and saved {len(records)} records from uploaded file.")
        
        return JsonResponse({
            "status": "ok", 
            "count": len(records),
            "message": f"Successfully updated tracker data with {len(records)} records."
        })
    except Exception as e:
        logger.error(f"Error writing to CSV: {e}", exc_info=True)
        return JsonResponse({"error": f"Server failed to save updated data: {e}"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_clear_clients(request):
    """
    POST: Overwrites input_csv.csv with an empty list, clearing all client data 
    while preserving the header row structure.
    
    This function is called by the JavaScript clearAllData() function.
    """
    logger.warning("--- CLEAR ALL CLIENT DATA TRIGGERED ---")
    
    # 1. Validation (Ensures it's a POST request, though decorator handles most of this)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        # 2. Overwrite the client CSV file with an empty list
        # This function preserves the header row based on the ALL_CLIENT_HEADERS global list.
        _write_clients_to_csv([]) 
        
        # 3. Return a successful response
        return JsonResponse({"status": "ok", "message": "All client data cleared."})
        
    except Exception as exc:
        logger.error(f"Error clearing client data: {exc}", exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)
@require_http_methods(["GET"])
def home(request):
    """Serve the single-page app template."""
    return render(request, "template.html")