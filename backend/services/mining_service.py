import asyncio
import time
import uuid
import os
from datetime import datetime
from backend.utils.logger import logger
from backend.workers.queue_manager import queue_manager
from backend.workers.maps_worker import maps_worker
from backend.workers.website_worker import website_worker
from backend.workers.classification_worker import classification_worker
from backend.workers.excel_worker import excel_worker
from backend.workers.checkpoint_manager import checkpoint_manager
from backend.services.settings_service import settings_service
from backend.services.history_service import history_service
from backend.database.sqlite import db
from backend.utils.translator import translate_to_english_async
from backend.utils.normalizer import validate_business_record, DuplicateDetector
from playwright.async_api import async_playwright
import pandas as pd

class KeywordExecutionResult:
    def __init__(self, district: str, keyword: str):
        self.district = district
        self.keyword = keyword
        self.status = "Skipped"  # Completed, Failed, Zero Results, Skipped
        self.businesses_found = 0
        self.businesses_saved = 0
        self.duplicates = 0
        self.validation_skipped = 0
        self.execution_time = 0.0  # seconds
        self.error_message = ""

    def to_dict(self):
        return {
            "district": self.district,
            "keyword": self.keyword,
            "status": self.status,
            "businesses_found": self.businesses_found,
            "businesses_saved": self.businesses_saved,
            "duplicates": self.duplicates,
            "validation_skipped": self.validation_skipped,
            "execution_time": self.execution_time,
            "error_message": self.error_message
        }

def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f"{hours}h {remaining_minutes}m"

