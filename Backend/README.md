# Glimpse Python Backend with FastAPI

## Authors and Developers

| Role       | Name     |
|------------|----------|
| Supervisor | VuongNL3 |
| Team Lead  | TuongHH  |
| Member     | DuongTQ  |
| Member     | HuyPQ    |

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
        - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
        - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
        - 🔍 [Qdrant](https://qdrant.tech) for vector search.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
<!-- - 🌐 [NGINX](https://www.nginx.com) as a web server and reverse proxy. -->
- 🚢 Deployment instructions using Docker Compose
<!-- - 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates. -->
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.
