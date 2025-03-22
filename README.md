# LinkedIn Lead Generation System

A scalable backend system for discovering and enriching LinkedIn profiles using AI-generated search strategies.

## Overview

This system helps users find relevant LinkedIn profiles based on company, country, and seniority criteria. It uses GPT-4 to generate optimal search strategies, SerpAPI to execute searches, and ProxyCurl to enrich profile data.

### Key Features

- **AI-Powered Search**: Uses GPT-4 to generate optimal search queries with company context
- **Parallel Processing**: Efficiently processes searches and profile enrichment in parallel
- **Enhanced Context**: Extracts company information to improve search quality
- **User-Guided Selection**: Allows users to select relevant job titles before final export
- **Precise Filtering**: Filters profiles by experience (6-10+ years for current, 10+ years for past employees)
- **Cost Optimization**: Minimizes API usage through caching and deduplication

## Architecture

The system consists of:

1. **FastAPI Backend**: Handles API requests and orchestrates the process
2. **Background Workers**: Process searches and profile enrichment asynchronously
3. **Database**: Stores job data, search results, and enriched profiles (using Supabase)
4. **External APIs**:
   - OpenAI GPT-4 API: Generates search strategies
   - SerpAPI: Executes Google searches
   - ProxyCurl API: Retrieves company information and enriches LinkedIn profiles
   - Google Sheets API: Exports results

## System Flow

1. **Job Creation**: User submits a job with:
   - Company LinkedIn URLs
   - Target countries
   - Employment status (current, past, or all)
   - Campaign goal

2. **Company Analysis**: 
   - System extracts company information using ProxyCurl
   - Information includes industry, size, description, and specialties

3. **Intelligent Search Strategy**: 
   - GPT-4 uses company context to generate optimized search queries
   - Customized for each company-country combination

4. **Profile Discovery**: 
   - System executes searches in parallel using SerpAPI
   - Discovers LinkedIn profiles matching criteria

5. **Profile Enrichment**: 
   - Retrieves detailed profile information using ProxyCurl
   - Extracts job titles, experience, and other data

6. **Smart Filtering**:
   - Filters profiles based on:
     - Experience criteria (6-10+ years for current, 10+ years for past employees)
     - Seniority level (partner, director, manager, CXO, owner, VP)
     - For past employees: checks if they left within last 5 years

7. **Title Selection**: 
   - User selects which job titles to include in final export

8. **Export**: 
   - Selected profiles exported to Google Sheets
   - Includes comprehensive profile information

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and docker-compose
- Supabase account
- API keys for:
  - OpenAI GPT-4
  - SerpAPI
  - ProxyCurl
  - Google Sheets API (with credentials JSON file)

### Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/linkedin-lead-gen.git
   cd linkedin-lead-gen
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. Start development server
   ```bash
   uvicorn app.main:app --reload
   ```

5. Access the API documentation
   ```
   http://localhost:8000/api/docs
   ```

### Docker Setup

1. Build and start the containers
   ```bash
   docker-compose up -d
   ```

2. Check the logs
   ```bash
   docker-compose logs -f
   ```

3. Access the API
   ```
   http://localhost/api/docs
   ```

### Production Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed production deployment instructions.

## API Usage

### Authentication

All API endpoints require an API key in the headers:

```
Authorization: Bearer YOUR_API_KEY
```

### Creating a Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "user@example.com",
    "campaign_goal": "Finding CTO candidates for our new AI project",
    "company_urls": [
      "https://www.linkedin.com/company/microsoft/",
      "https://www.linkedin.com/company/google/"
    ],
    "countries": ["United States", "United Kingdom"],
    "employment_status": "current"
  }'
```

### Selecting Job Titles

```bash
curl -X POST http://localhost:8000/api/jobs/JOB_ID/titles \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "titles": [
      {
        "company": "Microsoft",
        "title": "Chief Technology Officer",
        "selected": true
      },
      {
        "company": "Google",
        "title": "VP of Engineering",
        "selected": true
      }
    ]
  }'
```

## Customization

### Modifying Filtering Criteria

The filtering criteria (experience years, seniority levels) can be modified in the `proxycurl_service.py` file.

### Adding New Features

The modular architecture makes it easy to add new features:

1. Add new service in the `services` directory
2. Add new API endpoint in the `api` directory
3. Add new worker in the `workers` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [OpenAI](https://openai.com/) for the GPT-4 API
- [SerpAPI](https://serpapi.com/) for search capabilities
- [ProxyCurl](https://nubela.co/proxycurl/) for LinkedIn data
- [Supabase](https://supabase.io/) for database services
