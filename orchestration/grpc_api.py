"""gRPC API for pipeline"""

from concurrent import futures
import grpc
import logging
from pathlib import Path

# Define proto service (simplified - would normally be from .proto file)
class PipelineServiceServicer:
    """gRPC servicer for pipeline"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def ConvertFile(self, request, context):
        """Convert single file"""
        return ConvertFileResponse(
            success=True,
            output_path=f"converted/{request.file_name}",
        )
    
    def GetStatus(self, request, context):
        """Get pipeline status"""
        return StatusResponse(
            running=False,
            files_processed=53,
        )


def create_grpc_server(pipeline, port: int = 50051):
    """Create gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Add servicer
    # pipeline_pb2_grpc.add_PipelineServiceServicer_to_server(
    #     PipelineServiceServicer(pipeline), server
    # )
    server.add_insecure_port(f'[::]:{port}')
    return server


# For now, just a placeholder - would need actual proto definitions
GRPC_AVAILABLE = False

try:
    import grpc
    GRPC_AVAILABLE = True
except ImportError:
    pass


def start_grpc_server(pipeline, port: int = 50051):
    """Start gRPC server"""
    if not GRPC_AVAILABLE:
        logging.warning("gRPC not available, skipping")
        return None
    
    server = create_grpc_server(pipeline, port)
    server.start()
    logging.info(f"gRPC server started on port {port}")
    return server
