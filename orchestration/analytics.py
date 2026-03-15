"""Analytics and reporting"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger("orchestration.analytics")


@dataclass
class PhaseMetrics:
    """Phase metrics"""
    name: str
    duration: float
    files: int
    errors: int
    retries: int


@dataclass
class ProviderMetrics:
    """Provider metrics"""
    name: str
    calls: int
    tokens: int
    errors: int
    avg_latency: float
    total_cost: float


class AnalyticsEngine:
    """Analytics and reporting engine"""
    
    def __init__(self, output_dir: str = "./Surypus2"):
        self.output_dir = Path(output_dir)
        self.metrics_file = self.output_dir / "metrics.json"
        self.history_file = self.output_dir / "analytics_history.json"
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current pipeline metrics"""
        if self.metrics_file.exists():
            return json.loads(self.metrics_file.read_text())
        return {}
    
    def get_historical_metrics(self) -> List[Dict[str, Any]]:
        """Get historical metrics"""
        if self.history_file.exists():
            return json.loads(self.history_file.read_text())
        return []
    
    def save_run(self):
        """Save current run to history"""
        current = self.get_current_metrics()
        if not current:
            return
        
        history = self.get_historical_metrics()
        current["timestamp"] = datetime.now().isoformat()
        history.append(current)
        
        # Keep last 100 runs
        history = history[-100:]
        
        self.history_file.write_text(json.dumps(history, indent=2))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate analytics report"""
        history = self.get_historical_metrics()
        
        if not history:
            return {"error": "No historical data"}
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_runs": len(history),
            "summary": self._calculate_summary(history),
            "trends": self._calculate_trends(history),
            "providers": self._analyze_providers(history),
            "phases": self._analyze_phases(history),
            "recommendations": self._generate_recommendations(history),
        }
        
        return report
    
    def _calculate_summary(self, history: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        runtimes = [r.get("runtime_seconds", 0) for r in history]
        
        return {
            "avg_runtime": statistics.mean(runtimes) if runtimes else 0,
            "min_runtime": min(runtimes) if runtimes else 0,
            "max_runtime": max(runtimes) if runtimes else 0,
            "total_runs": len(history),
            "successful_runs": sum(1 for r in history if r.get("errors", 0) == 0),
        }
    
    def _calculate_trends(self, history: List[Dict]) -> Dict[str, Any]:
        """Calculate trends over time"""
        if len(history) < 2:
            return {"trend": "insufficient_data"}
        
        # Runtime trend
        runtimes = [r.get("runtime_seconds", 0) for r in history]
        
        # Simple trend detection
        recent = statistics.mean(runtimes[-5:]) if len(runtimes) >= 5 else runtimes[-1]
        older = statistics.mean(runtimes[:5]) if len(runtimes) >= 5 else runtimes[0]
        
        if recent < older * 0.9:
            trend = "improving"
        elif recent > older * 1.1:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "runtime_trend": trend,
            "recent_avg": recent,
            "older_avg": older,
        }
    
    def _analyze_providers(self, history: List[Dict]) -> Dict[str, Any]:
        """Analyze provider performance"""
        provider_stats = {}
        
        for run in history:
            ai = run.get("ai", {}).get("by_provider", {})
            for provider, data in ai.items():
                if provider not in provider_stats:
                    provider_stats[provider] = {"calls": 0, "tokens": 0, "errors": 0}
                
                provider_stats[provider]["calls"] += data.get("calls", 0)
                provider_stats[provider]["tokens"] += data.get("tokens", 0)
                provider_stats[provider]["errors"] += data.get("errors", 0)
        
        return provider_stats
    
    def _analyze_phases(self, history: List[Dict]) -> Dict[str, Any]:
        """Analyze phase performance"""
        phase_stats = {}
        
        for run in history:
            phases = run.get("phases", {})
            for phase, duration in phases.items():
                if phase not in phase_stats:
                    phase_stats[phase] = []
                phase_stats[phase].append(duration)
        
        return {
            phase: {
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "runs": len(durations),
            }
            for phase, durations in phase_stats.items()
        }
    
    def _generate_recommendations(self, history: List[Dict]) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if not history:
            return ["Run pipeline to generate recommendations"]
        
        # Check for errors
        total_errors = sum(r.get("errors", 0) for r in history)
        if total_errors > 10:
            recommendations.append("High error rate detected - consider adding more validation")
        
        # Check runtime
        recent_runtimes = [r.get("runtime_seconds", 0) for r in history[-5:]]
        avg_runtime = statistics.mean(recent_runtimes) if recent_runtimes else 0
        
        if avg_runtime > 3600:  # > 1 hour
            recommendations.append("Consider enabling caching or reducing batch size")
        
        # Check cache
        cache_rates = [r.get("cache", {}).get("hit_rate", 0) for r in history]
        avg_cache = statistics.mean(cache_rates) if cache_rates else 0
        
        if avg_cache < 0.3:
            recommendations.append("Low cache hit rate - consider adjusting cache policy")
        
        # Check providers
        ai_data = history[-1].get("ai", {}) if history else {}
        if not ai_data:
            recommendations.append("No AI usage detected - enable AI for better conversions")
        
        return recommendations
    
    def export_csv(self, output_path: str = None) -> str:
        """Export analytics to CSV"""
        history = self.get_historical_metrics()
        
        if not history:
            return "No data to export"
        
        output_path = output_path or str(self.output_dir / "analytics.csv")
        
        lines = ["timestamp,runtime_seconds,total_files,ai_calls,ai_tokens,errors"]
        
        for run in history:
            lines.append(",".join([
                run.get("timestamp", ""),
                str(run.get("runtime_seconds", 0)),
                str(sum([
                    len(list(self.output_dir.glob("src/*.hs"))),
                    len(list(self.output_dir.glob("qml/*.qml"))),
                    len(list(self.output_dir.glob("reports/**/*.jrxml"))),
                ])),
                str(run.get("ai", {}).get("total_calls", 0)),
                str(run.get("ai", {}).get("total_tokens", 0)),
                str(run.get("errors", 0)),
            ]))
        
        Path(output_path).write_text("\n".join(lines))
        return f"Exported to {output_path}"
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard"""
        report = self.generate_report()
        
        return {
            "summary": report.get("summary", {}),
            "trends": report.get("trends", {}),
            "recommendations": report.get("recommendations", []),
            "current": self.get_current_metrics(),
        }