class MiningService:

    def __init__(self):
        self.job_id = None
        self.status = "Idle" # Idle, Running, Paused, Stopped, Completed
        self.country = "USA"
        self.current_state = ""
        self.current_districts = []
        self.current_keywords = []
        self.format = "xlsx"
        
        self.current_district = "N/A"
        self.current_keyword = "N/A"
        self.current_business = "N/A"
        self.current_worker = "Idle"
        self.current_stage = "Idle"
        
        self.start_time = 0
        self.stats = self._get_initial_stats()
        self.log_messages = []
        self.websockets = set()
        
        self._background_task = None
        self._compiler_task = None
        self.csv_paths = {} # district -> csv path
        self.xlsx_paths = {} # district -> xlsx path
        self.translate_to_english = True
        self._write_lock = asyncio.Lock()
        self.completed_keywords_count = 0
        
    def _get_initial_stats(self):
        return {
            "businesses_found": 0,
            "businesses_saved": 0,
            "duplicates_skipped": 0,
            "phone_count": 0,
            "mobile_count": 0,
            "email_count": 0,
            "website_count": 0,
            "instagram_count": 0,
            "facebook_count": 0,
            "linkedin_count": 0,
            "twitter_count": 0,
            "youtube_count": 0,
            "error_count": 0,
            "retry_count": 0,
            "elapsed_time": 0
        }

    def register_websocket(self, ws):
        self.websockets.add(ws)
        
    def unregister_websocket(self, ws):
        self.websockets.discard(ws)
        
    async def broadcast_status(self):
        """Sends status payload to all connected WebSockets."""
        total_districts = len(self.current_districts) if self.current_districts else 1
        total_keywords = len(self.current_keywords) if self.current_keywords else 1
        
        dist_idx = getattr(self, "current_district_idx", 0)
        kw_idx = getattr(self, "current_keyword_idx", 0)
        business_idx = getattr(self, "current_business_idx", 0)
        total_found = getattr(self, "current_total_found", 0)
        
        completed_steps = getattr(self, "completed_keywords_count", 0)
        total_steps = total_districts * total_keywords
        
        overall_progress = round((completed_steps / total_steps) * 100, 1) if total_steps else 0
        district_progress = round((dist_idx / total_districts) * 100, 1) if total_districts else 0
        keyword_progress = round((kw_idx / total_keywords) * 100, 1) if total_keywords else 0
        business_progress = round((business_idx / total_found) * 100, 1) if total_found else 0
        
        payload = {
            "status": self.status,
            "job_id": self.job_id,
            "current_state": self.current_state,
            "current_district": self.current_district,
            "current_keyword": self.current_keyword,
            "current_business": self.current_business,
            "current_worker": self.current_worker,
            "current_stage": self.current_stage,
            "elapsed_time": int(time.time() - self.start_time) if self.status == "Running" and self.start_time > 0 else self.stats["elapsed_time"],
            "progress": {
                "overall": overall_progress,
                "district": district_progress,
                "keyword": keyword_progress,
                "business": business_progress,
                "district_count": f"{dist_idx + 1}/{total_districts}",
                "keyword_count": f"{kw_idx + 1}/{total_keywords}",
                "business_count": f"{business_idx}/{total_found if total_found else 'N/A'}"
            },
            "stats": self.stats,
            "logs": self.log_messages[-50:] # Limit to last 50 entries
        }
        
        import json
        closed = []
        for ws in list(self.websockets):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                closed.append(ws)
        for ws in closed:
            self.websockets.discard(ws)
            
    def log(self, message: str, level: str = "INFO"):
        """Logs locally, writes to file, and broadcasts to terminal UI."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(msg)

        # Keep only the latest 200 messages in memory
        if len(self.log_messages) > 200:
            self.log_messages = self.log_messages[-200:]

        # Log to rotating log file
        if level == "ERROR":
            logger.error(message)
        elif level == "SUCCESS":
            logger.info(f"SUCCESS: {message}")
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

        # Immediately push updated logs to connected frontend clients
        try:
            loop = asyncio.get_running_loop()
            if self.websockets:
                loop.create_task(self.broadcast_status())
        except RuntimeError:
            pass
    


    async def get_active_checkpoint(self) -> dict:
        """Retrieves the latest checkpoint from SQLite."""
        query = "SELECT * FROM checkpoints ORDER BY timestamp DESC LIMIT 1"
        rows = await db.execute(query)
        if not rows:
            return {}
        row = rows[0]
        import json
        return {
            "job_id": row["job_id"],
            "district": row["district"],
            "keyword": row["keyword"],
            "business_index": row["business_index"],
            "statistics": json.loads(row["statistics"]),
            "queue_state": json.loads(row["queue_state"]),
            "timestamp": row["timestamp"]
        }

    async def start_job(self, country: str, state: str, districts: list[str], keywords: list[str], output_format: str, translate_to_english: bool = True):
        if self.status in ("Running", "Paused"):
            return False, "Job already running."
            
        self.job_id = str(uuid.uuid4())
        self.status = "Running"
        self.country = country
        self.current_state = state
        self.current_districts = districts
        self.current_keywords = keywords
        self.format = output_format
        self.translate_to_english = translate_to_english
        self.start_time = time.time()
        self.stats = self._get_initial_stats()
        self.log_messages = []
        self.csv_paths = {}
        self.xlsx_paths = {}
        self.current_stage = "Starting"
        
        # Initialize keyword execution results
        self.keyword_results = []
        for dist in self.current_districts:
            for kw in self.current_keywords:
                self.keyword_results.append(KeywordExecutionResult(dist, kw))
                
        queue_manager.reset()
        queue_manager.current_job_id = self.job_id

        
        # Insert job record
        started_iso = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO jobs (job_id, status, current_state, started_at) VALUES (?, ?, ?, ?)",
            (self.job_id, self.status, self.current_state, started_iso)
        )
        
        # Spawn runner in the background
        self._background_task = asyncio.create_task(self._job_runner())
        self._compiler_task = asyncio.create_task(self._periodic_excel_compiler())
        self.log("Mining job initiated.")
        return True, "Mining started."

    async def pause_job(self):
        if self.status != "Running":
            return False, "Job not running."
        self.status = "Paused"
        queue_manager.pause()
        await db.execute("UPDATE jobs SET status = ? WHERE job_id = ?", ("Paused", self.job_id))
        self.log("Mining job paused.")
        await self.broadcast_status()
        return True, "Mining paused."

    async def resume_job(self):
        # Case 1: Paused in memory
        if self.status == "Paused":
            self.status = "Running"
            queue_manager.resume()
            await db.execute("UPDATE jobs SET status = ? WHERE job_id = ?", ("Running", self.job_id))
            self.log("Mining job resumed.")
            await self.broadcast_status()
            return True, "Mining resumed."
            
        # Case 2: Resume from database checkpoint
        checkpoint = await self.get_active_checkpoint()
        if not checkpoint:
            return False, "No active checkpoint found to resume from."
            
        self.job_id = checkpoint["job_id"]
        self.status = "Running"
        
        q_state = checkpoint["queue_state"]
        self.current_state = q_state["selected_state"]
        self.current_districts = q_state["selected_districts"]
        self.current_keywords = q_state["selected_keywords"]
        self.stats = checkpoint["statistics"]
        self.start_time = time.time() - q_state["elapsed_time"]
        self.csv_paths = q_state.get("csv_paths", {})
        self.xlsx_paths = q_state.get("xlsx_paths", {})
        self.translate_to_english = q_state.get("translate_to_english", True)
        self.country = q_state.get("country", "USA")
        
        # Restore duplicate cache
        self.duplicate_detector = DuplicateDetector()
        self.duplicate_detector.seen_businesses = q_state.get("seen_businesses", [])
        maps_worker.duplicate_detector = self.duplicate_detector
        maps_worker.seen_keys = set(q_state.get("seen_keys", []))
        
        # Restore keyword execution results
        self.keyword_results = []
        saved_results = q_state.get("keyword_results", [])
        if saved_results:
            for r_dict in saved_results:
                r = KeywordExecutionResult(r_dict["district"], r_dict["keyword"])
                r.status = r_dict["status"]
                r.businesses_found = r_dict["businesses_found"]
                r.businesses_saved = r_dict["businesses_saved"]
                r.duplicates = r_dict["duplicates"]
                r.validation_skipped = r_dict["validation_skipped"]
                r.execution_time = r_dict["execution_time"]
                r.error_message = r_dict["error_message"]
                self.keyword_results.append(r)
        else:
            for dist in self.current_districts:
                for kw in self.current_keywords:
                    self.keyword_results.append(KeywordExecutionResult(dist, kw))

        
        queue_manager.reset()
        queue_manager.current_job_id = self.job_id
        
        # Update jobs database status
        await db.execute("UPDATE jobs SET status = ? WHERE job_id = ?", ("Running", self.job_id))
        
        # Run in background with checkpoint loaded
        self._background_task = asyncio.create_task(self._job_runner(resume_checkpoint=checkpoint))
        self._compiler_task = asyncio.create_task(self._periodic_excel_compiler())
        self.log(f"Mining resumed from checkpoint. Continuing from keyword '{checkpoint['keyword']}' in district '{checkpoint['district']}'...")
        return True, "Mining resumed from checkpoint."

    async def stop_job(self):
        if self.status not in ("Running", "Paused"):
            return False, "No active job to stop."
        
        self.status = "Stopping"
        self.current_stage = "Stopping"
        queue_manager.stop()
        await db.execute("UPDATE jobs SET status = ? WHERE job_id = ?", ("Stopping", self.job_id))
        self.log("Stopping mining gracefully. Waiting for active workers to finish their current business...", "WARNING")
        await self.broadcast_status()
        
        # Await background runner task to finish gracefully
        if self._background_task:
            try:
                await self._background_task
            except Exception as e:
                logger.error(f"Error waiting for background task: {e}")
                
        self.status = "Stopped"
        self.current_stage = "Stopped"
        await db.execute("UPDATE jobs SET status = ?, finished_at = ? WHERE job_id = ?", ("Stopped", datetime.now().isoformat(), self.job_id))
        self.log("Mining job stopped gracefully. Mined data has been saved.", "SUCCESS")
        await self.broadcast_status()
        return True, "Mining stopped."

    async def broadcast_event(self, event_type: str, data: any):
        """Broadcasts specific server events to all connected WebSockets."""
        import json
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        closed = []
        for ws in list(self.websockets):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                closed.append(ws)
        for ws in closed:
            self.websockets.discard(ws)

    async def _job_runner(self, resume_checkpoint=None):
        """Asynchronous execution loop covering district and keyword processing."""
        settings = await settings_service.get_settings()
        
        # Initialize duplicate detector
        self.duplicate_detector = DuplicateDetector()
        maps_worker.duplicate_detector = self.duplicate_detector
        
        start_dist_idx = 0
        start_kw_idx = 0
        start_business_idx = 0
        
        if resume_checkpoint:
            q_state = resume_checkpoint["queue_state"]
            start_dist_idx = q_state.get("current_district_idx", 0)
            start_kw_idx = q_state.get("current_keyword_idx", 0)
            start_business_idx = q_state.get("current_business_idx", 0)
            self.duplicate_detector.seen_businesses = q_state.get("seen_businesses", [])
            
        self.current_district_idx = start_dist_idx
        self.current_keyword_idx = start_kw_idx
        self.current_business_idx = start_business_idx
        self.current_total_found = 0
        self.completed_keywords_count = (start_dist_idx * len(self.current_keywords)) + start_kw_idx
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                # 1. District processing loop
                for dist_idx in range(start_dist_idx, len(self.current_districts)):
                    if queue_manager.is_stopped:
                        break
                    self.current_district_idx = dist_idx
                    dist = self.current_districts[dist_idx]
                    self.current_district = dist
                    self.log(f"Processing District: {dist}", "INFO")
                    
                    dist_key = dist
                    if dist_key not in self.csv_paths:
                        c_path, x_path = excel_worker.init_filepaths(dist, f"{len(self.current_keywords)}_keywords", settings.output_directory)
                        self.csv_paths[dist_key] = c_path
                        self.xlsx_paths[dist_key] = x_path
                        
                    csv_path = self.csv_paths[dist_key]
                    
                    # 2. Keywords inside district (processed sequentially)
                    kw_range_start = start_kw_idx if dist_idx == start_dist_idx else 0
                    
                    for kw_i in range(kw_range_start, len(self.current_keywords)):
                        if queue_manager.is_stopped:
                            break
                        await queue_manager.wait_if_paused()
                        
                        kw_val = self.current_keywords[kw_i]
                        self.current_keyword = kw_val
                        self.current_keyword_idx = kw_i
                        
                        kw_result = KeywordExecutionResult(dist, kw_val)
                        kw_start_time = time.time()
                        
                        # Log starting keyword
                        start_time_str = datetime.now().strftime("%H:%M:%S")
                        logger.info(
                            f"\n"
                            f"========================================\n"
                            f"STARTING KEYWORD\n"
                            f"========================================\n\n"
                            f"District:\n{dist}\n\n"
                            f"Keyword:\n{kw_val}\n\n"
                            f"Start Time:\n{start_time_str}\n\n"
                            f"========================================\n"
                        )
                        self.log(f"STARTED Keyword: {kw_val} in {dist}", "INFO")
                        
                        # Callbacks
                        def handle_stat(stat_type):
                            if stat_type == "found":
                                self.stats["businesses_found"] += 1
                                kw_result.businesses_found += 1
                            elif stat_type == "duplicate":
                                self.stats["duplicates_skipped"] += 1
                                kw_result.duplicates += 1
                            elif stat_type == "error":
                                self.stats["error_count"] += 1
                                
                        def update_stage_callback(stage, name):
                            self.current_stage = stage
                            if name:
                                self.current_business = name
                            asyncio.create_task(self.broadcast_status())
                            
                        business_offset = start_business_idx if (dist_idx == start_dist_idx and kw_i == start_kw_idx) else 0
                        self.current_business_idx = business_offset
                        
                        business_tasks = []
                        
                        # Sub-task to process a single business concurrently (website scrape, translate, write)
                        async def process_business_task(business_data):
                            if queue_manager.is_stopped:
                                return
                            await queue_manager.wait_if_paused()
                            
                            extra_fields = {
                                "Email": "N/A", "Secondary Email": "N/A", "Instagram": "N/A",
                                "Facebook": "N/A", "LinkedIn": "N/A", "Twitter": "N/A", "YouTube": "N/A"
                            }
                            
                            # Website Crawling
                            if settings.enable_scraping and business_data["website"] != "N/A":
                                extra_fields = await website_worker.scrape_website(business_data["website"])
                                
                                # Increment website metrics
                                if extra_fields["Email"] != "N/A":
                                    self.stats["email_count"] += 1
                                if extra_fields["Facebook"] != "N/A":
                                    self.stats["facebook_count"] += 1
                                if extra_fields["Instagram"] != "N/A":
                                    self.stats["instagram_count"] += 1
                                    
                                if extra_fields.get("Email") and extra_fields["Email"] != "N/A":
                                    if hasattr(self, "duplicate_detector") and self.duplicate_detector is not None:
                                        await self.duplicate_detector.update_email(
                                            business_data["name"],
                                            business_data["address"],
                                            business_data["place_id"],
                                            extra_fields["Email"],
                                            row_index=business_data.get("row_index"),
                                            phone=business_data.get("phone"),
                                            mobile=business_data.get("mobile"),
                                            website=business_data.get("website")
                                        )
                                        
                            if business_data["website"] != "N/A":
                                self.stats["website_count"] += 1
                                
                            # Final Record Validation Check: strict mandatory field validation (Name, Address, Phone/Mobile)
                            is_rec_valid, reason_msg = validate_business_record(
                                business_data["name"],
                                business_data["address"],
                                business_data["phone"],
                                business_data["mobile"]
                            )
                            if not is_rec_valid:
                                logger.info(reason_msg)
                                kw_result.validation_skipped += 1
                                return
                                
                            # Classification
                            industry, tag = await classification_worker.classify(
                                business_data["category"], business_data["name"], kw_val, settings.enable_ai
                            )
                            
                            # Translation
                            name_en = business_data["name"]
                            street_en = business_data["street"]
                            city_en = business_data["city"]
                            state_en = business_data["state"]
                            industry_en = industry
                            tag_en = tag
                            
                            if getattr(self, "translate_to_english", True):
                                name_en = await translate_to_english_async(name_en)
                                street_en = await translate_to_english_async(street_en)
                                city_en = await translate_to_english_async(city_en)
                                state_en = await translate_to_english_async(state_en)
                            
                            # Excel row fields
                            row = [
                                name_en,
                                "N/A", # Salutation
                                "N/A", # First Name
                                ".",   # Last Name
                                "N/A", # Title
                                extra_fields["Email"],
                                extra_fields["Secondary Email"],
                                business_data["phone"],
                                business_data["mobile"],
                                "N/A", # Fax
                                "N/A", # Skype
                                business_data["website"],
                                extra_fields["Instagram"],
                                extra_fields["Facebook"],
                                extra_fields["LinkedIn"],
                                extra_fields["Twitter"],
                                extra_fields["YouTube"],
                                street_en,
                                city_en,
                                self.current_state,
                                business_data["zip_code"],
                                self.country,
                                industry_en
                            ]
                            
                            # Thread-safe write to CSV
                            async with self._write_lock:
                                excel_worker.write_batch(csv_path, [row])
                                
                            self.stats["businesses_saved"] += 1
                            kw_result.businesses_saved += 1
                            self.current_business_idx += 1
                            
                            # Broadcast live lead record saved
                            lead_record = {
                                "name": name_en,
                                "phone": business_data["phone"] if business_data["phone"] != "N/A" else business_data["mobile"],
                                "email": extra_fields["Email"],
                                "website": business_data["website"],
                                "street": street_en,
                                "city": city_en,
                                "state": self.current_state,
                                "country": self.country,
                                "industry": industry_en,
                                "tags": tag_en,
                                "status": "Saved"
                            }
                            await self.broadcast_event("business_saved", lead_record)
                            
                            if business_data["phone"] != "N/A":
                                self.stats["phone_count"] += 1
                            if business_data["mobile"] != "N/A":
                                self.stats["mobile_count"] += 1
                                
                            # Checkpoint save
                            elapsed_run = int(time.time() - self.start_time)
                            if elapsed_run > 0 and elapsed_run % settings.checkpoint_interval == 0:
                                q_state = {
                                    "country": self.country,
                                    "selected_state": self.current_state,
                                    "selected_districts": self.current_districts,
                                    "selected_keywords": self.current_keywords,
                                    "current_district_idx": dist_idx,
                                    "current_keyword_idx": kw_i,
                                    "current_business_idx": self.current_business_idx,
                                    "elapsed_time": elapsed_run,
                                    "csv_paths": self.csv_paths,
                                    "xlsx_paths": self.xlsx_paths,
                                    "seen_keys": list(maps_worker.seen_keys),
                                    "seen_businesses": self.duplicate_detector.seen_businesses if hasattr(self, "duplicate_detector") and self.duplicate_detector is not None else [],
                                    "translate_to_english": getattr(self, "translate_to_english", True),
                                    "keyword_results": [r.to_dict() for r in self.keyword_results]
                                }
                                await checkpoint_manager.create_checkpoint(self.job_id, dist, kw_val, self.current_business_idx, self.stats, q_state)
                                
                            await self.broadcast_status()
                            
                        # Run keyword search
                        self.log(f"RUNNING Keyword: {kw_val} in {dist}", "INFO")
                        try:
                            async for business in maps_worker.run(
                                browser, self.current_state, dist, kw_val, settings, handle_stat, lambda m: self.log(m, "INFO"), 
                                self.country, business_offset=business_offset, stage_callback=update_stage_callback
                            ):
                                if queue_manager.is_stopped:
                                    break
                                    
                                task = asyncio.create_task(process_business_task(business))
                                business_tasks.append(task)
                                
                            if business_tasks:
                                await asyncio.gather(*business_tasks, return_exceptions=True)
                                
                            kw_result.execution_time = time.time() - kw_start_time
                            exec_time_str = format_duration(kw_result.execution_time)
                            
                            if kw_result.businesses_found == 0:
                                kw_result.status = "Zero Results"
                                logger.info(
                                    f"\n"
                                    f"========================================\n\n"
                                    f"NO RESULTS\n\n"
                                    f"Keyword:\n{kw_val}\n\n"
                                    f"District:\n{dist}\n\n"
                                    f"Businesses Found:\n0\n\n"
                                    f"========================================\n"
                                )
                                self.log(f"ZERO RESULTS Keyword: {kw_val} in {dist}", "WARNING")
                            else:
                                kw_result.status = "Completed"
                                logger.info(
                                    f"\n"
                                    f"========================================\n"
                                    f"COMPLETED KEYWORD\n"
                                    f"========================================\n\n"
                                    f"District:\n{dist}\n\n"
                                    f"Keyword:\n{kw_val}\n\n"
                                    f"Businesses Found:\n{kw_result.businesses_found}\n\n"
                                    f"Businesses Saved:\n{kw_result.businesses_saved}\n\n"
                                    f"Duplicates:\n{kw_result.duplicates}\n\n"
                                    f"Validation Skipped:\n{kw_result.validation_skipped}\n\n"
                                    f"Execution Time:\n{exec_time_str}\n\n"
                                    f"========================================\n"
                                )
                                self.log(f"COMPLETED Keyword: {kw_val} in {dist}", "SUCCESS")
                                
                        except Exception as ex:
                            import traceback
                            stack_trace = traceback.format_exc()
                            kw_result.status = "Failed"
                            kw_result.execution_time = time.time() - kw_start_time
                            kw_result.error_message = f"{type(ex).__name__}: {str(ex)}"
                            
                            logger.error(
                                f"\n"
                                f"========================================\n"
                                f"FAILED KEYWORD\n"
                                f"========================================\n\n"
                                f"Keyword:\n{kw_val}\n\n"
                                f"District:\n{dist}\n\n"
                                f"Exception:\n{type(ex).__name__}: {str(ex)}\n\n"
                                f"Stack Trace:\n{stack_trace}"
                                f"========================================\n"
                            )
                            self.log(f"FAILED Keyword: {kw_val} in {dist}. Exception: {ex}", "ERROR")
                        finally:
                            # Always record results
                            for r in self.keyword_results:
                                if r.district == dist and r.keyword == kw_val:
                                    r.status = kw_result.status
                                    r.businesses_found = kw_result.businesses_found
                                    r.businesses_saved = kw_result.businesses_saved
                                    r.duplicates = kw_result.duplicates
                                    r.validation_skipped = kw_result.validation_skipped
                                    r.execution_time = kw_result.execution_time
                                    r.error_message = kw_result.error_message
                                    break
                            self.completed_keywords_count += 1
                            start_business_idx = 0 # Reset for next keyword
                            await self.broadcast_status()
                            
                        # If stopped, save final stopped checkpoint and exit
                        if queue_manager.is_stopped:
                            q_state = {
                                "country": self.country,
                                "selected_state": self.current_state,
                                "selected_districts": self.current_districts,
                                "selected_keywords": self.current_keywords,
                                "current_district_idx": dist_idx,
                                "current_keyword_idx": kw_i,
                                "current_business_idx": self.current_business_idx,
                                "elapsed_time": int(time.time() - self.start_time),
                                "csv_paths": self.csv_paths,
                                "xlsx_paths": self.xlsx_paths,
                                "seen_keys": list(maps_worker.seen_keys),
                                "seen_businesses": self.duplicate_detector.seen_businesses if hasattr(self, "duplicate_detector") and self.duplicate_detector is not None else [],
                                "translate_to_english": getattr(self, "translate_to_english", True),
                                "keyword_results": [r.to_dict() for r in self.keyword_results]
                            }
                            await checkpoint_manager.create_checkpoint(
                                self.job_id, dist, kw_val, self.current_business_idx, self.stats, q_state
                            )
                            break
                    
                    if queue_manager.is_stopped:
                        break

                    
                # Loop ended
                if queue_manager.is_stopped:
                    self.status = "Stopped"
                    self.current_stage = "Stopped"
                    await db.execute("UPDATE jobs SET status = ?, finished_at = ? WHERE job_id = ?", ("Stopped", datetime.now().isoformat(), self.job_id))
                    self.log("Mining job stopped gracefully by user.", "WARNING")
                else:
                    self.status = "Completed"
                    self.current_stage = "Completed"
                    await db.execute("UPDATE jobs SET status = ?, finished_at = ? WHERE job_id = ?", ("Completed", datetime.now().isoformat(), self.job_id))
                    self.log("Mining job completed successfully.", "SUCCESS")
                
            except asyncio.CancelledError:
                self.status = "Stopped"
                self.current_stage = "Stopped"
                await db.execute("UPDATE jobs SET status = ?, finished_at = ? WHERE job_id = ?", ("Stopped", datetime.now().isoformat(), self.job_id))
                self.log("Mining job cancelled/stopped.", "WARNING")
            except Exception as e:
                self.status = "Failed"
                self.current_stage = "Completed"
                await db.execute("UPDATE jobs SET status = ?, finished_at = ? WHERE job_id = ?", ("Failed", datetime.now().isoformat(), self.job_id))
                self.log(f"Mining job failed: {e}", "ERROR")
            finally:
                if hasattr(self, "_compiler_task") and self._compiler_task:
                    self._compiler_task.cancel()
                await browser.close()
                await self._compile_active_files()
                
                # Generate reports and export Excel
                out_dir = settings.output_directory if (hasattr(settings, "output_directory") and settings.output_directory) else "Output/Mining"
                self._generate_and_export_reports(out_dir)
                
                if self.status != "Stopped":
                    await checkpoint_manager.delete_checkpoint(self.job_id)

                
                # Generate and save duplicate audit report
                if hasattr(self, "duplicate_detector") and self.duplicate_detector is not None:
                    report = self.duplicate_detector.generate_duplicate_report()
                    self.log(report, "SUCCESS")
                    logger.info(report)
                    try:
                        out_dir = settings.output_directory if (hasattr(settings, "output_directory") and settings.output_directory) else "Output/Mining"
                        os.makedirs(out_dir, exist_ok=True)
                        report_path = os.path.join(out_dir, f"duplicate_report_{self.job_id}.txt")
                        with open(report_path, "w", encoding="utf-8") as f:
                            f.write(report)
                        self.log(f"Duplicate audit report saved to: {report_path}", "INFO")
                    except Exception as re:
                        logger.error(f"Failed to save duplicate report to file: {re}")
                
                await self.broadcast_status()

    def _generate_and_export_reports(self, out_dir):
        # 1. Print KEYWORD EXECUTION REPORT to log/console
        total_keywords = len(self.keyword_results)
        completed_list = [r for r in self.keyword_results if r.status == "Completed"]
        failed_list = [r for r in self.keyword_results if r.status == "Failed"]
        zero_list = [r for r in self.keyword_results if r.status == "Zero Results"]
        skipped_list = [r for r in self.keyword_results if r.status == "Skipped"]
        
        report_str = (
            f"\n"
            f"========================================\n"
            f"KEYWORD EXECUTION REPORT\n"
            f"========================================\n\n"
            f"Selected Keywords: {total_keywords}\n\n"
            f"Completed: {len(completed_list)}\n\n"
            f"Failed: {len(failed_list)}\n\n"
            f"Zero Results: {len(zero_list)}\n\n"
            f"Skipped: {len(skipped_list)}\n\n"
            f"========================================\n\n"
        )
        
        report_str += "Completed Keywords\n"
        for r in completed_list:
            report_str += f"{r.keyword} ({r.district})\n"
        report_str += "\n"
        
        report_str += "Failed Keywords\n"
        for r in failed_list:
            report_str += f"{r.keyword} ({r.district}) - {r.error_message}\n"
        report_str += "\n"
        
        report_str += "Zero Result Keywords\n"
        for r in zero_list:
            report_str += f"{r.keyword} ({r.district})\n"
        report_str += "\n"
        
        report_str += "Skipped Keywords\n"
        for r in skipped_list:
            report_str += f"{r.keyword} ({r.district})\n"
        report_str += "\n========================================\n"
        
        logger.info(report_str)
        self.log(report_str, "SUCCESS")
        
        # 2. Print MINING FINISHED SUMMARY (Requirement 13)
        total_time = time.time() - self.start_time
        summary_str = (
            f"\n"
            f"========================================\n\n"
            f"Mining Finished\n\n"
            f"Districts Selected:\n{len(self.current_districts)}\n\n"
            f"Keywords Selected:\n{len(self.current_keywords)}\n\n"
            f"Expected Executions:\n{total_keywords}\n\n"
            f"Completed:\n{len(completed_list)}\n\n"
            f"Failed:\n{len(failed_list)}\n\n"
            f"Zero Results:\n{len(zero_list)}\n\n"
            f"Skipped:\n{len(skipped_list)}\n\n"
            f"Businesses Found:\n{self.stats.get('businesses_found', 0)}\n\n"
            f"Businesses Saved:\n{self.stats.get('businesses_saved', 0)}\n\n"
            f"Duplicates:\n{self.stats.get('duplicates_skipped', 0)}\n\n"
            f"Validation Skipped:\n{sum(r.validation_skipped for r in self.keyword_results)}\n\n"
            f"Execution Time:\n{format_duration(total_time)}\n\n"
            f"========================================\n"
        )
        logger.info(summary_str)
        self.log(summary_str, "SUCCESS")
        
        # 3. Export Excel report keyword_execution_report.xlsx
        try:
            data = []
            for r in self.keyword_results:
                data.append({
                    "District": r.district,
                    "Keyword": r.keyword,
                    "Status": r.status,
                    "Businesses Found": r.businesses_found,
                    "Businesses Saved": r.businesses_saved,
                    "Duplicates": r.duplicates,
                    "Validation Skipped": r.validation_skipped,
                    "Execution Time": format_duration(r.execution_time),
                    "Error Message": r.error_message
                })
            df = pd.DataFrame(data)
            os.makedirs(out_dir, exist_ok=True)
            report_path = os.path.join(out_dir, "keyword_execution_report.xlsx")
            df.to_excel(report_path, index=False)
            logger.info(f"Keyword execution report exported to: {report_path}")
            self.log(f"Exported keyword execution report to {report_path}", "SUCCESS")
        except Exception as ex:
            logger.error(f"Failed to export keyword execution report Excel: {ex}")
            
        # 4. Validation check (Requirement 8)
        total_actual = len(completed_list) + len(failed_list) + len(zero_list) + len(skipped_list)
        if total_actual != total_keywords:
            err_msg = (
                f"\n"
                f"========================================\n"
                f"ERROR\n"
                f"Keyword execution mismatch.\n"
                f"One or more keywords were never processed.\n"
                f"========================================\n"
            )
            logger.error(err_msg)
            self.log(err_msg, "ERROR")

    async def _compile_active_files(self):
        """Compiles generated CSV files to Excel sheets, registering inside file history."""

        generated_files = []
        for dist, csv_p in self.csv_paths.items():
            xlsx_p = self.xlsx_paths.get(dist)
            if xlsx_p and os.path.exists(csv_p):
                # Compile CSV -> Excel
                excel_worker.compile_csv_to_excel(csv_p, xlsx_p)
                
                # Count rows
                import pandas as pd
                try:
                    df = pd.read_csv(csv_p)
                    row_count = len(df)
                except Exception:
                    row_count = 0
                    
                # Register in Recent Files
                file_id = await history_service.register_file(
                    filename=os.path.basename(xlsx_p),
                    category="Mining Files",
                    district=dist,
                    keyword_count=len(self.current_keywords),
                    row_count=row_count,
                    filepath=xlsx_p
                )
                generated_files.append(xlsx_p)
                
        # Handle multiple districts -> generate ZIP automatically
        if len(generated_files) > 1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"Mining_Leads_{timestamp}.zip"
            zip_path = os.path.join("Output/Mining", zip_filename)
            excel_worker.create_zip_archive(generated_files, zip_path)
            
            # Register ZIP file in History
            await history_service.register_file(
                filename=zip_filename,
                category="Mining Files",
                district="Multiple Districts",
                keyword_count=len(self.current_keywords),
                row_count=sum(self.stats["businesses_saved"] for d in self.current_districts), # Total leads across all
                filepath=zip_path
            )
            
        # Clean cache values from memory
        self.csv_paths = {}
        self.xlsx_paths = {}

    async def _periodic_excel_compiler(self):
        """Periodically compiles CSV files to Excel sheets every 3 seconds to prevent data loss."""
        while self.status in ("Running", "Stopping", "Paused"):
            await asyncio.sleep(3.0)
            async with self._write_lock:
                for dist, csv_p in list(self.csv_paths.items()):
                    xlsx_p = self.xlsx_paths.get(dist)
                    if xlsx_p and os.path.exists(csv_p):
                        try:
                            excel_worker.compile_csv_to_excel(csv_p, xlsx_p)
                        except Exception as e:
                            logger.error(f"Error periodically compiling Excel for {dist}: {e}")

mining_service = MiningService()
