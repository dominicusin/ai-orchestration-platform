"""Batch operations CLI"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.processing import BatchProcessor, ParallelProcessor


async def main():
    parser = argparse.ArgumentParser(description="Batch processing CLI")
    parser.add_argument("command", choices=["run", "status", "list", "cancel"])
    parser.add_argument("--files", nargs="+", help="Files to process")
    parser.add_argument("--job-id", help="Job ID for status/cancel")
    parser.add_argument("--workers", type=int, default=4, help="Max workers")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    
    args = parser.parse_args()
    
    processor = BatchProcessor(
        max_workers=args.workers,
        batch_size=args.batch_size,
    )
    
    if args.command == "run":
        if not args.files:
            print("Error: --files required")
            return 1
        
        def sample_processor(file_path, options):
            return f"Processed: {file_path}"
        
        job_id = processor.create_job(
            name="batch_job",
            files=args.files,
            options={"sample": True},
        )
        
        print(f"Created job: {job_id}")
        
        await processor.run_job(job_id, sample_processor)
        
        job = processor.get_job(job_id)
        print(f"Status: {job.status}")
        print(f"Results: {len(job.results)}")
        print(f"Errors: {len(job.errors)}")
    
    elif args.command == "status":
        if not args.job_id:
            print("Error: --job-id required")
            return 1
        
        job = processor.get_job(args.job_id)
        
        if not job:
            print(f"Job not found: {args.job_id}")
            return 1
        
        print(f"Job: {job.id}")
        print(f"Name: {job.name}")
        print(f"Status: {job.status}")
        print(f"Progress: {job.progress}%")
        print(f"Files: {len(job.files)}")
        print(f"Results: {len(job.results)}")
        print(f"Errors: {len(job.errors)}")
    
    elif args.command == "list":
        jobs = processor.list_jobs()
        
        print(f"Total jobs: {len(jobs)}")
        
        for job in jobs:
            print(f"  {job.id}: {job.name} - {job.status}")
    
    elif args.command == "cancel":
        if not args.job_id:
            print("Error: --job-id required")
            return 1
        
        if processor.cancel_job(args.job_id):
            print(f"Cancelled: {args.job_id}")
        else:
            print(f"Failed to cancel: {args.job_id}")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))