class PerformanceAnalyzer:
    """Analyze performance bottlenecks"""
    
    def __init__(self):
        self.data: List[Dict] = []
    
    def record(self, operation: str, duration: float, metadata: Dict = None):
        """Record operation timing"""
        self.data.append({
            "operation": operation,
            "duration": duration,
            "timestamp": time.time(),
            "metadata": metadata or {},
        })
    
    def get_slowest_operations(self, limit: int = 10) -> List[Dict]:
        """Get slowest operations"""
        sorted_data = sorted(self.data, key=lambda x: x["duration"], reverse=True)
        return sorted_data[:limit]
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for operation"""
        op_data = [d for d in self.data if d["operation"] == operation]
        
        if not op_data:
            return {"count": 0}
        
        durations = [d["duration"] for d in op_data]
        
        return {
            "count": len(durations),
            "total": sum(durations),
            "avg": statistics.mean(durations),
            "min": min(durations),
            "max": max(durations),
            "p50": statistics.median(durations),
            "p95": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
        }
    
    def get_bottlenecks(self) -> List[str]:
        """Identify bottlenecks"""
        bottlenecks = []
        
        for op in set(d["operation"] for d in self.data):
            stats = self.get_operation_stats(op)
            if stats.get("avg", 0) > 10:  # > 10 seconds
                bottlenecks.append(f"{op}: {stats['avg']:.1f}s avg")
        
        return bottlenecks


# Global analytics
_analytics: Optional[AnalyticsEngine] = None


def get_analytics() -> AnalyticsEngine:
    """Get analytics engine"""
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsEngine()
    return _analytics