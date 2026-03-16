# Vercel Deployment Guide

## Problem Fixed
The application was throwing `Error: [Errno 30] Read-only file system` when deployed to Vercel because the serverless environment has a read-only filesystem.

## Solution Implemented

### 1. **Temporary File Storage**
- Modified `app.py` to use `/tmp` directory for Vercel (write-able temporary storage)
- Falls back to local `./uploads` directory for local development
- Implements error handling for permission issues

### 2. **Configuration Files Added**
- **vercel.json**: Tells Vercel how to build and run the Flask application
- **.gitignore**: Excludes unnecessary files from deployment

### 3. **Code Changes**
The `app.py` now:
- Detects if running on Vercel using `VERCEL` environment variable
- Uses `/tmp/uploads` for Vercel, `./uploads` for local
- Cleans up temporary files after processing
- Handles permission errors gracefully

## How to Deploy to Vercel

### Prerequisites
1. Install Vercel CLI: `npm install -g vercel`
2. Have a GitHub account and push code to GitHub

### Method 1: Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/
2. Sign in with GitHub
3. Click "New Project"
4. Select your GitHub repository `Cloud-Data-Integrity-Verification`
5. Click "Import"
6. Click "Deploy"
7. Wait for deployment to complete

### Method 2: Via Vercel CLI
```powershell
cd "c:\Users\gujjeti dinesh\Desktop\CCV\Cloud-Data-Integrity-Project"
vercel --prod
```

## Deployment Notes

### File Size Limitations
- Vercel has a 50MB hard limit on function payload
- Recommended maximum file upload: 10MB
- For larger files, consider using cloud storage (AWS S3, Google Cloud Storage)

### No Persistent Storage
- Files uploaded to Vercel are stored only in temporary `/tmp` directory
- `/tmp` directory is cleared when function execution ends
- For persistent storage, integrate with cloud storage services

### Environment Variables
If you need to add environment variables for production:
1. Go to Vercel Dashboard
2. Project Settings → Environment Variables
3. Add your variables there

## Testing on Vercel

After deployment:
1. Open the Vercel-provided URL (e.g., `https://your-project.vercel.app`)
2. Test file upload functionality
3. Test verification and audit features

## Troubleshooting

### Issue: "Module not found" error
- **Solution**: All required modules are in `requirements.txt`. Vercel automatically installs them.

### Issue: Timeout on file processing
- **Solution**: Reduce file size. Vercel timeout is 10-60 seconds depending on plan.

### Issue: Large file uploads fail
- **Solution**: Use cloud storage service (S3) instead of uploading to serverless function.

## Future Enhancements

For production deployment, consider:
1. **AWS S3 Integration**: Store files in S3 instead of temp storage
2. **Database**: Use PostgreSQL/MongoDB for metadata persistence
3. **Caching**: Redis for improving performance
4. **Authentication**: Add user authentication and authorization

### Example S3 Integration (Optional)
```python
import boto3

BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
s3_client = boto3.client('s3')

# In upload handler:
s3_client.upload_file(temp_path, BUCKET_NAME, file_id)
```

For more details, see the main README.md file.
