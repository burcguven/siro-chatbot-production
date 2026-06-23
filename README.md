# SIRO HR Chatbot Production

This repository contains the production-ready version of the SIRO HR Chatbot project.

It includes:

* Frontend application
* Backend API and RAG pipeline
* Docker Compose deployment configuration
* MySQL initialization schema
* Required local data/vector database files for production startup

## Project Structure

```text
siro-chatbot-production/
│
├── siro_chatbot_FE/              # Frontend application
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json
│   └── src/
│
├── siro_hr_chatbot/              # Backend application
│   ├── Dockerfile
│   ├── .env.example
│   ├── requirements.txt
│   ├── app.py
│   ├── rag/
│   ├── authentication/
│   ├── faiss_index_3b/
│   ├── chroma_db/
│   └── uploaded_documents/
│
└── siro-hr-chatbot-deployment/   # Docker Compose deployment
    ├── docker-compose.yml
    ├── .env.example
    ├── mysql/
    │   └── init.sql
    └── docs/
```

## Requirements

Before running the project, make sure the following are installed:

* Docker Desktop
* Git

For Windows users, Docker Desktop should be running with the WSL 2 backend enabled.

## Environment Files

Real `.env` files are not included in the repository for security reasons.

Each `.env.example` file should be copied and renamed as `.env`.

There are three environment files required:

```text
siro_hr_chatbot/.env
siro_chatbot_FE/.env
siro-hr-chatbot-deployment/.env
```

### 1. Backend `.env`

Create this file:

```text
siro_hr_chatbot/.env
```

Use `siro_hr_chatbot/.env.example` as a template.

Important Docker database values:

```env
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_root_password
DB_NAME=chatbot_db
```

For Docker Compose, `DB_HOST` must be `mysql`, not `localhost`.

### 2. Frontend `.env`

Create this file:

```text
siro_chatbot_FE/.env
```

Use `siro_chatbot_FE/.env.example` as a template.

For local Docker deployment:

```env
VITE_CHATBOT_BACKEND_API=http://localhost:8000
```

For production deployment, replace this with the backend server/domain address.

### 3. Deployment `.env`

Create this file:

```text
siro-hr-chatbot-deployment/.env
```

Use `siro-hr-chatbot-deployment/.env.example` as a template.

Example:

```env
VITE_CHATBOT_BACKEND_API=http://localhost:8000

MYSQL_ROOT_PASSWORD=your_mysql_root_password
MYSQL_DATABASE=chatbot_db
```

`MYSQL_ROOT_PASSWORD` must match the backend `DB_PASSWORD`.

## Running the Project with Docker

Open a terminal in the deployment folder:

```bash
cd siro-hr-chatbot-deployment
```

Then run:

```bash
docker compose up --build
```

This command will:

1. Start the MySQL container
2. Initialize the database using `mysql/init.sql`
3. Build and start the backend container
4. Build and start the frontend container
5. Create a Hugging Face cache volume for model files

The first run may take a long time because backend ML models may need to be downloaded and loaded.

After the first successful run, Hugging Face model files are cached in a Docker volume:

```text
huggingface_cache
```

This helps prevent downloading the same models again on future runs.

## Accessing the Application

After all containers start successfully, open:

Frontend:

```text
http://localhost:3000
```

Backend API documentation:

```text
http://localhost:8000/docs
```

MySQL is exposed on the host machine at:

```text
localhost:3307
```

Inside Docker Compose, the backend connects to MySQL using:

```text
mysql:3306
```

## Checking Container Status

To see running containers:

```bash
docker ps
```

Expected containers:

```text
siro-hr-mysql
siro-hr-backend
siro-chatbot-frontend
```

To view logs:

```bash
docker compose logs -f
```

Backend logs only:

```bash
docker logs -f siro-hr-backend
```

Frontend logs only:

```bash
docker logs -f siro-chatbot-frontend
```

MySQL logs only:

```bash
docker logs -f siro-hr-mysql
```

## Stopping the Project

To stop the running containers:

```bash
docker compose down
```

This stops the containers but keeps the MySQL database volume.

Do not use this command unless you intentionally want to delete the database volume:

```bash
docker compose down -v
```

`-v` removes Docker volumes, including the MySQL database data.

## Running Again Later

If the code has not changed, run:

```bash
docker compose up
```

If the code, Dockerfile, requirements, package files, or environment build arguments changed, run:

```bash
docker compose up --build
```

## Resetting the Database

The `mysql/init.sql` file runs only when the MySQL volume is created for the first time.

If you need to recreate the database from `init.sql`, run:

```bash
docker compose down -v
docker compose up --build
```

Warning: this deletes the existing MySQL database volume and all stored database data.

## Notes for Production Deployment

Before deploying on a real server:

* Replace all placeholder values in `.env` files.
* Do not commit real `.env` files.
* Use strong production passwords and secret keys.
* Replace `localhost` URLs with the server IP address or production domain.
* Make sure the frontend API URL points to the correct backend address.
* If HTTPS/domain routing is used, update CORS and callback URLs accordingly.
* Keep `.env.example` files in the repository as templates.
* Keep real credentials outside GitHub.

## Important Security Note

This repository should not contain real secrets such as:

* Database passwords
* API keys
* SAP credentials
* JWT secret keys
* Production admin passwords
* Private company data that should not be public

Use `.env.example` files for templates and provide real `.env` files privately during deployment.

## Main Technologies

* FastAPI
* Python
* LangChain
* FAISS
* ChromaDB
* Hugging Face Transformers
* MySQL
* React / Vite
* Nginx
* Docker
* Docker Compose

## Quick Start Summary

```bash
cd siro-hr-chatbot-deployment
docker compose up --build
```

Then open:

```text
http://localhost:3000
http://localhost:8000/docs
```
