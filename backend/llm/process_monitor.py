"""
Process Monitor - Track scraping and extraction progress in detail
Menampilkan informasi: job title, durasi, duplikasi data, status real-time
"""
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio


@dataclass
class ProcessMetric:
    """Metric untuk satu job/item yang diproses"""
    title: str
    job_title: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, error, skipped
    duration: float = 0.0  # dalam detik
    duplicates: int = 0
    duplicates_found: List[str] = None  # ID duplikat yang ditemukan
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    def __post_init__(self):
        if self.duplicates_found is None:
            self.duplicates_found = []
    
    def to_dict(self):
        data = asdict(self)
        # Format waktu yang lebih readable
        if self.start_time:
            data['start_time'] = self.start_time
        if self.end_time:
            data['end_time'] = self.end_time
        return data


class ProcessMonitor:
    """Monitor untuk proses scraping dan ekstraksi skill"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.items: Dict[str, ProcessMetric] = {}
        self.stats = {
            "total_processed": 0,
            "total_completed": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "total_duplicates": 0,
            "elapsed_time": 0,
        }
    
    def start_item(self, item_id: str, title: str, job_title: Optional[str] = None):
        """Mulai tracking item"""
        self.items[item_id] = ProcessMetric(
            title=title,
            job_title=job_title,
            status="processing",
            start_time=datetime.now().isoformat()
        )
    
    def complete_item(self, 
                     item_id: str, 
                     duplicates: int = 0, 
                     duplicates_found: List[str] = None):
        """Mark item sebagai completed"""
        if item_id in self.items:
            item = self.items[item_id]
            item.status = "completed"
            item.end_time = datetime.now().isoformat()
            item.duplicates = duplicates
            item.duplicates_found = duplicates_found or []
            
            # Update stats
            self.stats["total_completed"] += 1
            self.stats["total_processed"] += 1
            self.stats["total_duplicates"] += duplicates
            self.stats["elapsed_time"] = self._calc_elapsed()
    
    def skip_item(self, item_id: str, reason: str = "Already exists"):
        """Mark item sebagai skipped"""
        if item_id not in self.items:
            self.items[item_id] = ProcessMetric(
                title=f"Item {item_id}",
                status="skipped"
            )
        else:
            self.items[item_id].status = "skipped"
            self.items[item_id].end_time = datetime.now().isoformat()
        
        self.stats["total_skipped"] += 1
        self.stats["total_processed"] += 1
    
    def error_item(self, item_id: str, error: str):
        """Mark item dengan error"""
        if item_id not in self.items:
            self.items[item_id] = ProcessMetric(
                title=f"Item {item_id}",
                status="error",
                error=error
            )
        else:
            self.items[item_id].status = "error"
            self.items[item_id].error = error
            self.items[item_id].end_time = datetime.now().isoformat()
        
        self.stats["total_errors"] += 1
        self.stats["total_processed"] += 1
    
    def get_summary(self):
        """Get ringkasan tracking"""
        elapsed = self._calc_elapsed()
        
        return {
            "progress": {
                "total": len(self.items),
                "completed": self.stats["total_completed"],
                "skipped": self.stats["total_skipped"],
                "errors": self.stats["total_errors"],
                "percentage": round(
                    (self.stats["total_processed"] / max(len(self.items), 1)) * 100, 1
                )
            },
            "duplicates": {
                "total": self.stats["total_duplicates"],
            },
            "timing": {
                "elapsed_seconds": elapsed,
                "elapsed_formatted": self._format_duration(elapsed),
                "estimated_remaining": self._estimate_remaining(elapsed),
            },
            "recent_items": self._get_recent_items(5)
        }
    
    def get_all_metrics(self):
        """Get semua metrics"""
        return [item.to_dict() for item in self.items.values()]
    
    def _calc_elapsed(self) -> float:
        """Hitung durasi yang telah berlalu dalam detik"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def _format_duration(self, seconds: float) -> str:
        """Format durasi ke format readable"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def _estimate_remaining(self, elapsed: float) -> str:
        """Estimasi waktu tersisa"""
        if self.stats["total_processed"] == 0:
            return "calculating..."
        
        avg_time = elapsed / self.stats["total_processed"]
        remaining_items = len(self.items) - self.stats["total_processed"]
        estimated_seconds = avg_time * remaining_items
        
        return self._format_duration(estimated_seconds)
    
    def _get_recent_items(self, limit: int = 5) -> List[Dict]:
        """Get recent items yang diproses"""
        items_list = list(self.items.values())
        # Sort berdasarkan last update (end_time atau start_time yang paling baru)
        items_list.sort(key=lambda x: x.end_time or x.start_time or "", reverse=True)
        
        return [item.to_dict() for item in items_list[:limit]]
