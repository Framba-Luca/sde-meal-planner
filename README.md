# SDE Meal Planner

A service-oriented meal planner application that uses TheMealDB API to help users plan their meals. The system is built with microservices architecture using FastAPI, Streamlit, and PostgreSQL.

## Architecture

The system consists of 4 macro-services:

### 1. GUI (Streamlit)
- **Port:** 8501
- **Description:** Web-based user interface for interacting with all services
- **Features:**
  - User authentication (username/password and Google OAuth2)
  - Meal proposal based on ingredients
  - Meal planning for multiple days
  - Custom recipe management
  - Recipe search from TheMealDB
  - View and manage meal plans

### 2. Authentication Service
- **Port:** 8001
- **Description:** Handles user authentication with OAuth2 and JWT
- **Features:**
  - User registration and login
  - JWT token generation and validation
  - Google OAuth2 integration
  - Session management

### 3. Meal Planner Macro-Service
Divided into smaller micro-services:

#### a. Meal Proposer Service
- **Port:** 8003
- **Description:** Proposes recipes from TheMealDB based on ingredients
- **Features:**
  - Search recipes by ingredient
  - Get random recipes
  - Search by name, category, or area
  - Format recipes with ingredients and instructions

#### b. Meal Planning Service
- **Port:** 8004
- **Description:** Creates meal plans using the meal proposer service
- **Features:**
  - Generate meal plans for multiple days
  - Create breakfast, lunch, and dinner for each day
  - Store meal plans in database
  - Update and delete meal plans

#### c. Recipes Fetch Service
- **Port:** 8006
- **Description:** Fetches recipes from TheMealDB API
- **Features:**
  - Search recipes by name, ingredient, category, or area
  - Get random recipes
  - List all categories and areas
  - Lookup recipes by ID

### 4. Recipe Interaction Service
- **Port:** 8005
- **Description:** Allows users to add and manage their own recipes
- **Features:**
  - Create custom recipes
  - View, update, and delete custom recipes
  - Search custom recipes
  - Filter by category or area

### 5. Database Service
- **Port:** 8002
- **Description:** Adaptive database abstraction layer for PostgreSQL
- **Features:**
  - User management
  - Meal plan management
  - Custom recipe storage
  - Database initialization

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE meal_plans (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE meal_plan_items (
    id SERIAL PRIMARY KEY,
    meal_plan_id INT REFERENCES meal_plans(id) ON DELETE CASCADE,
    mealdb_id INT NOT NULL,
    meal_date DATE NOT NULL,
    meal_type VARCHAR(20)
);

CREATE TABLE custom_recipes (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    area VARCHAR(100),
    instructions TEXT,
    image TEXT,
    tags TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE custom_recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INT REFERENCES custom_recipes(id) ON DELETE CASCADE,
    ingredient_name VARCHAR(255) NOT NULL,
    measure VARCHAR(100)
);
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)

## Setup Instructions

### Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd sde-meal-planner
   ```

2. **Configure environment variables (optional):**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

3. **Build and start all services:**
    ```bash
    docker-compose up --build
    ```

4. **Access the application:**
    - Streamlit GUI: http://localhost:8501
    - Authentication Service API: http://localhost:8001/docs
    - Database Service API: http://localhost:8002/docs
    - Meal Proposer API: http://localhost:8003/docs
    - Meal Planner API: http://localhost:8004/docs
    - Recipe CRUD API: http://localhost:8005/docs
    - Recipes Fetch API: http://localhost:8006/docs

**Note:** Database tables are automatically initialized on startup. No manual initialization required.

### Local Development

1. **Install dependencies for each service:**
   ```bash
   cd authentication-service && pip install -r requirements.txt
   cd ../database-service && pip install -r requirements.txt
   cd ../meal-proposer && pip install -r requirements.txt
   cd ../meal-planner-pcl && pip install -r requirements.txt
   cd ../recipe-crud-interaction && pip install -r requirements.txt
   cd ../recipes-fetch-service && pip install -r requirements.txt
   cd ../streamlit && pip install -r requirements.txt
   ```

2. **Start PostgreSQL:**
   ```bash
   docker run -d \
     --name meal-planner-db \
     -e POSTGRES_DB=mealplanner \
     -e POSTGRES_USER=mealplanner \
     -e POSTGRES_PASSWORD=mealplanner \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Set environment variables:**
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=mealplanner
   export DB_USER=mealplanner
   export DB_PASSWORD=mealplanner
   ```

4. **Run each service:**
   ```bash
   # Terminal 1
   cd authentication-service && python main.py
   
   # Terminal 2
   cd database-service && python main.py
   
   # Terminal 3
   cd meal-proposer && python main.py
   
   # Terminal 4
   cd meal-planner-pcl && python main.py
   
   # Terminal 5
   cd recipe-crud-interaction && python main.py
   
   # Terminal 6
   cd recipes-fetch-service && python main.py
   
   # Terminal 7
   cd streamlit && streamlit run app.py
   ```

## Usage

### Creating a User

1. Open http://localhost:8501 in your browser
2. Click on "Register" (or use the API endpoint)
3. Enter username, password, and full name
4. Login with your credentials

### Proposing a Meal

1. Navigate to "Meal Proposal"
2. Optionally enter an ingredient
3. Click "Propose Meal"
4. View the suggested recipe with ingredients and instructions

### Creating a Meal Plan

1. Navigate to "Meal Planning"
2. Enter the number of days
3. Optionally select a start date and ingredient
4. Click "Generate Meal Plan"
5. View the generated plan with breakfast, lunch, and dinner for each day

### Adding Custom Recipes

1. Navigate to "My Recipes"
2. Click on "Add Recipe" tab
3. Fill in recipe details (name, category, area, instructions, etc.)
4. Click "Save Recipe"

### Searching Recipes

1. Navigate to "Recipe Search"
2. Select search type (Name, Ingredient, Category, or Area)
3. Enter search term or select from dropdown
4. Click "Search"
5. Browse matching recipes

## API Documentation

Each service provides interactive API documentation via Swagger UI:

- Authentication Service: http://localhost:8001/docs
- Database Service: http://localhost:8002/docs
- Meal Proposer: http://localhost:8003/docs
- Meal Planner: http://localhost:8004/docs
- Recipe CRUD: http://localhost:8005/docs
- Recipes Fetch: http://localhost:8006/docs

## Stopping the Application

```bash
docker-compose down
```

To remove volumes (delete all data):

```bash
docker-compose down -v
```

## Troubleshooting

### Database Connection Issues

If services can't connect to the database:
1. Check if PostgreSQL is running: `docker ps`
2. Check database logs: `docker logs meal-planner-db`
3. Verify environment variables in docker-compose.yml

### Service Startup Issues

If a service fails to start:
1. Check service logs: `docker logs <service-name>`
2. Verify dependencies are running
3. Check port conflicts

### TheMealDB API Issues

If recipe fetching fails:
1. Check internet connection
2. Verify TheMealDB is accessible: https://www.themealdb.com
3. Check meal-proposer and recipes-fetch-service logs

## Development

### Adding New Features

1. Create a new service directory with:
   - `Dockerfile`
   - `requirements.txt`
   - `main.py` (REST API endpoints)
   - `service.py` (business logic)

2. Add the service to `docker-compose.yml`

3. Update the Streamlit GUI to interact with the new service

### Testing

Each service can be tested independently:
```bash
# Test authentication
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123","full_name":"Test User"}'

# Test meal proposal
curl -X POST http://localhost:8003/propose \
  -H "Content-Type: application/json" \
  -d '{"ingredient":"chicken"}'

# Test recipe search
curl http://localhost:8006/search/name/chicken
```

## License

This project is provided as-is for educational purposes.

## Acknowledgments

- [TheMealDB](https://www.themealdb.com/) - Free meal recipe database API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for building APIs
- [Streamlit](https://streamlit.io/) - Framework for creating data apps
- [PostgreSQL](https://www.postgresql.org/) - Powerful, open source object-relational database system
