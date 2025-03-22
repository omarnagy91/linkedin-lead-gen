# LinkedIn Lead Generation API Documentation

This document outlines the API endpoints available in the LinkedIn Lead Generation system.

## Base URL

The base URL for all API endpoints is: `https://your-azure-vm-domain.com/api`

## Authentication

All API endpoints require an API key to be included in the request headers:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Create Job

Creates a new LinkedIn lead generation job.

**URL**: `/jobs`

**Method**: `POST`

**Request Body**:

```json
{
  "user_email": "user@example.com",
  "campaign_goal": "Looking for potential customers for our new enterprise software solution",
  "company_urls": [
    "https://www.linkedin.com/company/microsoft/",
    "https://www.linkedin.com/company/google/"
  ],
  "countries": ["United States", "United Kingdom", "Germany"],
  "employment_status": "current",
  "decision_level": "C-Suite and Directors"
}
```

**Response**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Job created successfully"
}
```

### Get Job Status

Retrieves the status of a job.

**URL**: `/jobs/{job_id}`

**Method**: `GET`

**Response**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2024-03-23T12:34:56Z",
  "updated_at": "2024-03-23T12:40:23Z",
  "progress": {
    "searches_completed": 15,
    "searches_total": 25,
    "profiles_discovered": 245,
    "profiles_enriched": 112
  }
}
```

Possible status values:
- `submitted`: Job has been submitted but processing hasn't started
- `processing`: Job is currently being processed
- `awaiting_selection`: Job has completed initial processing and is waiting for title selection
- `exporting`: Selected profiles are being exported
- `completed`: Job has been completed successfully
- `failed`: Job has failed

### Get Job Titles

Retrieves grouped job titles found for a job.

**URL**: `/jobs/{job_id}/titles`

**Method**: `GET`

**Response**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "titles": [
    {
      "company": "Microsoft",
      "title": "Chief Technology Officer",
      "count": 5,
      "selected": false
    },
    {
      "company": "Microsoft",
      "title": "Vice President of Engineering",
      "count": 12,
      "selected": false
    },
    {
      "company": "Google",
      "title": "Director of Product",
      "count": 8,
      "selected": false
    }
  ]
}
```

### Select Job Titles

Selects which job titles to include in the final export.

**URL**: `/jobs/{job_id}/titles`

**Method**: `POST`

**Request Body**:

```json
{
  "titles": [
    {
      "company": "Microsoft",
      "title": "Chief Technology Officer",
      "selected": true
    },
    {
      "company": "Microsoft",
      "title": "Vice President of Engineering",
      "selected": true
    },
    {
      "company": "Google",
      "title": "Director of Product",
      "selected": false
    }
  ]
}
```

**Response**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "exporting",
  "message": "Titles selected successfully, export started"
}
```

### Check Export Status

Checks the status of the export process.

**URL**: `/jobs/{job_id}/export`

**Method**: `GET`

**Response**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "export_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
  "profiles_exported": 52,
  "completed_at": "2024-03-23T13:45:12Z"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:

```json
{
  "error": true,
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
```
