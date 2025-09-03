import uvicorn
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='ClusterMaster Backend API Server')
    parser.add_argument('--backup-dir', type=str, help='Directory to store backup files')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    
    args = parser.parse_args()
    
    # Set environment variable for backup directory if provided
    if args.backup_dir:
        os.environ['CLUSTER_BACKUP_DIR'] = args.backup_dir
        print(f"🗂️  Backup directory set to: {args.backup_dir}")
    
    print(f"🚀 Starting ClusterMaster API server on {args.host}:{args.port}")
    if args.backup_dir:
        print(f"📁 Backups will be stored in: {args.backup_dir}")
    else:
        print(f"📁 Backups will be stored in: ./backups")
    
    uvicorn.run(
        "simple_main:app",  
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )

if __name__ == "__main__":
    main()