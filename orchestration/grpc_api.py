"""gRPC API for DAG execution"""

import logging

logger = logging.getLogger("orchestration.grpc_api")


class GRPCService:
    """gRPC service stub"""

    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port

    def start(self):
        logger.info(f"gRPC server would start on {self.host}:{self.port}")

    def stop(self):
        logger.info("gRPC server stopped")

    def submit_task(self, task: dict) -> dict:
        """Submit task via gRPC"""
        return {"status": "submitted", "task_id": task.get("id")}

    def get_status(self, task_id: str) -> dict:
        """Get task status"""
        return {"task_id": task_id, "status": "pending"}


_grpc_service = None


def get_grpc_service() -> GRPCService:
    global _grpc_service
    if _grpc_service is None:
        _grpc_service = GRPCService()
    return _grpc_service
